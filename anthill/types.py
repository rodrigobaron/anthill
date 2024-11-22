from typing import List, Callable, Union, Optional, Literal

# Third-party imports
from pydantic import BaseModel
from pulsar.client import Message as ClientMessage, MessageRole as ClientMessageRole


class AgentResponse(BaseModel):
    content: str

class AgentFunction(BaseModel):
    # id: int
    def run(self, **kwargs):
        raise NotImplementedError()

class TransferToAgent(BaseModel):
    # name: Literal["transfer_to_agent"]
    name: str
    agent_id: int


class Agent(BaseModel):
    name: str = "Agent"
    model: str
    instructions: Union[str, Callable[[], str]] = "You are a helpful agent."
    functions: List = []
    transfers: List["Agent"] = []


class Message(BaseModel):
    sender: Optional[str] = None
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List] = None


class Response(BaseModel):
    messages: List = []
    agent: Optional[Agent] = None
    context_variables: dict = {}


class Result(BaseModel):
    """
    Encapsulates the possible return values for an agent function.

    Attributes:
        value (str): The result value as a string.
        agent (Agent): The agent instance, if applicable.
        context_variables (dict): A dictionary of context variables.
    """

    value: str = ""
    agent: Optional[Agent] = None
    context_variables: dict = {}
