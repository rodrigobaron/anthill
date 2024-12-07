import json

from anthill import Anthill
from anthill.types import Message


def process_and_print_streaming_response(response):
    content = ""
    last_sender = ""
    tool_calls_printed = False

    for chunk in response:
        if isinstance(chunk, Message):
            # Handle sender/role changes
            if chunk.sender and chunk.sender != last_sender:
                last_sender = chunk.sender
                print(f"\033[94m{last_sender}:\033[0m", end=" ", flush=True)

            # Handle content streaming
            if chunk.content is not None:
                # Only print the new content (delta)
                new_content = chunk.content[len(content):]
                print(new_content, end="", flush=True)
                content = chunk.content

            # Handle tool calls
            if chunk.tool_calls is not None and len(chunk.tool_calls) > 0 and not tool_calls_printed:
                for tool_call in chunk.tool_calls:
                    name = tool_call["name"]
                    if name:
                        print(f"\033[95m{name}\033[0m()", end="", flush=True)
                tool_calls_printed = True  # Mark tool calls as printed to avoid duplicates

        # Handle end of message
        if "delim" in chunk and chunk["delim"] == "end":
            if content or tool_calls_printed:
                print()  # Add final newline
            content = ""
            tool_calls_printed = False

        # Handle response object
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
