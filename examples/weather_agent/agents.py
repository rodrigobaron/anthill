import json
from typing import Optional
from anthill import Agent
from anthill.types import AgentFunction

class GetWeather(AgentFunction):
    """Get the current weather in a given location. Location MUST be a city."""
    location: str
    time: Optional[str] = "now"

    def run(self, **kwargs):
        return json.dumps({"location": self.location, "temperature": "65", "time": self.time})

class SendEmail(AgentFunction):
    recipient: str
    subject: str
    body: str

    def run(self, **kwargs):
        print("Sending email...")
        print(f"To: {self.recipient}")
        print(f"Subject: {self.subject}")
        print(f"Body: {self.body}")
        return "Sent!"


weather_agent = Agent(
    name="Weather Agent",
    model="llama-3.1-70b-versatile",
    instructions="You are a helpful agent which help user with weather. Answer the user about weather or just say: I DO NOT KNOW!",
    functions=[GetWeather, SendEmail],
)
