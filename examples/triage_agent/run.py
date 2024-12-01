from anthill.repl import run_demo_loop
from agents import triage_agent

if __name__ == "__main__":

    run_demo_loop(starting_agent=triage_agent, stream=False)
