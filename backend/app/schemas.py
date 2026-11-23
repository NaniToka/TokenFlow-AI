"""
Enhanced request/response schemas with comprehensive validation.

Provides Pydantic v2 models for:
- API request/response payloads
- Compression metadata and diagnostics
- Error responses with structured error codes
- WebSocket message types
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

# --- Core Models ---


class Turn(BaseModel):
    """A single conversation turn."""

    role: Literal["user", "model"] = Field(
        ..., description="Speaker role: 'user' or 'model'"
    )
    content: str = Field(
        ..., min_length=1, max_length=50_000,
        description="Turn content text (1-50k characters)"
    )

    @field_validator("content")
    @classmethod
    def strip_content(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Turn content cannot be empty or whitespace-only")
        return stripped


# --- Request Models ---


class CompressRequest(BaseModel):
    """Prompt compression request payload."""

    history: list[Turn] = Field(
        default_factory=list,
        max_length=200,
        description="Conversation history (max 200 turns)",
    )
    current_message: str = Field(
        default="",
        max_length=50_000,
        description="Current user message to optimize context for",
    )
    system_instruction: str = Field(
        default="",
        max_length=10_000,
        description="Optional system instruction to preserve in compressed prompt",
    )
    top_k: int = Field(
        default=3, ge=1, le=20,
        description="Number of top-ranked history turns to retain",
    )
    alpha: float | None = Field(
        default=None, ge=0.0, le=1.0,
        description="Semantic vs recency weight (None = auto-tune)",
    )


class BatchCompressRequest(BaseModel):
    """Batch compression request for multiple conversations."""

    requests: list[CompressRequest] = Field(
        ..., min_length=1, max_length=10,
        description="List of compression requests (max 10 per batch)",
    )


# --- Response Models ---


class CompressionMetadata(BaseModel):
    """Detailed metadata about the compression process."""

    ranking_strategy: str = Field(
        default="hybrid",
        description="Ranking strategy used (e.g., 'bm25+dense_vector+recency')",
    )
    alpha_used: float = Field(
        default=0.7,
        description="Effective alpha weight used for scoring",
    )
    drift_detected: bool = Field(
        default=False,
        description="Whether conversational drift was detected",
    )
    turns_evaluated: int = Field(default=0)
    turns_selected: int = Field(default=0)
    turns_evicted: int = Field(default=0)
    model_used: str = Field(
        default="fallback_extractive",
        description="LLM model used for summarization",
    )
    scores: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Per-turn scoring breakdown",
    )


class CompressResponse(BaseModel):
    """Full compression response with metrics."""

    summary: str = Field(description="Background context summary of evicted turns")
    selected_turns: list[Turn] = Field(description="Top-K retained turns")
    final_prompt: str = Field(description="Assembled optimized prompt")
    original_tokens: int = Field(description="Token count before compression")
    compressed_tokens: int = Field(description="Token count after compression")
    tokens_saved: int = Field(description="Tokens eliminated")
    cost_before_usd: float = Field(description="Estimated cost before compression")
    cost_after_usd: float = Field(description="Estimated cost after compression")
    cost_saved_usd: float = Field(description="Estimated cost savings")
    compression_ratio: float = Field(description="Compression percentage")
    metadata: CompressionMetadata = Field(
        default_factory=CompressionMetadata,
        description="Detailed compression diagnostics",
    )


class BatchCompressResponse(BaseModel):
    """Batch compression response."""

    results: list[CompressResponse]
    total_tokens_saved: int
    total_cost_saved_usd: float


# --- Error Models ---


class ErrorCode(str, Enum):
    """Machine-readable error codes."""

    VALIDATION_ERROR = "VALIDATION_ERROR"
    EMPTY_MESSAGE = "EMPTY_MESSAGE"
    HISTORY_TOO_LARGE = "HISTORY_TOO_LARGE"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    LLM_UNAVAILABLE = "LLM_UNAVAILABLE"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorDetail(BaseModel):
    """Structured error detail."""

    field: str | None = None
    message: str
    value: Any | None = None


class ErrorResponse(BaseModel):
    """Standardized error response."""

    error: ErrorCode
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)
    correlation_id: str | None = None


# --- Stats Models ---


class SessionStats(BaseModel):
    """Session analytics summary."""

    total_requests: int = 0
    total_original_tokens: int = 0
    total_compressed_tokens: int = 0
    total_tokens_saved: int = 0
    total_cost_before_usd: float = 0.0
    total_cost_after_usd: float = 0.0
    total_cost_saved_usd: float = 0.0
    avg_compression_ratio: float = 0.0
    avg_latency_ms: float = 0.0
    request_history: list[dict[str, Any]] = Field(default_factory=list)


# --- Health Check Models ---


class HealthStatus(BaseModel):
    """Application health check response."""

    status: str = "healthy"
    service: str = "TokenFlow AI"
    version: str = "2.0.0"
    environment: str = "development"
    llm_available: bool = False
    uptime_seconds: float = 0.0
    features: dict[str, bool] = Field(default_factory=dict)
