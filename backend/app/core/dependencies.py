"""
Dependency Injection container for clean service resolution.

Provides FastAPI-compatible dependency functions that inject
configured service instances into route handlers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.config import Settings, get_settings

if TYPE_CHECKING:
    from app.services.compression.pipeline import CompressionPipeline
    from app.services.evaluation.evaluator import ContextQualityEvaluator
    from app.services.llm.client import LLMClientManager
    from app.services.rag.retriever import ContextRetriever
    from app.services.ranking.engine import RankingEngine
    from app.services.stats_logger import StatsTracker


class ServiceContainer:
    """
    Centralized service container for dependency injection.

    Lazily initializes services on first access and caches instances
    for the lifetime of the application.
    """

    def __init__(self, settings: Settings):
        self._settings = settings
        self._llm_client: LLMClientManager | None = None
        self._ranking_engine: RankingEngine | None = None
        self._compression_pipeline: CompressionPipeline | None = None
        self._stats_tracker: StatsTracker | None = None
        self._context_retriever: ContextRetriever | None = None
        self._quality_evaluator: ContextQualityEvaluator | None = None

    @property
    def settings(self) -> Settings:
        return self._settings

    @property
    def llm_client(self) -> LLMClientManager:
        if self._llm_client is None:
            from app.services.llm.client import LLMClientManager

            self._llm_client = LLMClientManager(self._settings.llm)
        return self._llm_client

    @property
    def ranking_engine(self) -> RankingEngine:
        if self._ranking_engine is None:
            from app.services.ranking.engine import RankingEngine

            self._ranking_engine = RankingEngine(
                config=self._settings.ranking,
                features=self._settings.features,
                llm_client=self.llm_client,
            )
        return self._ranking_engine

    @property
    def compression_pipeline(self) -> CompressionPipeline:
        if self._compression_pipeline is None:
            from app.services.compression.pipeline import CompressionPipeline

            self._compression_pipeline = CompressionPipeline(
                ranking_engine=self.ranking_engine,
                llm_client=self.llm_client,
                stats_tracker=self.stats_tracker,
                settings=self._settings,
            )
        return self._compression_pipeline

    @property
    def stats_tracker(self) -> StatsTracker:
        if self._stats_tracker is None:
            from app.services.stats_logger import StatsTracker

            self._stats_tracker = StatsTracker()
        return self._stats_tracker

    @property
    def context_retriever(self) -> ContextRetriever:
        if self._context_retriever is None:
            from app.services.rag.retriever import ContextRetriever

            self._context_retriever = ContextRetriever(llm_client=self.llm_client)
        return self._context_retriever

    @property
    def quality_evaluator(self) -> ContextQualityEvaluator:
        if self._quality_evaluator is None:
            from app.services.evaluation.evaluator import ContextQualityEvaluator

            self._quality_evaluator = ContextQualityEvaluator()
        return self._quality_evaluator

    async def shutdown(self) -> None:
        """Cleanup resources on application shutdown."""
        if self._llm_client:
            await self._llm_client.close()


# --- Global container singleton ---
_container: ServiceContainer | None = None


def get_container() -> ServiceContainer:
    """Get or create the global service container."""
    global _container
    if _container is None:
        _container = ServiceContainer(get_settings())
    return _container


def reset_container() -> None:
    """Reset container (for testing)."""
    global _container
    _container = None


# --- FastAPI Dependency Functions ---


def get_compression_pipeline():
    """FastAPI dependency for the compression pipeline."""
    return get_container().compression_pipeline


def get_stats_tracker():
    """FastAPI dependency for the stats tracker."""
    return get_container().stats_tracker


def get_ranking_engine():
    """FastAPI dependency for the ranking engine."""
    return get_container().ranking_engine


def get_context_retriever():
    """FastAPI dependency for the RAG context retriever."""
    return get_container().context_retriever


def get_quality_evaluator():
    """FastAPI dependency for the context quality evaluator."""
    return get_container().quality_evaluator
