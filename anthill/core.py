# Standard library imports
import copy
import json
from collections import defaultdict
from typing import List, Callable, Union

# Package/library imports
from pulsar.client import OpenAiApiLike, Message as ClientMessage, MessageRole as ClientMessageRole

# Local imports
from .util import function_to_json, debug_print, merge_chunk
from .types import (
    Agent,
    AgentResponse,
    TransferToAgent,
    Message,
    Response,
    Result,
)
# import logging
# logging.basicConfig(level=logging.DEBUG)

__CTX_VARS_NAME__ = "context_variables"

client_role_map = {
    "assistant": ClientMessageRole.ASSISTANT,
    "user": ClientMessageRole.USER,
    "tool": ClientMessageRole.ASSISTANT
}

class Anthill:
    def __init__(self, client: OpenAiApiLike):
        self.client = client

    def get_chat_completion(
        self,
        agent: Agent,
        history: List,
        context_variables: dict,
        model_override: str,
        stream: bool,
        debug: bool,
    ) -> Message:
        context_variables = defaultdict(str, context_variables)
        instructions = (
            agent.instructions(context_variables)
            if callable(agent.instructions)
            else agent.instructions
        )
        agent_list = [f"{k+1}: {t_agent.name}" for k, t_agent in enumerate(agent.transfers)]
        instructions = f"Your are {agent.name}. \n// INSTRUCTIONS:\n{instructions}\n Do NOT assume anything or use placeholders."

        tools_map = [{f.__name__: f.__doc__} for f in agent.functions]
        if len(agent_list) > 0:
            agent_list_inst = "\n".join(agent_list)
            instructions = f"{instructions}\n// TEAM AGENTS (agent_id: name): {agent_list_inst}"
            tools_map.append({"TransferToAgent": "Tranfer to team Agent"})
        tools_map.append({"AgentResponse": "Send a message/question to user."})
        
        
        if len(tools_map) > 0:
            tool_list_inst = "\n".join([f"{k}: {v}" for t in tools_map for k, v in t.items()])
            instructions = f"{instructions}\n// TOOLS: {tool_list_inst}"

        messages = []
        for h in history:
            messages.append(ClientMessage(role=client_role_map[h["role"]], content= h["content"]))
            tool_calls = h.get("tool_calls") or []
            for t in tool_calls:
                tool = t["arguments"]
                messages.append(ClientMessage(role=client_role_map[h["role"]], content= str(tool)))
            
        debug_print(debug, "Getting chat completion for...:", instructions, messages)

        if len(agent.functions) > 0:
            type_agent_functions = Union[tuple(agent.functions)] if len(agent.functions) > 1 else agent.functions
            if len(agent.transfers) > 0:
                response_type = Union[AgentResponse, TransferToAgent, List[type_agent_functions]]
            else:
                response_type = Union[AgentResponse, List[type_agent_functions]]
        else:
            if len(agent.transfers) > 0:
                response_type = Union[AgentResponse, TransferToAgent]
            else:
                response_type = AgentResponse
        
        create_params = {
            "model": model_override or agent.model,
            "messages": messages,
            "system": instructions,
            "response_type": response_type,
            "stream": stream,
            "use_cot": True
        }
        response = self.client.chat_completion(**create_params)

        if isinstance(response, AgentResponse):
            return Message(sender=agent.name, role="assistant", content=response.content)
        
        response = response if isinstance(response, list) else [response]
        response = [{"name": r.__class__.__name__, "arguments": r} for r in response]
        return Message(sender=agent.name, role="assistant", tool_calls=response)

    def handle_function_result(self, result, debug) -> Result:
        match result:
            case Result() as result:
                return result

            case Agent() as agent:
                return Result(
                    value= f"current assistant: {agent.name}.\n If your are {agent.name} please handle the user request!",
                    agent=agent,
                )
            case _:
                try:
                    return Result(value=str(result))
                except Exception as e:
                    error_message = f"Failed to cast response to string: {result}. Make sure agent functions return a string or Result object. Error: {str(e)}"
                    debug_print(debug, error_message)
                    raise TypeError(error_message)

    def handle_tool_calls(
        self,
        tool_calls: List,
        current_agent: Agent,
        context_variables: dict,
        debug: bool,
    ) -> Response:
        partial_response = Response(
            messages=[], agent=None, context_variables={})

        for tool_call in tool_calls:
            name = tool_call["name"]
            func = tool_call["arguments"]
            
            if isinstance(func, TransferToAgent):
                raw_result = current_agent.transfers[func.agent_id-1]
            else:
                raw_result = func.run(context_variables=context_variables)

            result: Result = self.handle_function_result(raw_result, debug)
            
            partial_response.messages.append(
                {
                    "role": "tool",
                    # "tool_call_id": func.id,
                    "tool_name": name,
                    "content": f"{name}: => {result.value}",
                }
            )
            partial_response.context_variables.update(result.context_variables)
            if result.agent:
                partial_response.agent = result.agent

        return partial_response

    def run_and_stream(
        self,
        agent: Agent,
        messages: List,
        context_variables: dict = {},
        model_override: str = None,
        debug: bool = False,
        max_turns: int = float("inf"),
        execute_tools: bool = True,
    ):
        active_agent = agent
        context_variables = copy.deepcopy(context_variables)
        history = copy.deepcopy(messages)
        init_len = len(messages)

        while len(history) - init_len < max_turns:

            message = {
                "content": "",
                "sender": agent.name,
                "role": "assistant",
                "function_call": None,
                "tool_calls": defaultdict(
                    lambda: {
                        "function": {"arguments": "", "name": ""},
                        "id": "",
                        "type": "",
                    }
                ),
            }

            # get completion with current history, agent
            completion = self.get_chat_completion(
                agent=active_agent,
                history=history,
                context_variables=context_variables,
                model_override=model_override,
                stream=True,
                debug=debug,
            )

            yield {"delim": "start"}
            for chunk in completion:
                delta = json.loads(chunk.choices[0].delta.json())
                if delta["role"] == "assistant":
                    delta["sender"] = active_agent.name
                yield delta
                delta.pop("role", None)
                delta.pop("sender", None)
                merge_chunk(message, delta)
            yield {"delim": "end"}

            message["tool_calls"] = list(
                message.get("tool_calls", {}).values())
            if not message["tool_calls"]:
                message["tool_calls"] = None
            debug_print(debug, "Received completion:", message)
            history.append(message)

            if not message["tool_calls"] or not execute_tools:
                debug_print(debug, "Ending turn.")
                break

            # convert tool_calls to objects
            tool_calls = []
            for tool_call in message["tool_calls"]:
                function = Function(
                    arguments=tool_call["function"]["arguments"],
                    name=tool_call["function"]["name"],
                )
                tool_call_object = ChatCompletionMessageToolCall(
                    id=tool_call["id"], function=function, type=tool_call["type"]
                )
                tool_calls.append(tool_call_object)

            # handle function calls, updating context_variables, and switching agents
            partial_response = self.handle_tool_calls(
                tool_calls, active_agent.functions, context_variables, debug
            )
            history.extend(partial_response.messages)
            context_variables.update(partial_response.context_variables)
            if partial_response.agent:
                active_agent = partial_response.agent

        yield {
            "response": Response(
                messages=history[init_len:],
                agent=active_agent,
                context_variables=context_variables,
            )
        }

    def run(
        self,
        agent: Agent,
        messages: List,
        context_variables: dict = {},
        model_override: str = None,
        stream: bool = False,
        debug: bool = False,
        max_turns: int = float("inf"),
        execute_tools: bool = True,
    ) -> Response:
        if stream:
            return self.run_and_stream(
                agent=agent,
                messages=messages,
                context_variables=context_variables,
                model_override=model_override,
                debug=debug,
                max_turns=max_turns,
                execute_tools=execute_tools,
            )
        active_agent = agent
        context_variables = copy.deepcopy(context_variables)
        history = copy.deepcopy(messages)
        init_len = len(messages)

        while len(history) - init_len < max_turns and active_agent:

            # get completion with current history, agent
            message = self.get_chat_completion(
                agent=active_agent,
                history=history,
                context_variables=context_variables,
                model_override=model_override,
                stream=stream,
                debug=debug,
            )
            debug_print(debug, "Received completion:", message)
            # message.sender = active_agent.name
            history.append(
                json.loads(message.model_dump_json())
            )

            if not message.tool_calls or not execute_tools:
                debug_print(debug, "Ending turn.")
                break

            # handle function calls, updating context_variables, and switching agents
            partial_response = self.handle_tool_calls(
                message.tool_calls, active_agent, context_variables, debug
            )
            history.extend(partial_response.messages)
            context_variables.update(partial_response.context_variables)
            if partial_response.agent:
                active_agent = partial_response.agent

        return Response(
            messages=history[init_len:],
            agent=active_agent,
            context_variables=context_variables,
        )
