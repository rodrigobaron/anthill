from anthill import Anthill, Agent
from anthill.types import AgentFunction

client = Anthill()


def instructions(context_variables):
    name = context_variables.get("name", "User")
    return f"You are a helpful agent. Greet the user by name ({name})."

class PrintAccountDetails(AgentFunction):
    user_name: str

    def run(self, **kwargs):
        user_id = context_variables.get("user_id", None)
        name = context_variables.get("name", None)
        print(f"Account Details: {name} {user_id}")
        return "Success"


agent = Agent(
    name="Agent",
    model="groq/llama-3.1-70b-versatile",
    instructions=instructions,
    functions=[PrintAccountDetails],
)

context_variables = {"name": "James", "user_id": 123}

response = client.run(
    messages=[{"role": "user", "content": "Hi!"}],
    agent=agent,
    context_variables=context_variables,
)
print(response.messages[-1]["content"])

response = client.run(
    messages=[{"role": "user", "content": "Print my account details!"}],
    agent=agent,
    context_variables=context_variables,
)
print(response.messages[-1]["content"])
