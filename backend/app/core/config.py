"""
Multi-environment configuration management with validation and feature flags.

Supports: development, staging, production environments.
Loads from .env files with pydantic-settings validation.
"""

from enum import Enum
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class FeatureFlags(BaseSettings):
    """Runtime feature flags for gradual rollouts."""

    ENABLE_SEMANTIC_CACHE: bool = False
    ENABLE_DRIFT_DETECTION: bool = True
    ENABLE_CROSS_ENCODER_RERANKING: bool = False
    ENABLE_WEBSOCKET_STREAMING: bool = True
    ENABLE_BACKGROUND_TASKS: bool = True
    ENABLE_MULTI_MODEL: bool = True
    ENABLE_BM25_RANKING: bool = True
    ENABLE_ADAPTIVE_ALPHA: bool = True

    model_config = SettingsConfigDict(env_prefix="FF_", extra="ignore")


class LLMConfig(BaseSettings):
    """LLM provider configuration."""

    GEMINI_API_KEY: str = ""
    PRIMARY_MODEL: str = "gemini-2.0-flash"
    FALLBACK_MODEL: str = "gemini-1.5-flash"
    EMBEDDING_MODEL: str = "text-embedding-004"
    EMBEDDING_DIMENSIONS: int = 768
    SUMMARIZATION_MAX_TOKENS: int = 256
    TEMPERATURE: float = 0.3
    TOP_P: float = 0.95

    model_config = SettingsConfigDict(env_prefix="LLM_", extra="ignore")

    @field_validator("GEMINI_API_KEY")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        if v and v.startswith("your_"):
            return ""
        return v


class CacheConfig(BaseSettings):
    """Cache layer configuration."""

    REDIS_URL: str = "redis://localhost:6379/0"
    EMBEDDING_CACHE_TTL: int = 3600  # 1 hour
    SUMMARY_CACHE_TTL: int = 1800  # 30 minutes
    MAX_CACHE_SIZE: int = 10_000

    model_config = SettingsConfigDict(env_prefix="CACHE_", extra="ignore")


class RankingConfig(BaseSettings):
    """Ranking engine hyperparameters."""

    DEFAULT_TOP_K: int = 3
    MAX_TOP_K: int = 20
    DEFAULT_ALPHA: float = 0.7
    RECENCY_DECAY_FACTOR: float = 0.05
    BM25_K1: float = 1.5
    BM25_B: float = 0.75
    CROSS_ENCODER_THRESHOLD: float = 0.5
    DRIFT_WINDOW_SIZE: int = 5
    DRIFT_THRESHOLD: float = 0.3

    model_config = SettingsConfigDict(env_prefix="RANKING_", extra="ignore")


class Settings(BaseSettings):
    """Root application settings with multi-environment support."""

    # --- Core ---
    APP_NAME: str = "TokenFlow AI"
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # --- Server ---
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    ALLOWED_ORIGINS: list[str] | str = "http://localhost:3000,http://localhost:5173"
    RATE_LIMIT_PER_MINUTE: str = "60/minute"

    # --- Nested configs ---
    llm: LLMConfig = Field(default_factory=LLMConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    ranking: RankingConfig = Field(default_factory=RankingConfig)
    features: FeatureFlags = Field(default_factory=FeatureFlags)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__",
    )

    @property
    def cors_origins(self) -> list[str]:
        if isinstance(self.ALLOWED_ORIGINS, str):
            return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]
        return self.ALLOWED_ORIGINS

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == Environment.PRODUCTION

    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT == Environment.TESTING

    # Backward-compatible property
    @property
    def GEMINI_API_KEY(self) -> str:
        return self.llm.GEMINI_API_KEY


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached singleton settings loader."""
    return Settings()


# Module-level convenience alias
settings = get_settings()
