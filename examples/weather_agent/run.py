from anthill.repl import run_demo_loop
from agents import weather_agent

if __name__ == "__main__":
    run_demo_loop(starting_agent=weather_agent, stream=True)
