from anthill import Anthill, Agent
from pulsar.client import GroqClient

client = Anthill(client=GroqClient())

agent = Agent(
    name="Agent",
    model="llama-3.1-70b-versatile",
    instructions="You are a helpful agent.",
)

messages = [{"role": "user", "content": "Hi!"}]
response = client.run(agent=agent, messages=messages)

print(response.messages[-1]["content"])
