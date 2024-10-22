import json

from anthill import Agent
from dotenv import load_dotenv

load_dotenv()


def get_weather(location, time="now"):
    """Get the current weather in a given location. Location MUST be a city."""
    return json.dumps({"location": location, "temperature": "65", "time": time})


def send_email(recipient, subject, body):
    print("Sending email...")
    print(f"To: {recipient}")
    print(f"Subject: {subject}")
    print(f"Body: {body}")
    return "Sent!"


weather_agent = Agent(
    name="Weather Agent",
    model="openrouter/meta-llama/llama-3.1-70b-instruct:free",
    instructions="You are a helpful agent.",
    functions=[get_weather, send_email],
)
