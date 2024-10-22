from anthill import Agent
from dotenv import load_dotenv

load_dotenv()

def process_refund(item_id, reason="NOT SPECIFIED"):
    """Refund an item. Refund an item. Make sure you have the item_id of the form item_... Ask for user confirmation before processing the refund."""
    print(f"[mock] Refunding item {item_id} because {reason}...")
    return "Success!"


def apply_discount():
    """Apply a discount to the user's cart."""
    print("[mock] Applying discount...")
    return "Applied discount of 11%"


triage_agent = Agent(
    name="Triage Agent",
    model="groq/llama-3.1-70b-versatile",
    instructions="Determine which agent is best suited to handle the user's request, and transfer the conversation to that agent. When identified a best agent to handle user request transfer right way. DO NOT ASK ANYTHING WHICH IS NOT YOU RESPONSABILITY",
    completion_args={'temperature': 0.2}
)
sales_agent = Agent(
    name="Sales Agent",
    model="groq/llama-3.1-70b-versatile",
    instructions="Your responsability is sell bees, for others topics such as user satisfaction, refund, or others is not your responsabilities. Be super enthusiastic about selling bees.",
    completion_args={'temperature': 0.2}
)
refunds_agent = Agent(
    name="Refunds Agent",
    model="groq/llama-3.1-70b-versatile",
    instructions="Help the user with a refund. First ask the refund reason, if the reason is that it was too expensive, offer the user a refund code. If they insist, then process the refund.",
    functions=[process_refund, apply_discount],
    completion_args={'temperature': 0.2}
)

def transfer_to_triage():
    """When user a user is asking about a topic/responsability that is not handled by the current agent."""
    return triage_agent


def transfer_to_sales():
    "Transfer to sales agent."
    return sales_agent


def transfer_to_refunds():
    "Transfer to refund agent."
    return refunds_agent


triage_agent.functions = [transfer_to_sales, transfer_to_refunds]
sales_agent.functions.append(transfer_to_triage)
refunds_agent.functions.append(transfer_to_triage)
