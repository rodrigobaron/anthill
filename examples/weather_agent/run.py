from anthill.repl import run_demo_loop
from agents import weather_agent
from pulsar.client import GroqClient

client = GroqClient()

if __name__ == "__main__":
    run_demo_loop(client=client, starting_agent=weather_agent, stream=True)
