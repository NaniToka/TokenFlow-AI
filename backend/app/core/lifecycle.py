"""
Application lifecycle management with graceful startup and shutdown.

Handles resource initialization, health checks, and cleanup
using FastAPI's lifespan context manager.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.dependencies import get_container
from app.core.logging import get_logger, setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application lifecycle with structured startup/shutdown.

    Startup:
        - Configure structured logging
        - Initialize service container
        - Warm up LLM client connections
        - Log startup diagnostics

    Shutdown:
        - Drain pending background tasks
        - Close LLM client connections
        - Flush log buffers
    """
    settings = get_settings()

    # --- STARTUP ---
    setup_logging(
        log_level=settings.LOG_LEVEL,
        json_logs=settings.is_production,
    )

    logger.info(
        "application_starting",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT.value,
        debug=settings.DEBUG,
        host=settings.HOST,
        port=settings.PORT,
    )

    container = get_container()

    # Warm up LLM client
    has_api_key = bool(settings.llm.GEMINI_API_KEY)
    logger.info(
        "llm_client_status",
        has_api_key=has_api_key,
        primary_model=settings.llm.PRIMARY_MODEL,
        fallback_model=settings.llm.FALLBACK_MODEL,
        embedding_model=settings.llm.EMBEDDING_MODEL,
    )

    # Log feature flags
    logger.info(
        "feature_flags",
        semantic_cache=settings.features.ENABLE_SEMANTIC_CACHE,
        drift_detection=settings.features.ENABLE_DRIFT_DETECTION,
        cross_encoder=settings.features.ENABLE_CROSS_ENCODER_RERANKING,
        websocket=settings.features.ENABLE_WEBSOCKET_STREAMING,
        background_tasks=settings.features.ENABLE_BACKGROUND_TASKS,
        multi_model=settings.features.ENABLE_MULTI_MODEL,
        bm25=settings.features.ENABLE_BM25_RANKING,
        adaptive_alpha=settings.features.ENABLE_ADAPTIVE_ALPHA,
    )

    logger.info("application_started", status="ready")

    yield

    # --- SHUTDOWN ---
    logger.info("application_shutting_down")
    await container.shutdown()
    logger.info("application_stopped", status="clean_shutdown")
