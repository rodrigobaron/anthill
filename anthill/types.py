# from openai.types.chat import ChatCompletionMessage
from typing import List, Callable, Union, Optional

# Third-party imports
from pydantic import BaseModel

AgentFunction = Callable[[], Union[str, "Agent", dict]]


class Agent(BaseModel):
    name: str = "Agent"
    model: str
    instructions: Union[str, Callable[[], str]] = "You are a helpful agent."
    functions: List[AgentFunction] = []
    tool_choice: str = None
    completion_args: Union[dict, str] = {}


class StepCompletionMessage(BaseModel):
    title: str
    content: str
    next_action: str
    tool_name: Optional[str] = None
    tool_input: Optional[Union[dict, str]] = None

    def __repr__(self):
        dict = {k: v for k, v in self.dict().items() if v is not None}
        return str(dict)

    def __str__(self):
        return self.__repr__()


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
