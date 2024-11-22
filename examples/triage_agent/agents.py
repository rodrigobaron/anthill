from typing import Optional, Literal
from anthill import Agent, AgentFunction, TransferToAgent


class ProcessRefund(AgentFunction):
    # name: Literal["process_refund"]
    item_id: int
    reason: Optional[str] = "NOT SPECIFIED"

    def run(self, **kwargs):
        """Refund an item. Refund an item. Make sure you have the item_id of the form item_... Ask for user confirmation before processing the refund."""
        print(f"[mock] Refunding item {self.item_id} because {self.reason}...")
        return "Success!"

class ApplyDiscount(AgentFunction):
    # name: Literal["apply_discount"]

    def run(self, **kwargs):
        """Apply a discount to the user's cart."""
        print("[mock] Applying discount...")
        return "Applied discount of 11%"


triage_agent = Agent(
    name="Triage Agent",
    model="llama-3.1-70b-versatile",
    instructions="Determine which agent is best suited to handle the user's request, and transfer the conversation to that agent.",
)
sales_agent = Agent(
    name="Sales Agent",
    model="llama-3.1-70b-versatile",
    instructions="Be super enthusiastic about selling bees.",
)
refunds_agent = Agent(
    name="Refunds Agent",
    model="llama-3.1-70b-versatile",
    instructions="Help the user with a refund. If the reason is that it was too expensive, offer the user a refund code. If they insist, then process the refund.",
    functions=[ProcessRefund, ApplyDiscount],
)

triage_agent.transfers = [sales_agent, refunds_agent]
sales_agent.transfers = [triage_agent]
refunds_agent.transfers = [triage_agent]