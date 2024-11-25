from anthill.repl import run_demo_loop
from agents import triage_agent
from pulsar.client import GroqClient

if __name__ == "__main__":
    groq_client = GroqClient()

    run_demo_loop(client=groq_client, starting_agent=triage_agent, stream=False)
