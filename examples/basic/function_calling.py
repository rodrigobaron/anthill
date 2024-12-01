from anthill import Anthill, Agent
from anthill.types import AgentFunction

client = Anthill()

class GetWeather(AgentFunction):
    location: str
    def run(self, **kwargs):
        return "{'temp':67, 'unit':'F'}"

agent = Agent(
    name="Agent",
    model="groq/llama-3.1-70b-versatile",
    instructions="You are a helpful agent.",
    functions=[GetWeather],
)

messages = [{"role": "user", "content": "What's the weather in NYC?"}]

response = client.run(agent=agent, messages=messages)
print(response.messages[-1]["content"])
