import json
from typing import Optional
from anthill import Agent

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
    model="groq/llama-3.3-70b-versatile",
    instructions="You are a helpful agent which help user with weather. Answer the user about weather or just say: I DO NOT KNOW!",
    functions=[get_weather, send_email],
)
