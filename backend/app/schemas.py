"""
Enhanced request/response schemas with comprehensive validation.

Provides Pydantic v2 models for:
- API request/response payloads
- Compression modes, multi-model pricing, and PII redaction reports
- RAG indexing and retrieval endpoints
- Automated Quality Evaluation & Ablation Inspection
- Async background tasks and error taxonomy
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class CompressionMode(str, Enum):
    """Optimization strategies controlling ranking & pruning aggressiveness."""

    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    CODE_PRESERVING = "code_preserving"
    VERBATIM_FACTS = "verbatim_facts"


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
    target_model: str = Field(
        default="gemini-1.5-flash",
        description="Target downstream LLM for pricing and token savings calculation",
    )
    compression_mode: CompressionMode = Field(
        default=CompressionMode.BALANCED,
        description="Compression strategy preset",
    )
    sanitize_pii: bool = Field(
        default=False,
        description="Redact API keys, emails, JWTs, and IP addresses before output",
    )
    use_cache: bool = Field(
        default=True,
        description="Use semantic LRU summary cache when available",
    )


class BatchCompressRequest(BaseModel):
    """Batch compression request for multiple conversations."""

    requests: list[CompressRequest] = Field(
        ..., min_length=1, max_length=10,
        description="List of compression requests (max 10 per batch)",
    )


class RedactionReport(BaseModel):
    """Audit report of PII/secret redactions performed."""

    enabled: bool = False
    redactions_count: int = 0
    xss_stripped: int = 0
    redacted_types: list[str] = Field(default_factory=list)


class CompressionMetadata(BaseModel):
    """Detailed metadata about the compression process."""

    ranking_strategy: str = Field(
        default="hybrid",
        description="Ranking strategy used (e.g., 'bm25+dense_vector+recency')",
    )
    compression_mode: str = Field(default="balanced")
    target_model: str = Field(default="gemini-1.5-flash")
    alpha_used: float = Field(default=0.7)
    drift_detected: bool = Field(default=False)
    turns_evaluated: int = Field(default=0)
    turns_selected: int = Field(default=0)
    turns_evicted: int = Field(default=0)
    model_used: str = Field(default="fallback_extractive")
    cache_hit: bool = Field(default=False)
    latency_ms: float = Field(default=0.0)
    redaction: RedactionReport = Field(default_factory=RedactionReport)
    scores: list[dict[str, Any]] = Field(default_factory=list)


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
    metadata: CompressionMetadata = Field(default_factory=CompressionMetadata)


class BatchCompressResponse(BaseModel):
    """Batch compression response."""

    results: list[CompressResponse]
    total_tokens_saved: int
    total_cost_saved_usd: float


# --- RAG Workbench Models ---


class RAGIndexRequest(BaseModel):
    """Request to chunk and index a document into the in-memory RAG store."""

    text: str = Field(..., min_length=1, max_length=200_000)
    chunk_size: int = Field(default=400, ge=100, le=4000)
    chunk_overlap: int = Field(default=80, ge=0, le=500)
    source_name: str = Field(default="workspace_document", max_length=128)


class RAGChunkItem(BaseModel):
    chunk_id: int
    text: str
    token_count: int
    start_char: int
    end_char: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class RAGIndexResponse(BaseModel):
    chunks_indexed: int
    total_store_chunks: int
    chunks: list[RAGChunkItem]


class RAGQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=10_000)
    top_k: int = Field(default=3, ge=1, le=20)
    alpha: float = Field(default=0.5, ge=0.0, le=1.0)


class RAGQueryResponse(BaseModel):
    query: str
    results: list[dict[str, Any]]
    total_indexed: int


# --- Evaluation & Ablation Models ---


class EvaluateRequest(BaseModel):
    history: list[Turn]
    response: CompressResponse


class EvaluateResponse(BaseModel):
    original_tokens: int
    compressed_tokens: int
    tokens_saved: int
    compression_ratio: float
    lexical_recall: float
    entity_coverage: float
    semantic_fidelity: float
    hallucination_risk: float
    composite_grade: str


class RankInspectRequest(BaseModel):
    history: list[Turn] = Field(..., min_length=1, max_length=200)
    current_message: str = Field(..., min_length=1, max_length=50_000)
    top_k: int = Field(default=3, ge=1, le=20)
    alpha: float | None = Field(default=None, ge=0.0, le=1.0)
    compression_mode: CompressionMode = Field(default=CompressionMode.BALANCED)


class RankInspectResponse(BaseModel):
    alpha_used: float
    drift_detected: bool
    ranking_strategy: str
    scores: list[dict[str, Any]]


# --- Sanitization Endpoint Models ---


class SanitizeRequest(BaseModel):
    text: str = Field(..., max_length=100_000)
    redact_pii: bool = Field(default=True)


class SanitizeResponse(BaseModel):
    sanitized_text: str
    xss_stripped: int
    redactions_count: int
    redacted_types: list[str]


# --- Async Task Models ---


class AsyncTaskResponse(BaseModel):
    task_id: str
    status: str
    duration_ms: float = 0.0
    result: CompressResponse | None = None
    error: str | None = None


# --- Error Models ---


class ErrorCode(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    EMPTY_MESSAGE = "EMPTY_MESSAGE"
    HISTORY_TOO_LARGE = "HISTORY_TOO_LARGE"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    LLM_UNAVAILABLE = "LLM_UNAVAILABLE"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorDetail(BaseModel):
    field: str | None = None
    message: str
    value: Any | None = None


class ErrorResponse(BaseModel):
    error: ErrorCode
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)
    correlation_id: str | None = None


# --- Stats & Health Models ---


class SessionStats(BaseModel):
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


class HealthStatus(BaseModel):
    status: str = "healthy"
    service: str = "TokenFlow AI"
    version: str = "2.0.0"
    environment: str = "development"
    llm_available: bool = False
    uptime_seconds: float = 0.0
    features: dict[str, bool] = Field(default_factory=dict)
