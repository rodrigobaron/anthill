from typing import Optional, Literal
from anthill import AgentFunction


class EscalateToAgent(AgentFunction):
    function_name: Literal["escalate_to_agent"]
    reason: Optional[str] = None

    def run(self, **kwargs):
        return f"Escalating to agent: {self.reason}" if self.reason else "Escalating to agent"

class ValidToChangeFlight(AgentFunction):
    function_name: Literal["valid_to_change_flight"]
    def run(self, **kwargs):
        return "Customer is eligible to change flight"

class ChangeFlight(AgentFunction):
    function_name: Literal["change_flight"]
    def run(self, **kwargs):
        return "Flight was successfully changed!"

class InitiateRefund(AgentFunction):
    function_name: Literal["initiate_refund"]
    def run(self, **kwargs):
        return "Refund initiated"

class InitiateFlightCredits(AgentFunction):
    function_name: Literal["initiate_flight_credits"]
    def run(self, **kwargs):
        return "Successfully initiated flight credits"

class CaseResolved(AgentFunction):
    function_name: Literal["case_resolved"]
    def run(self, **kwargs):
        return "Case resolved. No further questions."

class InitiateBaggageSearch(AgentFunction):
    function_name: Literal["initiate_baggage_search"]
    def run(self, **kwargs):
        return "Baggage was found!"
