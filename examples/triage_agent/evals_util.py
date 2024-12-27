from pulsar.client import Client

from pydantic import BaseModel
from typing import Optional

__client = Client()


class BoolEvalResult(BaseModel):
    value: bool
    reason: Optional[str]


def evaluate_with_llm_bool(instruction, data) -> BoolEvalResult:
    eval_result = __client.chat_completion(
        model="groq/llama-3.3-70b-versatile",
        system=instruction,
        messages=data,
        response_type=BoolEvalResult,
    )
    return eval_result
