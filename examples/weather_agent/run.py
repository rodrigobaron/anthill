from anthill.repl import run_demo_loop
from agents import weather_agent

if __name__ == "__main__":
    print(weather_agent)
    run_demo_loop(weather_agent, stream=True)
