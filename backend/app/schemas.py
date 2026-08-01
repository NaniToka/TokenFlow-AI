from typing import List, Literal
from pydantic import BaseModel, Field


class Turn(BaseModel):
    role: Literal["user", "model"]
    content: str = Field(..., min_length=1)


class CompressRequest(BaseModel):
    history: List[Turn] = Field(default_factory=list)
    current_message: str
    top_k: int = Field(default=3, ge=1, le=10)


class CompressResponse(BaseModel):
    summary: str
    selected_turns: List[Turn]
    final_prompt: str
    original_tokens: int
    compressed_tokens: int
    tokens_saved: int
    cost_before_usd: float
    cost_after_usd: float
    cost_saved_usd: float
    compression_ratio: float
