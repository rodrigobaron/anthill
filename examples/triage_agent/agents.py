from typing import Optional, Literal
from anthill import Agent, AgentFunction, TransferToAgent
from pydantic import Field


class ProcessRefund(AgentFunction):
    """Refund an item. Refund an item. Make sure you have the item_id of the form item_... Ask for user confirmation before processing the refund."""

    item_id: int = Field(..., description="item_id is a number (e.g 10, 123, 1002) to item on database!")
    reason: Optional[str] = "NOT SPECIFIED"

    def run(self, **kwargs):
        print(f"[mock] Refunding item {self.item_id} because {self.reason}...")
        return "Success!"

class ApplyDiscount(AgentFunction):
    """Apply a discount to the user's cart."""
    # name: Literal["apply_discount"]
    discount_code: str
    def run(self, **kwargs):
        
        print("[mock] Applying discount...")
        return "Applied discount of 11%"


triage_agent = Agent(
    name="Triage Agent",
    model="groq/llama-3.1-70b-versatile",
    instructions="- Determine which agent is best suited to handle the user's request, and transfer the conversation to that agent\n- If no agent is suited you can aswer the user",
)
sales_agent = Agent(
    name="Sales Agent",
    model="groq/llama-3.1-70b-versatile",
    instructions="Be super enthusiastic about selling bees. Anything else than sales is not up to you.",
)
refunds_agent = Agent(
    name="Refunds Agent",
    model="groq/llama-3.1-70b-versatile",
    instructions="Help the user with a refund. If the reason is that it was too expensive, offer the user a refund code. If they insist, then process the refund. If have any question just ask to user.",
    functions=[ProcessRefund, ApplyDiscount],
)

triage_agent.transfers = [sales_agent, refunds_agent]
sales_agent.transfers = [triage_agent]
refunds_agent.transfers = [triage_agent]