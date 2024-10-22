# Standard library imports
import copy
import json
import time
from typing import List, Union, Optional
from collections.abc import Iterable

# Package/library imports
from litellm import completion
from jinja2 import Template
from abc import ABC, abstractmethod

# Local imports
from .util import function_to_json, debug_print
from .prompts import SYSTEM_PROMPT
from .types import (
    Agent,
    StepCompletionMessage,
    Response,
    Result,
)

__CTX_VARS_NAME__ = "context_variables"


class AnthillCallback(ABC):
    @abstractmethod
    def before_first_thought(
        agent: Agent,
        history: List,
        context_variables: dict,
        model_override: str,
        execute_tools: bool,
    ) -> Optional[StepCompletionMessage]:
        pass

    @abstractmethod
    def before_tool_call(
        tool_name: str,
        tool_input: Optional[Union[dict, str]],
        agent: Agent,
        history: List,
        context_variables: dict,
        model_override: str,
        execute_tools: bool,
    ) -> Optional[StepCompletionMessage]:
        pass

    @abstractmethod
    def before_last_thought(
        last_step: StepCompletionMessage,
        step_count: int,
        agent: Agent,
        history: List,
        context_variables: dict,
        model_override: str,
        execute_tools: bool,
    ) -> Optional[StepCompletionMessage]:
        pass


class Anthill:

    def get_step_completion(
        self,
        agent: Agent,
        history: List,
        context_variables: dict,
        model_override: str,
        execute_tools: bool = True,
        response_format: Union[dict, str] = None,
    ) -> StepCompletionMessage:
        instructions = (
            agent.instructions(context_variables)
            if callable(agent.instructions)
            else agent.instructions
        )
        completion_args = agent.completion_args or {}
        functions_json = (
            [function_to_json(f) for f in agent.functions] if execute_tools else []
        )
        template = Template(SYSTEM_PROMPT)
        system_prompt = template.render(
            **{
                "name": agent.name,
                "tools": functions_json,
                "instructions": instructions,
            }
        )

        model = model_override or agent.model
        messages = [{"role": "system", "content": system_prompt}] + history
        messages = [{"role": m["role"], "content": m["content"]} for m in messages]
        for attempt in range(3):
            create_params = dict(
                model=model,
                messages=messages,
                stream=False,
                response_format=response_format,
                **completion_args,
            )
            try:
                response = completion(**create_params)
                return StepCompletionMessage.parse_raw(
                    response.choices[0].message.content
                )
            except Exception as e:
                debug_print("attempt", attempt, str(e))
                if attempt == 2:
                    return StepCompletionMessage.parse_raw(
                        f'{{"title": "Error", "content": "Failed to generate step after 3 attempts. Error: {str(e)}", "next_action": "final_step"}}'
                    )
                time.sleep(1)  # Wait for 1 second before retrying

    def get_chat_completion(
        self,
        agent: Agent,
        history: List,
        context_variables: dict,
        model_override: str,
        stream: bool,
        response_format: Union[dict, str] = None,
    ) -> Iterable[str]:
        instructions = (
            agent.instructions(context_variables)
            if callable(agent.instructions)
            else agent.instructions
        )
        completion_args = agent.completion_args or {}
        template = Template(SYSTEM_PROMPT)
        system_prompt = template.render(
            **{"name": agent.name, "tools": [], "instructions": instructions}
        )

        model = model_override or agent.model
        messages = [{"role": "system", "content": system_prompt}] + history
        messages = [{"role": m["role"], "content": m["content"]} for m in messages]
        create_params = dict(
            model=model,
            messages=messages,
            stream=stream,
            response_format=response_format,
            **completion_args,
        )
        response = completion(**create_params)
        if stream:
            for part in response:
                yield part.choices[0].delta.content or ""
        else:
            yield response.choices[0].message.content

    def handle_function_result(self, result) -> Result:
        match result:
            case Result() as result:
                return result

            case Agent() as agent:
                return Result(
                    value=json.dumps({"assistant": agent.name}),
                    agent=agent,
                )
            case _:
                try:
                    return Result(value=str(result))
                except Exception as e:
                    error_message = f"Failed to cast response to string: {result}. Make sure agent functions return a string or Result object. Error: {str(e)}"
                    debug_print(error_message)
                    raise TypeError(error_message)

    def run(
        self,
        agent: Agent,
        messages: List,
        context_variables: dict = {},
        model_override: str = None,
        stream: bool = False,
        max_turns: int = 25,
        execute_tools: bool = True,
        callback: Optional[AnthillCallback] = None,
    ) -> Iterable[Response]:
        active_agent = agent
        context_variables = copy.deepcopy(context_variables)
        history = copy.deepcopy(messages)
        history.append(
            {
                "role": "assistant",
                "content": "I will think step by step following my instructions, starting at the beginning after decomposing the problem/task.",
            }
        )
        step_count = 1
        debug_print("Getting chat completion for...:", messages)

        if callback:
            before_first_thought = callback.before_first_thought(
                agent=active_agent,
                history=copy.deepcopy(messages),
                context_variables=context_variables,
                model_override=model_override,
                execute_tools=execute_tools,
            )
            if before_first_thought:
                history.append(
                    {"role": "assistant", "content": str(before_first_thought)}
                )

        while True:
            step_data = self.get_step_completion(
                agent=active_agent,
                history=history,
                context_variables=context_variables,
                model_override=model_override,
                execute_tools=execute_tools,
                response_format={"type": "json_object"},
            )

            debug_print("Step:", step_count, ",received completion:", step_data)
            functions_map = {f.__name__: f for f in active_agent.functions}
            if step_data.tool_name is not None:
                if step_data.tool_name not in functions_map:
                    invalid_tool_thought = StepCompletionMessage(
                        title="Wrong tool",
                        content=f"I was trying use '{step_data.tool_name}' tool but that is not available. I should consider this tools: {functions_map}",
                        next_action="continue",
                    )
                    history.append(
                        {"role": "assistant", "content": str(invalid_tool_thought)}
                    )
                else:
                    step_data.tool_input = (
                        None
                        if step_data.tool_input in (None, "", "{}", {})
                        else step_data.tool_input
                    )
                    step_data.next_action = "continue"
                    history.append({"role": "assistant", "content": str(step_data)})

                    if callback:
                        before_tool_call = callback.before_tool_call(
                            tool_name=step_data.tool_name,
                            tool_input=step_data.tool_input,
                            agent=active_agent,
                            history=history,
                            context_variables=context_variables,
                            model_override=model_override,
                            execute_tools=execute_tools,
                        )
                        if before_tool_call:
                            history.append(
                                {"role": "assistant", "content": str(before_tool_call)}
                            )
                            step_count += 1
                            continue

                    if step_data.tool_input is None:
                        tool_result = functions_map[step_data.tool_name]()
                    else:
                        tool_result = functions_map[step_data.tool_name](
                            step_data.tool_input
                        )

                    debug_print("Tool result", tool_result)
                    result: Result = self.handle_function_result(tool_result)
                    if result.agent:
                        active_agent = result.agent
                        debug_print("Active agent changed", active_agent)
                        history.append(
                            {
                                "role": "assistant",
                                "content": f"The {active_agent.name} is handling the resquest from now.",
                            }
                        )
                    else:
                        history.append(
                            {
                                "role": "assistant",
                                "content": f"{step_data.tool_name} result: {tool_result}",
                            }
                        )
            else:
                if callback:
                    before_last_thought = callback.before_last_thought(
                        last_step=step_data,
                        step_count=step_count,
                        agent=active_agent,
                        history=history,
                        context_variables=context_variables,
                        model_override=model_override,
                        execute_tools=execute_tools,
                    )
                    if before_last_thought:
                        step_data.next_action = "continue"
                        history.append({"role": "assistant", "content": str(step_data)})
                        step_data = before_last_thought

                if step_count > max_turns:
                    step_data.next_action = "final_step"

                history.append({"role": "assistant", "content": str(step_data)})
                if step_data.next_action == "final_step":
                    break
            step_count += 1

        # Generate final answer
        history.append(
            {
                "role": "user",
                "content": "Please provide the final content to the user based solely on your reasoning above. Do not use JSON formatting. Only provide the response without any titles or preambles. Retain any formatting as instructed by the original prompt, such as exact formatting for free response or multiple choice.",
            }
        )

        g = self.get_chat_completion(
            agent=active_agent,
            history=history,
            context_variables=context_variables,
            model_override=model_override,
            stream=stream,
        )

        final_data = ""
        for chunk in g:
            final_data += chunk
            if stream:
                yield {
                    "partial": Response(
                        messages=[
                            {
                                "role": "assistant",
                                "content": chunk,
                                "sender": active_agent.name,
                            }
                        ],
                        agent=active_agent,
                        context_variables=context_variables,
                    )
                }

        response = Response(
            messages=[
                {
                    "role": "assistant",
                    "content": final_data,
                    "sender": active_agent.name,
                }
            ],
            agent=active_agent,
            context_variables=context_variables,
        )
        debug_print("Response:", response)
        yield {"result": response}
