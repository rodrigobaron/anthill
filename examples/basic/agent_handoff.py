from anthill import Anthill, Agent

client = Anthill()

english_agent = Agent(
    name="English Agent",
    model="groq/llama-3.3-70b-versatile",
    instructions="You only speak English.",
)

spanish_agent = Agent(
    name="Spanish Agent",
    model="groq/llama-3.3-70b-versatile",
    instructions="You only speak Spanish to the user.",
)

def transfer_to_spanish_agent():
    """Transfer spanish speaking users immediately."""
    return spanish_agent


english_agent.functions.append(transfer_to_spanish_agent)

messages = [{"role": "user", "content": "Hola. ¿Como estás?"}]
response = client.run(agent=english_agent, messages=messages)

print(response.messages[-1]["content"])
