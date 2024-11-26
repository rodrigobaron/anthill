from anthill import Anthill
from agents import weather_agent
import pytest

from pulsar.client import GroqClient

client = Anthill(client=GroqClient())


def run_and_get_tool_calls(agent, query):
    message = {"role": "user", "content": query}
    response = client.run(
        agent=agent,
        messages=[message],
    )
    return response.messages[0].get("tool_calls") or []


@pytest.mark.parametrize(
    "query",
    [
        "What's the weather in NYC?",
        "Tell me the weather in London.",
        # "Do I need an umbrella today? I'm in chicago.",
    ],
)
def test_calls_weather_when_asked(query):
    tool_calls = run_and_get_tool_calls(weather_agent, query)

    assert len(tool_calls) == 1
    assert tool_calls[0]["name"] == "GetWeather"


@pytest.mark.parametrize(
    "query",
    [
        "Who's the president of the United States?",
        "What is the time right now?",
        "Hi!",
    ],
)
def test_does_not_call_weather_when_not_asked(query):
    # import pdb; pdb.set_trace()
    tool_calls = run_and_get_tool_calls(weather_agent, query)

    assert not tool_calls
