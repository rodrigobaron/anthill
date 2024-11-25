from pulsar.client import GroqClient

from pydantic import BaseModel
from typing import Optional

__client = GroqClient()


class BoolEvalResult(BaseModel):
    value: bool
    reason: Optional[str]


def evaluate_with_llm_bool(instruction, data) -> BoolEvalResult:
    eval_result = __client.chat_completion(
        model="llama-3.1-70b-versatile",
        system=instruction,
        messages=[
            dict(content=data, role="user"),
        ],
        response_type=BoolEvalResult,
        use_cot=True
    )
    return eval_result
