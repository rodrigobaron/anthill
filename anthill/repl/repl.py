from anthill import Anthill


def pretty_print_messages(response, stream) -> None:
    for k, r in enumerate(response):
        if stream:
            if "result" in r:
                return r["result"]
            if "partial" in r:
                chunk = r["partial"].messages[-1]
                if k == 0:
                    # print agent name in blue
                    print(f"\033[94m{chunk['sender']}\033[0m:", end=" ")
                print(chunk["content"], end="", flush=stream)
        else:
            if "result" in r:
                chunk = r["result"].messages[-1]
                # print agent name in blue
                print(f"\033[94m{chunk['sender']}\033[0m:", end=" ")
                print(chunk["content"])
                return r["result"]


def run_demo_loop(starting_agent, context_variables=None, stream=False) -> None:
    client = Anthill()
    print("Starting Anthill CLI 🐜")

    messages = []
    agent = starting_agent

    while True:
        user_input = input("\033[90mUser\033[0m: ")
        messages.append({"role": "user", "content": user_input})

        response = client.run(
            agent=agent,
            messages=messages,
            context_variables=context_variables or {},
            stream=stream,
        )

        response = pretty_print_messages(response, stream)

        messages.extend(response.messages)
        agent = response.agent
