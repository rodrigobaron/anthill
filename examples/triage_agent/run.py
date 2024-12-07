from anthill.repl import run_demo_loop, run_demo_app
from agents import triage_agent

if __name__ == "__main__":

    run_demo_app(starting_agent=triage_agent)
