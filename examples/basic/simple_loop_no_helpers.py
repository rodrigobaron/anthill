from anthill import Anthill, Agent
from pulsar.client import GroqClient

client = Anthill(client=GroqClient())

my_agent = Agent(
    name="Agent",
    model="llama-3.1-70b-versatile",
    instructions="You are a helpful agent.",
)


def pretty_print_messages(messages):
    for message in messages:
        if message["content"] is None:
            continue
        print(f"{message['sender']}: {message['content']}")


messages = []
agent = my_agent
while True:
    user_input = input("> ")
    messages.append({"role": "user", "content": user_input})

    response = client.run(agent=agent, messages=messages)
    messages = response.messages
    agent = response.agent
    pretty_print_messages(messages)
