"""
TokenFlow AI - Production API Server
Intelligent Context Management & Prompt Memory Optimization Platform.
"""

import asyncio
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
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
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
from app.core.lifecycle import lifespan
from app.core.logging import get_correlation_id, get_logger
from app.core.metrics import telemetry
from app.core.middleware import (
    CorrelationMiddleware,
    SecurityHeadersMiddleware,
    TimingMiddleware,
)
from app.core.sanitizer import InputSanitizer
from app.schemas import (
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
    HealthStatus,
    RAGChunkItem,
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
from app.services.compression.pipeline import CompressionPipeline
from app.services.evaluation.evaluator import ContextQualityEvaluator
from app.services.export.exporter import PromptExporter
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
    description="Production-grade Prompt Memory Optimizer & Intelligent Context Middleware API",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Core", "description": "Health, models, and system diagnostics"},
        {"name": "Compression", "description": "Prompt optimization, async jobs, and context reduction"},
        {"name": "RAG", "description": "Semantic chunking and hybrid sparse-dense retrieval"},
        {"name": "Evaluation", "description": "Automated quality scoring and ranking ablation"},
        {"name": "Security", "description": "PII redaction and prompt sanitization"},
        {"name": "Analytics", "description": "Token reduction metrics, cache stats, and P50/P95/P99 telemetry"},
        {"name": "Streaming", "description": "Real-time WebSocket compression"},
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


# --- Exception Handlers ---
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


# --- Health, Models & Diagnostics ---
_SERVER_START_TIME = time.time()


@app.get("/health", tags=["Core"], response_model=HealthStatus)
@app.get("/api/v1/health", tags=["Core"], response_model=HealthStatus)
def health_check():
    """System health check with LLM connectivity and active feature flags."""
    container = get_container()
    return HealthStatus(
        status="healthy",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT.value,
        llm_available=container.llm_client.is_available,
        uptime_seconds=round(time.time() - _SERVER_START_TIME, 2),
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


# --- Compression Endpoints ---
@app.post("/api/v1/compress", tags=["Compression"], response_model=CompressResponse)
@limiter.limit(settings.RATE_LIMIT_PER_MINUTE)
def compress_prompt(
    request: Request,
    body: CompressRequest,
    pipeline: CompressionPipeline = Depends(get_compression_pipeline),
):
    """
    Compresses conversation history and user query into an optimized prompt.
    Processes request in-memory with stateless execution.
    """
    if not body.current_message or not body.current_message.strip():
        raise HTTPException(status_code=400, detail="current_message parameter cannot be empty.")

    try:
        response = pipeline.compress(body)
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("compression_pipeline_error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="An internal server error occurred while compressing the prompt.",
        ) from e


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


@app.post("/api/v1/rag/query", tags=["RAG"], response_model=RAGQueryResponse)
def rag_query_chunks(
    body: RAGQueryRequest,
    retriever: ContextRetriever = Depends(get_context_retriever),
):
    """Retrieves top-K semantically relevant chunks using BM25 + dense scoring."""
    results = retriever.retrieve(query=body.query, top_k=body.top_k, alpha=body.alpha)
    return RAGQueryResponse(
        query=body.query,
        results=results,
        total_indexed=retriever.total_chunks,
    )


@app.delete("/api/v1/rag/clear", tags=["RAG"])
def rag_clear_store(retriever: ContextRetriever = Depends(get_context_retriever)):
    """Clears all chunks from the in-memory RAG document store."""
    retriever.clear()
    return {"status": "cleared", "total_indexed": 0}


# --- Evaluation & Ranking Inspection Endpoints ---
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
    """Inspects per-turn BM25, semantic, recency, and drift scores without altering session metrics."""
    res = ranker.rank_turns(
        history=body.history,
        current_message=body.current_message,
        top_k=body.top_k,
        alpha=body.alpha,
        compression_mode=body.compression_mode.value,
    )
    return RankInspectResponse(
        alpha_used=res.alpha_used,
        drift_detected=res.drift_detected,
        ranking_strategy=res.ranking_strategy,
        scores=res.scores,
    )


# --- Security & Sanitization Endpoints ---
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
    """
    WebSocket endpoint for real-time streaming compression.
    Sends incremental phase updates: init -> ranking -> summarizing -> complete.
    """
    await websocket.accept()
    container = get_container()
    pipeline = container.compression_pipeline

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            req = CompressRequest(**payload)

            await websocket.send_json({"stage": "init", "message": "Sanitizing & counting baseline tokens..."})
            await websocket.send_json({"stage": "ranking", "message": "Running hybrid BM25 + dense vector + drift scoring..."})
            await websocket.send_json({"stage": "summarizing", "message": "Checking semantic LRU cache & compressing evicted context..."})

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


# --- Analytics, Cache & Telemetry ---
@app.get("/metrics", tags=["Analytics"], response_class=PlainTextResponse)
def get_prometheus_metrics():
    """Prometheus metrics scraping endpoint."""
    return PlainTextResponse(
        metrics_registry.generate_prometheus_output(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


@app.get("/api/v1/telemetry", tags=["Analytics"])
def get_runtime_telemetry():
    """Returns P50/P90/P95/P99 latency percentiles, HTTP status breakdown, and cache telemetry."""
    return {
        "latency": telemetry.summary(),
        "cache": {
            "summary_cache": summary_cache.stats(),
            "embedding_cache": embedding_cache.stats(),
        },
    }


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
