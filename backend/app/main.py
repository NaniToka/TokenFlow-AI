"""
TokenFlow AI - Production API Server
Intelligent Context Management, RAG & Prompt Memory Optimization Platform v3.0.
"""

import asyncio
import base64
import json
import os
import time
from typing import Literal

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.dependencies import (
    get_compression_pipeline,
    get_container,
    get_context_retriever,
    get_quality_evaluator,
    get_ranking_engine,
    get_stats_tracker,
)
from app.core.guardrails import PromptInjectionFirewall
from app.core.lifecycle import lifespan
from app.core.log_buffer import audit_log_buffer
from app.core.logging import get_correlation_id, get_logger
from app.core.metrics import telemetry
from app.core.middleware import (
    CorrelationMiddleware,
    SecurityHeadersMiddleware,
    TimingMiddleware,
)
from app.core.sanitizer import InputSanitizer
from app.schemas import (
    ABExperimentRequest,
    AsyncTaskResponse,
    BatchCompressRequest,
    BatchCompressResponse,
    CompressionMode,
    CompressRequest,
    CompressResponse,
    ErrorCode,
    ErrorDetail,
    ErrorResponse,
    EvaluateRequest,
    EvaluateResponse,
    GuardScanRequest,
    HealthStatus,
    NeedleTestRequest,
    OpenAIChatCompressRequest,
    OpenAIChatCompressResponse,
    RAGChunkItem,
    RAGFileUploadRequest,
    RAGIndexRequest,
    RAGIndexResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    RankInspectRequest,
    RankInspectResponse,
    SanitizeRequest,
    SanitizeResponse,
)
from app.services.cache.semantic_cache import embedding_cache, summary_cache
from app.services.compression.openai_adapter import (
    compress_response_to_openai_messages,
    openai_messages_to_compress_request,
)
from app.services.compression.pipeline import CompressionPipeline
from app.services.evaluation.ab_runner import run_ab_experiment
from app.services.evaluation.evaluator import ContextQualityEvaluator
from app.services.evaluation.needle_test import run_needle_in_haystack_test
from app.services.export.exporter import PromptExporter
from app.services.export.sdk_snippets import generate_sdk_snippets
from app.services.llm.circuit_breaker import llm_circuit_breaker
from app.services.rag.ingestor import parse_uploaded_file
from app.services.rag.retriever import ContextRetriever
from app.services.ranking.engine import RankingEngine
from app.services.stats_logger import StatsTracker
from app.services.tasks.background_worker import async_task_queue
from app.utils.metrics import metrics_registry
from app.utils.token_counter import list_supported_models

logger = get_logger(__name__)

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT_PER_MINUTE])

app = FastAPI(
    title=settings.APP_NAME,
    description="Production-grade Prompt Memory Optimizer, RAG & Context Middleware Platform",
    version="3.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Core", "description": "Health, models, SDK snippets, and system diagnostics"},
        {"name": "Compression", "description": "Prompt optimization, OpenAI adapter, SSE/async jobs"},
        {"name": "RAG", "description": "Semantic chunking, file ingestion, HyDE, and citations"},
        {"name": "Evaluation", "description": "Quality scoring, Needle-in-a-Haystack, and A/B experiments"},
        {"name": "Security", "description": "Prompt injection firewall and PII redaction"},
        {"name": "Analytics", "description": "Metrics, P50/P95/P99 telemetry, cache, and audit traces"},
        {"name": "Streaming", "description": "Real-time WebSocket and SSE streaming"},
    ],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- Middleware Stack ---
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(TimingMiddleware)
app.add_middleware(CorrelationMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if settings.is_production else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Correlation-ID", "X-Request-ID", "X-Response-Time-Ms"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = [
        ErrorDetail(
            field=" -> ".join(str(loc) for loc in err["loc"]),
            message=err["msg"],
            value=err.get("input"),
        )
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error=ErrorCode.VALIDATION_ERROR,
            message="Request validation failed. Please check the payload structure.",
            details=details,
            correlation_id=get_correlation_id(),
        ).model_dump(),
    )


# --- Health, Models & SDK Codegen ---
_SERVER_START_TIME = time.time()


@app.get("/health", tags=["Core"], response_model=HealthStatus)
@app.get("/api/v1/health", tags=["Core"], response_model=HealthStatus)
def health_check():
    """System health check with LLM connectivity, circuit breaker state, and feature flags."""
    container = get_container()
    return HealthStatus(
        status="healthy",
        service=settings.APP_NAME,
        version="3.0.0",
        environment=settings.ENVIRONMENT.value,
        llm_available=container.llm_client.is_available,
        uptime_seconds=round(time.time() - _SERVER_START_TIME, 2),
        circuit_breaker_state=llm_circuit_breaker.state.value,
        features={
            "semantic_cache": settings.features.ENABLE_SEMANTIC_CACHE,
            "drift_detection": settings.features.ENABLE_DRIFT_DETECTION,
            "bm25_ranking": settings.features.ENABLE_BM25_RANKING,
            "adaptive_alpha": settings.features.ENABLE_ADAPTIVE_ALPHA,
            "websocket_streaming": settings.features.ENABLE_WEBSOCKET_STREAMING,
            "multi_model": settings.features.ENABLE_MULTI_MODEL,
        },
    )


@app.get("/api/v1/models", tags=["Core"])
def get_supported_models():
    """Returns supported target LLM pricing profiles and compression mode presets."""
    return {
        "models": list_supported_models(),
        "compression_modes": [
            {
                "id": CompressionMode.BALANCED.value,
                "label": "Balanced Hybrid",
                "description": "Balances semantic similarity, BM25 keywords, and exponential recency.",
            },
            {
                "id": CompressionMode.AGGRESSIVE.value,
                "label": "Aggressive Cost Saver",
                "description": "Amplifies off-topic drift penalty and trims top-K window to maximize savings.",
            },
            {
                "id": CompressionMode.CODE_PRESERVING.value,
                "label": "Code & Stack-Trace Guard",
                "description": "Boosts turns containing code blocks, SQL queries, and error traces.",
            },
            {
                "id": CompressionMode.VERBATIM_FACTS.value,
                "label": "Verbatim Metrics & Entities",
                "description": "Prioritizes turns with numerical constants, metrics, and exact identifiers.",
            },
        ],
    }


@app.get("/api/v1/sdk-snippets", tags=["Core"])
def get_sdk_snippets(
    target_model: str = "gemini-1.5-flash",
    compression_mode: str = "balanced",
    top_k: int = 3,
    fusion_method: str = "rrf",
    sanitize_pii: bool = True,
):
    """Generates drop-in integration code snippets for Python, TypeScript, OpenAI adapter, and cURL."""
    return generate_sdk_snippets(
        target_model=target_model,
        compression_mode=compression_mode,
        top_k=top_k,
        fusion_method=fusion_method,
        sanitize_pii=sanitize_pii,
    )


# --- Compression Endpoints ---
@app.post("/api/v1/compress", tags=["Compression"], response_model=CompressResponse)
@limiter.limit(settings.RATE_LIMIT_PER_MINUTE)
def compress_prompt(
    request: Request,
    body: CompressRequest,
    pipeline: CompressionPipeline = Depends(get_compression_pipeline),
):
    """Compresses conversation history and user query into an optimized prompt."""
    if not body.current_message or not body.current_message.strip():
        raise HTTPException(status_code=400, detail="current_message parameter cannot be empty.")

    try:
        return pipeline.compress(body)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("compression_pipeline_error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="An internal server error occurred while compressing the prompt.",
        ) from e


@app.post("/api/v1/chat/compress", tags=["Compression"], response_model=OpenAIChatCompressResponse)
def openai_chat_compress(
    body: OpenAIChatCompressRequest,
    pipeline: CompressionPipeline = Depends(get_compression_pipeline),
):
    """Drop-in OpenAI-format `messages: [{role, content}]` context compressor."""
    try:
        req = openai_messages_to_compress_request(
            messages=body.messages,
            top_k=body.top_k,
            target_model=body.target_model,
            compression_mode=body.compression_mode,
            max_context_tokens=body.max_context_tokens,
            sanitize_pii=body.sanitize_pii,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    res = pipeline.compress(req)
    out_messages = compress_response_to_openai_messages(
        res,
        system_instruction=req.system_instruction,
        current_message=req.current_message,
    )
    return OpenAIChatCompressResponse(
        messages=out_messages,
        original_tokens=res.original_tokens,
        compressed_tokens=res.compressed_tokens,
        tokens_saved=res.tokens_saved,
        compression_ratio=res.compression_ratio,
        cost_saved_usd=res.cost_saved_usd,
    )


@app.post("/api/v1/compress/stream", tags=["Streaming"])
async def sse_compress_stream(
    body: CompressRequest,
    pipeline: CompressionPipeline = Depends(get_compression_pipeline),
):
    """Server-Sent Events (SSE) endpoint streaming incremental compression pipeline stages."""
    if not body.current_message or not body.current_message.strip():
        raise HTTPException(status_code=400, detail="current_message parameter cannot be empty.")

    async def _event_generator():
        yield f"data: {json.dumps({'stage': 'init', 'message': 'Scanning firewall & deduplicating turns...'})}\n\n"
        await asyncio.sleep(0.01)
        yield f"data: {json.dumps({'stage': 'ranking', 'message': f'Executing {body.fusion_method.upper()} hybrid scoring...'})}\n\n"
        res = await asyncio.to_thread(pipeline.compress, body)
        yield f"data: {json.dumps({'stage': 'complete', 'result': res.model_dump()})}\n\n"

    return StreamingResponse(_event_generator(), media_type="text/event-stream")


@app.post("/api/v1/compress/batch", tags=["Compression"], response_model=BatchCompressResponse)
@limiter.limit("10/minute")
def batch_compress(
    request: Request,
    body: BatchCompressRequest,
    pipeline: CompressionPipeline = Depends(get_compression_pipeline),
):
    """Compress multiple conversations concurrently in a single batch."""
    results = []
    total_saved = 0
    total_cost_saved = 0.0

    for item in body.requests:
        res = pipeline.compress(item)
        results.append(res)
        total_saved += res.tokens_saved
        total_cost_saved += res.cost_saved_usd

    return BatchCompressResponse(
        results=results,
        total_tokens_saved=total_saved,
        total_cost_saved_usd=round(total_cost_saved, 8),
    )


@app.post("/api/v1/compress/async", tags=["Compression"], response_model=AsyncTaskResponse)
async def async_compress(
    body: CompressRequest,
    background_tasks: BackgroundTasks,
    pipeline: CompressionPipeline = Depends(get_compression_pipeline),
):
    """Enqueues a prompt compression job for non-blocking background execution."""
    if not body.current_message or not body.current_message.strip():
        raise HTTPException(status_code=400, detail="current_message parameter cannot be empty.")

    task_id = async_task_queue.create_task()

    async def _run_job():
        return await asyncio.to_thread(pipeline.compress, body)

    background_tasks.add_task(async_task_queue.execute_task, task_id, _run_job())
    task = async_task_queue.get_task(task_id)
    return AsyncTaskResponse(
        task_id=task_id,
        status=task.status.value if task else "PENDING",
    )


@app.get("/api/v1/tasks/{task_id}", tags=["Compression"], response_model=AsyncTaskResponse)
def get_async_task_status(task_id: str):
    """Polls status and result of an asynchronous compression job."""
    task = async_task_queue.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found.")

    return AsyncTaskResponse(
        task_id=task.task_id,
        status=task.status.value,
        duration_ms=task.duration_ms,
        result=task.result,
        error=task.error,
    )


# --- RAG Workbench Endpoints ---
@app.post("/api/v1/rag/index", tags=["RAG"], response_model=RAGIndexResponse)
def rag_index_document(
    body: RAGIndexRequest,
    retriever: ContextRetriever = Depends(get_context_retriever),
):
    """Chunks a document semantically and indexes it in the hybrid RAG store."""
    new_chunks = retriever.index_document_with_chunks(
        text=body.text,
        metadata={"source": body.source_name},
        chunk_size=body.chunk_size,
        chunk_overlap=body.chunk_overlap,
    )
    return RAGIndexResponse(
        chunks_indexed=len(new_chunks),
        total_store_chunks=retriever.total_chunks,
        chunks=[
            RAGChunkItem(
                chunk_id=c.chunk_id,
                text=c.text,
                token_count=c.token_count,
                start_char=c.start_char,
                end_char=c.end_char,
                metadata=c.metadata,
            )
            for c in new_chunks
        ],
    )


@app.post("/api/v1/rag/upload", tags=["RAG"], response_model=RAGIndexResponse)
def rag_upload_file(
    body: RAGFileUploadRequest,
    retriever: ContextRetriever = Depends(get_context_retriever),
):
    """Ingests a text, Markdown, Python, JSON, CSV, or log file into the RAG store."""
    try:
        raw_bytes = base64.b64decode(body.content) if body.is_base64 else body.content.encode("utf-8")
        doc = parse_uploaded_file(body.filename, raw_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    new_chunks = retriever.index_document_with_chunks(
        text=doc.normalized_text,
        metadata={"source": doc.filename, "extension": doc.extension, "lines": doc.line_count},
        chunk_size=body.chunk_size,
        chunk_overlap=body.chunk_overlap,
    )
    return RAGIndexResponse(
        chunks_indexed=len(new_chunks),
        total_store_chunks=retriever.total_chunks,
        chunks=[
            RAGChunkItem(
                chunk_id=c.chunk_id,
                text=c.text,
                token_count=c.token_count,
                start_char=c.start_char,
                end_char=c.end_char,
                metadata=c.metadata,
            )
            for c in new_chunks
        ],
    )


@app.post("/api/v1/rag/query", tags=["RAG"], response_model=RAGQueryResponse)
def rag_query_chunks(
    body: RAGQueryRequest,
    retriever: ContextRetriever = Depends(get_context_retriever),
):
    """Retrieves top-K chunks with HyDE query expansion, N-gram reranking, and grounding citations."""
    adv = retriever.retrieve_advanced(
        query=body.query,
        top_k=body.top_k,
        alpha=body.alpha,
        use_hyde=body.use_hyde,
        use_reranker=body.use_reranker,
    )
    return RAGQueryResponse(
        query=body.query,
        expanded_query=str(adv["expanded_query"]),
        added_terms=list(adv["added_terms"]),
        results=list(adv["results"]),
        citations=dict(adv["citations"]),
        total_indexed=retriever.total_chunks,
    )


@app.delete("/api/v1/rag/clear", tags=["RAG"])
def rag_clear_store(retriever: ContextRetriever = Depends(get_context_retriever)):
    """Clears all chunks from the in-memory RAG document store."""
    retriever.clear()
    return {"status": "cleared", "total_indexed": 0}


# --- Evaluation, Needle-in-a-Haystack & A/B Experiments ---
@app.post("/api/v1/evaluate", tags=["Evaluation"], response_model=EvaluateResponse)
def evaluate_compression(
    body: EvaluateRequest,
    evaluator: ContextQualityEvaluator = Depends(get_quality_evaluator),
):
    """Runs automated quality grading across lexical recall, entity coverage, and hallucination risk."""
    report = evaluator.evaluate(body.history, body.response)
    return EvaluateResponse(
        original_tokens=report.original_tokens,
        compressed_tokens=report.compressed_tokens,
        tokens_saved=report.tokens_saved,
        compression_ratio=report.compression_ratio,
        lexical_recall=report.lexical_recall,
        entity_coverage=report.entity_coverage,
        semantic_fidelity=report.semantic_fidelity,
        hallucination_risk=report.hallucination_risk,
        composite_grade=report.composite_grade,
    )


@app.post("/api/v1/rank/inspect", tags=["Evaluation"], response_model=RankInspectResponse)
def inspect_ranking_ablation(
    body: RankInspectRequest,
    ranker: RankingEngine = Depends(get_ranking_engine),
):
    """Inspects per-turn scores across Linear/RRF fusion, MMR diversity, and Cross-Encoder reranking."""
    res = ranker.rank_turns(
        history=body.history,
        current_message=body.current_message,
        top_k=body.top_k,
        alpha=body.alpha,
        compression_mode=body.compression_mode.value,
        fusion_method=body.fusion_method,
        use_mmr=body.use_mmr,
        use_reranker=body.use_reranker,
    )
    return RankInspectResponse(
        alpha_used=res.alpha_used,
        drift_detected=res.drift_detected,
        ranking_strategy=res.ranking_strategy,
        scores=res.scores,
    )


@app.post("/api/v1/evaluate/needle", tags=["Evaluation"])
def run_needle_stress_test(
    body: NeedleTestRequest,
    pipeline: CompressionPipeline = Depends(get_compression_pipeline),
):
    """Runs a Needle-in-a-Haystack recall stress test at configurable dialogue depth."""
    return run_needle_in_haystack_test(
        pipeline=pipeline,
        haystack_turns=body.haystack_turns,
        needle_depth_pct=body.needle_depth_pct,
        top_k=body.top_k,
        fusion_method=body.fusion_method,
        compression_mode=body.compression_mode,
    )


@app.post("/api/v1/experiments/compare", tags=["Evaluation"])
def compare_ab_strategies(
    body: ABExperimentRequest,
    pipeline: CompressionPipeline = Depends(get_compression_pipeline),
    evaluator: ContextQualityEvaluator = Depends(get_quality_evaluator),
):
    """Runs side-by-side Variant A vs Variant B compression strategies and computes deltas."""
    return run_ab_experiment(
        pipeline=pipeline,
        evaluator=evaluator,
        history=body.history,
        current_message=body.current_message,
        variant_a=body.variant_a,
        variant_b=body.variant_b,
    )


# --- Security & Prompt Firewall Endpoints ---
@app.post("/api/v1/sanitize", tags=["Security"], response_model=SanitizeResponse)
def sanitize_prompt_text(body: SanitizeRequest):
    """Scans and sanitizes text for XSS injections and optional sensitive PII/API credentials."""
    res = InputSanitizer.sanitize_and_redact(body.text, redact_pii=body.redact_pii)
    return SanitizeResponse(
        sanitized_text=res.sanitized_text,
        xss_stripped=res.xss_stripped,
        redactions_count=res.redactions_count,
        redacted_types=res.redacted_types,
    )


@app.post("/api/v1/guard/scan", tags=["Security"])
def scan_prompt_guardrails(body: GuardScanRequest):
    """Runs full Prompt Injection Firewall + PII & XSS redaction audit."""
    fw = PromptInjectionFirewall.scan(body.text)
    san = InputSanitizer.sanitize_and_redact(body.text, redact_pii=body.redact_pii)
    return {
        "firewall": {
            "is_safe": fw.is_safe,
            "risk_score": fw.risk_score,
            "highest_severity": fw.highest_severity,
            "findings": [
                {
                    "rule_id": f.rule_id,
                    "severity": f.severity,
                    "description": f.description,
                    "matched_excerpt": f.matched_excerpt,
                }
                for f in fw.findings
            ],
        },
        "sanitization": {
            "sanitized_text": san.sanitized_text,
            "xss_stripped": san.xss_stripped,
            "redactions_count": san.redactions_count,
            "redacted_types": san.redacted_types,
        },
    }


# --- Export Endpoint ---
@app.post("/api/v1/export/{fmt}", tags=["Compression"])
def export_compression_report(
    fmt: Literal["markdown", "json", "csv"],
    body: CompressResponse,
):
    """Serializes a compression output into Markdown, JSON, or CSV turn-scoring audit format."""
    if fmt == "markdown":
        content = PromptExporter.to_markdown(body)
        return Response(
            content=content,
            media_type="text/markdown",
            headers={"Content-Disposition": "attachment; filename=tokenflow_report.md"},
        )
    if fmt == "csv":
        content = PromptExporter.to_csv(body)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=tokenflow_scores.csv"},
        )
    content = PromptExporter.to_json(body)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=tokenflow_payload.json"},
    )


# --- WebSocket Streaming ---
@app.websocket("/api/v1/ws/compress")
async def websocket_compress(websocket: WebSocket):
    """WebSocket endpoint streaming incremental compression pipeline stages."""
    await websocket.accept()
    container = get_container()
    pipeline = container.compression_pipeline

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            req = CompressRequest(**payload)

            await websocket.send_json({"stage": "init", "message": "Sanitizing, scanning firewall & deduplicating..."})
            await websocket.send_json({"stage": "ranking", "message": f"Running {req.fusion_method.upper()} + drift scoring..."})
            await websocket.send_json({"stage": "summarizing", "message": "Packing token budget & generating memory note..."})

            response = pipeline.compress(req)

            await websocket.send_json({
                "stage": "complete",
                "result": response.model_dump(),
            })
    except WebSocketDisconnect:
        logger.info("websocket_client_disconnected")
    except Exception as e:
        logger.error("websocket_error", error=str(e))
        try:
            await websocket.send_json({"stage": "error", "message": str(e)})
            await websocket.close()
        except Exception:
            pass


# --- Analytics, Cache, Circuit Breaker, Audit Logs & Telemetry ---
@app.get("/metrics", tags=["Analytics"], response_class=PlainTextResponse)
def get_prometheus_metrics():
    """Prometheus metrics scraping endpoint with latency histogram buckets."""
    return PlainTextResponse(
        metrics_registry.generate_prometheus_output(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


@app.get("/api/v1/telemetry", tags=["Analytics"])
def get_runtime_telemetry():
    """Returns P50/P90/P95/P99 latency percentiles, circuit breaker state, and cache telemetry."""
    return {
        "latency": telemetry.summary(),
        "circuit_breaker": llm_circuit_breaker.status(),
        "cache": {
            "summary_cache": summary_cache.stats(),
            "embedding_cache": embedding_cache.stats(),
        },
    }


@app.get("/api/v1/circuit-breaker", tags=["Analytics"])
def get_circuit_breaker_status():
    """Returns upstream LLM circuit breaker diagnostics."""
    return llm_circuit_breaker.status()


@app.post("/api/v1/circuit-breaker/reset", tags=["Analytics"])
def reset_circuit_breaker():
    """Resets upstream LLM circuit breaker back to CLOSED."""
    llm_circuit_breaker.reset()
    return {"status": "reset", "circuit_breaker": llm_circuit_breaker.status()}


@app.get("/api/v1/logs", tags=["Analytics"])
def get_audit_logs(limit: int = 50):
    """Returns recent structured telemetry trace logs (zero PII/prompt text)."""
    return {"logs": audit_log_buffer.list_recent(limit=min(100, max(1, limit)))}


@app.delete("/api/v1/logs", tags=["Analytics"])
def clear_audit_logs():
    """Clears the in-memory telemetry trace buffer."""
    audit_log_buffer.clear()
    return {"status": "cleared"}


@app.get("/api/v1/cache/stats", tags=["Analytics"])
def get_cache_stats():
    """Returns detailed hit/miss telemetry for semantic LRU caches."""
    return {
        "summary_cache": summary_cache.stats(),
        "embedding_cache": embedding_cache.stats(),
    }


@app.post("/api/v1/cache/clear", tags=["Analytics"])
def clear_caches():
    """Flushes semantic summary and embedding LRU caches."""
    summary_cache.clear()
    embedding_cache.clear()
    return {"status": "cleared", "message": "All semantic caches flushed."}


@app.get("/api/v1/stats", tags=["Analytics"])
def get_session_stats(tracker: StatsTracker = Depends(get_stats_tracker)):
    """Returns cumulative session analytics and request history breakdown."""
    return tracker.get_stats()


@app.post("/api/v1/stats/reset", tags=["Analytics"])
def reset_session_stats(tracker: StatsTracker = Depends(get_stats_tracker)):
    """Resets all in-memory session statistics and history logs."""
    tracker.reset_stats()
    return {"status": "success", "message": "Session statistics reset successfully."}


# --- Static File & SPA Mounting ---
base_dir = os.path.dirname(os.path.abspath(__file__))
possible_dist_dirs = [
    os.path.abspath(os.path.join(base_dir, "../../frontend/dist")),
    os.path.abspath(os.path.join(base_dir, "../static")),
]

frontend_dist = None
for candidate in possible_dist_dirs:
    if os.path.exists(candidate) and os.path.isdir(candidate):
        frontend_dist = candidate
        break

if frontend_dist and os.path.exists(frontend_dist):
    dist_root: str = str(frontend_dist)
    assets_dir = os.path.join(dist_root, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def catch_all(full_path: str):
        if (
            full_path.startswith("api/")
            or full_path.startswith("docs")
            or full_path.startswith("redoc")
            or full_path.startswith("openapi.json")
            or full_path == "metrics"
        ):
            raise HTTPException(status_code=404, detail="API route not found")

        file_path = os.path.join(dist_root, full_path)
        if full_path and os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)

        index_html = os.path.join(dist_root, "index.html")
        if os.path.exists(index_html):
            return FileResponse(index_html)

        raise HTTPException(status_code=404, detail="Frontend asset not found")
