import json

from anthill import Anthill
from anthill.types import Message


def process_and_print_streaming_response(response):
    content = ""
    last_sender = ""

    for chunk in response:
        if isinstance(chunk, Message):
            if chunk.sender:
                last_sender = chunk.sender

            if chunk.content:
                if not content and last_sender:
                    print(f"\033[94m{last_sender}:\033[0m", end=" ", flush=True)
                    last_sender = ""
                print(chunk.content, end="", flush=True)
                content = chunk.content

            tool_calls = chunk.tool_calls or []
            for tool_call in tool_calls:
                name, args = tool_call["name"], tool_call["arguments"]
                if not name:
                    continue
                arg_str = args.model_dump_json().replace(":", "=")
                print(f"\033[94m{last_sender}: \033[95m{name}\033[0m({arg_str[1:-1]})")

        if "delim" in chunk and chunk["delim"] == "end" and content:
            print()  # End of response message
            content = ""

        if "response" in chunk:
            return chunk["response"]


def pretty_print_messages(messages) -> None:
    for message in messages:
        if message["role"] != "assistant":
            continue

        # print agent name in blue
        print(f"\033[94m{message['sender']}\033[0m:", end=" ")

        # print response, if any
        if message["content"]:
            print(message["content"])

        # print tool calls in purple, if any
        tool_calls = message.get("tool_calls") or []
        if len(tool_calls) > 1:
            print()
        for tool_call in tool_calls:
            name, args = tool_call["name"], tool_call["arguments"]
            arg_str = json.dumps(args).replace(":", "=")
            print(f"\033[95m{name}\033[0m({arg_str[1:-1]})")


def run_demo_loop(
    starting_agent, client=None, context_variables=None, stream=False, debug=False
) -> None:
    ant_client = Anthill(client=client)
    print("Starting Anthill CLI 🐜")

    messages = []
    agent = starting_agent

    while True:
        user_input = input("\033[90mUser\033[0m: ")
        messages.append({"role": "user", "content": user_input})

        response = ant_client.run(
            agent=agent,
            messages=messages,
            context_variables=context_variables or {},
            stream=stream,
            debug=debug,
        )

        if stream:
            response = process_and_print_streaming_response(response)
        else:
            pretty_print_messages(response.messages)

        messages.extend(response.messages)
        agent = response.agent
