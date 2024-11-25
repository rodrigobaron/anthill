from configs.tools import *
from data.routines.baggage.policies import *
from data.routines.flight_modification.policies import *
from data.routines.prompts import STARTER_PROMPT
from anthill import Agent


def triage_instructions(context_variables):
    customer_context = context_variables.get("customer_context", None)
    flight_context = context_variables.get("flight_context", None)
    return f"""You are to triage a users request, and call a tool to transfer to the right intent.
    Once you are ready to transfer to the right intent, call the tool to transfer to the right intent.
    You dont need to know specifics, just the topic of the request.
    When you need more information to triage the request to an agent, ask a direct question without explaining why you're asking it.
    Do not share your thought process with the user! Do not make unreasonable assumptions on behalf of user.
    The customer context is here: {customer_context}, and flight context is here: {flight_context}"""


triage_agent = Agent(
    name="Triage Agent",
    model="llama-3.1-70b-versatile",
    instructions=triage_instructions,
)

flight_modification = Agent(
    name="Flight Modification Agent",
    model="llama-3.1-70b-versatile",
    instructions="""You are a Flight Modification Agent for a customer service airlines company.
      You are an expert customer service agent deciding which sub intent the user should be referred to.
You already know the intent is for flight modification related question. First, look at message history and see if you can determine if the user wants to cancel or change their flight.
Ask user clarifying questions until you know whether or not it is a cancel request or change flight request. Once you know, call the appropriate transfer function. Either ask clarifying questions, or call one of your functions, every time.""",
)

flight_cancel = Agent(
    name="Flight cancel traversal",
    model="llama-3.1-70b-versatile",
    instructions=STARTER_PROMPT + FLIGHT_CANCELLATION_POLICY,
    functions=[
        EscalateToAgent,
        InitiateRefund,
        InitiateFlightCredits,
        CaseResolved,
    ],
)

flight_change = Agent(
    name="Flight change traversal",
    model="llama-3.1-70b-versatile",
    instructions=STARTER_PROMPT + FLIGHT_CHANGE_POLICY,
    functions=[
        EscalateToAgent,
        ChangeFlight,
        ValidToChangeFlight,
        CaseResolved,
    ],
)

lost_baggage = Agent(
    name="Lost baggage traversal",
    model="llama-3.1-70b-versatile",
    instructions=STARTER_PROMPT + LOST_BAGGAGE_POLICY,
    functions=[
        EscalateToAgent,
        InitiateBaggageSearch,
        CaseResolved,
    ],
)

triage_agent.transfers = [flight_modification, lost_baggage]
flight_modification.transfers = [flight_cancel, flight_change]
flight_cancel.transfers = [triage_agent]
flight_change.transfers = [triage_agent]
lost_baggage.transfers = [triage_agent]