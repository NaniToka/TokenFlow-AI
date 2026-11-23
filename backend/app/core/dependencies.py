"""
Dependency Injection container for clean service resolution.

Provides FastAPI-compatible dependency functions that inject
configured service instances into route handlers.
"""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from app.core.config import Settings, get_settings

if TYPE_CHECKING:
    from app.services.ranking.engine import RankingEngine
    from app.services.compression.pipeline import CompressionPipeline
    from app.services.stats_logger import StatsTracker
    from app.services.llm.client import LLMClientManager


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
