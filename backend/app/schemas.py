from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class Turn(BaseModel):
    role: Literal["user", "model", "system"]
    content: str = Field(..., min_length=1)

    @field_validator("role", mode="before")
    @classmethod
    def normalize_role(cls, v: str) -> str:
        if isinstance(v, str):
            v_lower = v.strip().lower()
            if v_lower in ("user", "model", "system"):
                return v_lower
        return v

    @field_validator("content")
    @classmethod
    def validate_content_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Turn content must not be blank or whitespace-only.")
        return v.strip()


class CompressRequest(BaseModel):
    system_instruction: Optional[str] = Field(default="You are a helpful AI assistant.")
    history: List[Turn] = Field(default_factory=list)
    current_message: str = Field(..., min_length=1)
    top_k: int = Field(default=3, ge=1, le=20)
    alpha: float = Field(default=0.7, ge=0.0, le=1.0)



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
