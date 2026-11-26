"""
Enhanced request/response schemas with comprehensive validation.

Provides Pydantic v2 models for:
- API request/response payloads (v1/v2/OpenAI proxy)
- RRF fusion, MMR diversity, Cross-Encoder reranking, Knapsack budgeting
- RAG indexing, file upload, HyDE query expansion, citations
- Prompt Injection Firewall, Needle-in-a-Haystack, A/B Experiments, Salience Heat-Maps
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
    fusion_method: Literal["linear", "rrf"] = Field(
        default="linear",
        description="Score fusion method: linear weighted sum or Reciprocal Rank Fusion",
    )
    use_mmr: bool = Field(
        default=False,
        description="Enable Maximal Marginal Relevance diversity selection",
    )
    mmr_lambda: float = Field(
        default=0.7, ge=0.0, le=1.0,
        description="MMR relevance vs diversity trade-off",
    )
    use_reranker: bool = Field(
        default=False,
        description="Apply second-stage N-gram + identifier cross-encoder reranking",
    )
    use_dedup: bool = Field(
        default=True,
        description="Collapse near-duplicate retry/boilerplate turns prior to ranking",
    )
    use_hierarchical: bool = Field(
        default=True,
        description="Enable hierarchical map-reduce summarization for >12 evicted turns",
    )
    max_context_tokens: int | None = Field(
        default=None, ge=64, le=1_000_000,
        description="Optional hard token budget enforced via greedy knapsack packing",
    )
    sanitize_pii: bool = Field(
        default=False,
        description="Redact API keys, emails, JWTs, and IP addresses before output",
    )
    scan_prompt_injection: bool = Field(
        default=True,
        description="Run Prompt Injection Firewall diagnostics on request text",
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


class FirewallReport(BaseModel):
    """Prompt injection & jailbreak scan telemetry."""

    is_safe: bool = True
    risk_score: float = 0.0
    highest_severity: str = "NONE"
    findings: list[dict[str, Any]] = Field(default_factory=list)


class CompressionMetadata(BaseModel):
    """Detailed metadata about the compression process."""

    ranking_strategy: str = Field(default="hybrid")
    compression_mode: str = Field(default="balanced")
    fusion_method: str = Field(default="linear")
    target_model: str = Field(default="gemini-1.5-flash")
    alpha_used: float = Field(default=0.7)
    drift_detected: bool = Field(default=False)
    turns_evaluated: int = Field(default=0)
    turns_selected: int = Field(default=0)
    turns_evicted: int = Field(default=0)
    duplicates_removed: int = Field(default=0)
    dropped_for_budget: int = Field(default=0)
    epochs_summarized: int = Field(default=0)
    model_used: str = Field(default="fallback_extractive")
    cache_hit: bool = Field(default=False)
    latency_ms: float = Field(default=0.0)
    redaction: RedactionReport = Field(default_factory=RedactionReport)
    firewall: FirewallReport = Field(default_factory=FirewallReport)
    knowledge_graph: dict[str, Any] = Field(default_factory=dict)
    salience_tokens: list[dict[str, Any]] = Field(default_factory=list)
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


# --- OpenAI Drop-in Compatibility Models ---


class OpenAIChatCompressRequest(BaseModel):
    messages: list[dict[str, str]] = Field(..., min_length=1, max_length=200)
    top_k: int = Field(default=3, ge=1, le=20)
    target_model: str = Field(default="gpt-4o")
    compression_mode: str = Field(default="balanced")
    max_context_tokens: int | None = Field(default=None, ge=64, le=1_000_000)
    sanitize_pii: bool = Field(default=False)


class OpenAIChatCompressResponse(BaseModel):
    messages: list[dict[str, str]]
    original_tokens: int
    compressed_tokens: int
    tokens_saved: int
    compression_ratio: float
    cost_saved_usd: float


# --- RAG Workbench Models ---


class RAGIndexRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=200_000)
    chunk_size: int = Field(default=400, ge=100, le=4000)
    chunk_overlap: int = Field(default=80, ge=0, le=500)
    source_name: str = Field(default="workspace_document", max_length=128)


class RAGFileUploadRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=256)
    content: str = Field(..., min_length=1, max_length=1_000_000)
    is_base64: bool = Field(default=False)
    chunk_size: int = Field(default=400, ge=100, le=4000)
    chunk_overlap: int = Field(default=80, ge=0, le=500)


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
    use_hyde: bool = Field(default=True)
    use_reranker: bool = Field(default=True)


class RAGQueryResponse(BaseModel):
    query: str
    expanded_query: str = ""
    added_terms: list[str] = Field(default_factory=list)
    results: list[dict[str, Any]]
    citations: dict[str, Any] = Field(default_factory=dict)
    total_indexed: int


# --- Evaluation, Needle-in-Haystack & A/B Experiment Models ---


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
    fusion_method: Literal["linear", "rrf"] = Field(default="linear")
    use_mmr: bool = Field(default=False)
    use_reranker: bool = Field(default=False)


class RankInspectResponse(BaseModel):
    alpha_used: float
    drift_detected: bool
    ranking_strategy: str
    scores: list[dict[str, Any]]


class NeedleTestRequest(BaseModel):
    haystack_turns: int = Field(default=20, ge=4, le=60)
    needle_depth_pct: int = Field(default=25, ge=0, le=100)
    top_k: int = Field(default=3, ge=1, le=10)
    fusion_method: Literal["linear", "rrf"] = Field(default="rrf")
    compression_mode: str = Field(default="balanced")


class ABExperimentRequest(BaseModel):
    history: list[Turn] = Field(..., min_length=1, max_length=200)
    current_message: str = Field(..., min_length=1, max_length=50_000)
    variant_a: dict[str, Any] = Field(default_factory=lambda: {"top_k": 3, "fusion_method": "linear", "compression_mode": "balanced"})
    variant_b: dict[str, Any] = Field(default_factory=lambda: {"top_k": 3, "fusion_method": "rrf", "use_mmr": True, "use_reranker": True, "compression_mode": "code_preserving"})


# --- Security & Sanitization Endpoint Models ---


class SanitizeRequest(BaseModel):
    text: str = Field(..., max_length=100_000)
    redact_pii: bool = Field(default=True)


class SanitizeResponse(BaseModel):
    sanitized_text: str
    xss_stripped: int
    redactions_count: int
    redacted_types: list[str]


class GuardScanRequest(BaseModel):
    text: str = Field(..., max_length=100_000)
    redact_pii: bool = Field(default=True)


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
    version: str = "3.0.0"
    environment: str = "development"
    llm_available: bool = False
    uptime_seconds: float = 0.0
    circuit_breaker_state: str = "CLOSED"
    features: dict[str, bool] = Field(default_factory=dict)
