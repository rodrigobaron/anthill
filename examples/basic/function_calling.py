from anthill import Anthill, Agent

client = Anthill()

def get_weather(location) -> str:
    return "{'temp':67, 'unit':'F'}"

agent = Agent(
    name="Agent",
    model="groq/llama-3.3-70b-versatile",
    instructions="You are a helpful agent.",
    functions=[get_weather],
)

messages = [{"role": "user", "content": "What's the weather in NYC?"}]

response = client.run(agent=agent, messages=messages)
print(response.messages[-1]["content"])
