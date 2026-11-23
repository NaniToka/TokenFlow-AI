"""
TokenFlow AI - Production API Server
Intelligent Context Management & Prompt Memory Optimization Platform.
"""

import os
import json
import time
import logging
from typing import Any, Dict

from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from app.utils.metrics import metrics_registry
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.lifecycle import lifespan
from app.core.logging import get_logger, get_correlation_id
from app.core.middleware import (
    CorrelationMiddleware,
    TimingMiddleware,
    SecurityHeadersMiddleware,
)
from app.core.dependencies import (
    get_container,
    get_compression_pipeline,
    get_stats_tracker,
)
from app.schemas import (
    CompressRequest,
    CompressResponse,
    BatchCompressRequest,
    BatchCompressResponse,
    HealthStatus,
    ErrorResponse,
    ErrorCode,
    ErrorDetail,
)
from app.services.compression.pipeline import CompressionPipeline
from app.services.stats_logger import StatsTracker

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
        {"name": "Core", "description": "Health and system diagnostics"},
        {"name": "Compression", "description": "Prompt optimization and context reduction"},
        {"name": "Analytics", "description": "Token reduction metrics and session telemetry"},
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


# --- Health & Diagnostics ---
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
        start_time = time.perf_counter()
        response = pipeline.compress(body)
        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "prompt_compressed",
            tokens_saved=response.tokens_saved,
            ratio=response.compression_ratio,
            latency_ms=round(latency_ms, 2),
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("compression_pipeline_error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="An internal server error occurred while compressing the prompt.",
        )


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


# --- WebSocket Streaming ---
@app.websocket("/api/v1/ws/compress")
async def websocket_compress(websocket: WebSocket):
    """
    WebSocket endpoint for real-time streaming compression.
    Sends incremental phase updates: parsing -> ranking -> summarizing -> assembled.
    """
    await websocket.accept()
    container = get_container()
    pipeline = container.compression_pipeline

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            req = CompressRequest(**payload)

            await websocket.send_json({"stage": "init", "message": "Validating context turns..."})
            await websocket.send_json({"stage": "ranking", "message": "Executing hybrid BM25 + dense ranking..."})
            await websocket.send_json({"stage": "summarizing", "message": "Generating context note..."})

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


# --- Analytics & Telemetry ---
@app.get("/metrics", tags=["Analytics"], response_class=PlainTextResponse)
def get_prometheus_metrics():
    """Prometheus metrics scraping endpoint."""
    return PlainTextResponse(
        metrics_registry.generate_prometheus_output(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


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
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def catch_all(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("redoc") or full_path.startswith("openapi.json") or full_path == "metrics":
            raise HTTPException(status_code=404, detail="API route not found")

        file_path = os.path.join(frontend_dist, full_path)
        if full_path and os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)

        index_html = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_html):
            return FileResponse(index_html)

        raise HTTPException(status_code=404, detail="Frontend asset not found")
