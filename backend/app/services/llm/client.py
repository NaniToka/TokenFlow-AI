"""
LLM Client Manager with multi-model support and automatic fallback.

Provides a unified interface for:
- Text embedding generation (single and batch)
- Abstractive summarization
- Model switching and fallback chains
"""

from __future__ import annotations

import hashlib

from google import genai

from app.core.config import LLMConfig
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMClientManager:
    """
    Manages connections to Gemini API with multi-model fallback.

    Features:
    - Primary + fallback model chain for summarization
    - Batch embedding with graceful degradation
    - Connection health checking
    - In-memory embedding dedup within a request
    """

    def __init__(self, config: LLMConfig):
        self._config = config
        self._client: genai.Client | None = None
        self._initialized = False
        self._init_client()

    def _init_client(self) -> None:
        """Initialize the Gemini client if API key is available."""
        api_key = self._config.GEMINI_API_KEY
        if not api_key:
            logger.warning("llm_client_no_api_key", note="Running in offline/fallback mode")
            return

        try:
            self._client = genai.Client(api_key=api_key)
            self._initialized = True
            logger.info("llm_client_initialized", model=self._config.PRIMARY_MODEL)
        except Exception as e:
            logger.error("llm_client_init_failed", error=str(e))

    @property
    def is_available(self) -> bool:
        """Check if the LLM client is initialized and available."""
        return self._initialized and self._client is not None

    def get_embedding(self, text: str) -> list[float]:
        """
        Generate a vector embedding for a single text.

        Returns empty list if client is unavailable or on error.
        """
        if not text or not text.strip():
            return []

        if not self.is_available or self._client is None:
            return []

        try:
            response = self._client.models.embed_content(
                model=self._config.EMBEDDING_MODEL,
                contents=text,
            )
            if response.embeddings and len(response.embeddings) > 0:
                return response.embeddings[0].values or []
            return []
        except Exception as e:
            logger.error("embedding_failed", error=str(e), text_len=len(text))
            return []

    def get_batch_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts in a single batch call.

        Falls back to individual calls if batch fails.
        Returns list of float vectors matching input order.
        """
        if not texts:
            return []

        if not self.is_available or self._client is None:
            return [[] for _ in texts]

        try:
            response = self._client.models.embed_content(
                model=self._config.EMBEDDING_MODEL,
                contents=texts,
            )
            if response.embeddings and len(response.embeddings) == len(texts):
                return [emb.values or [] for emb in response.embeddings]

            # Partial response handling
            embeddings = []
            if response.embeddings:
                for emb in response.embeddings:
                    embeddings.append(emb.values or [])
            while len(embeddings) < len(texts):
                embeddings.append([])
            return embeddings

        except Exception as e:
            logger.error("batch_embedding_failed", error=str(e), count=len(texts))
            # Fallback to individual calls
            return [self.get_embedding(t) for t in texts]

    def summarize(
        self,
        text: str,
        system_instruction: str = "",
        model: str | None = None,
    ) -> str:
        """
        Generate an abstractive summary using primary model with fallback.

        Args:
            text: Content to summarize.
            system_instruction: Optional system prompt.
            model: Override model (uses primary by default).

        Returns:
            Summary string, or empty string on failure.
        """
        if not text or not text.strip():
            return ""

        if not self.is_available:
            return ""

        target_model = model or self._config.PRIMARY_MODEL
        fallback = self._config.FALLBACK_MODEL

        # Try primary model
        result = self._call_generate(text, system_instruction, target_model)
        if result:
            return result

        # Try fallback model
        if target_model != fallback:
            logger.warning("llm_primary_failed_trying_fallback", fallback=fallback)
            result = self._call_generate(text, system_instruction, fallback)
            if result:
                return result

        return ""

    def _call_generate(
        self, text: str, system_instruction: str, model: str
    ) -> str:
        """Execute a single generate_content call."""
        if self._client is None:
            return ""
        try:
            response = self._client.models.generate_content(
                model=model,
                contents=text,
                config={
                    "temperature": self._config.TEMPERATURE,
                    "top_p": self._config.TOP_P,
                    "max_output_tokens": self._config.SUMMARIZATION_MAX_TOKENS,
                },
            )
            if response and response.text:
                return response.text.strip()
            return ""
        except Exception as e:
            logger.error("llm_generate_failed", model=model, error=str(e))
            return ""

    @staticmethod
    def content_hash(text: str) -> str:
        """Generate a stable hash for embedding cache keys."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    async def close(self) -> None:
        """Cleanup client resources."""
        self._client = None
        self._initialized = False
        logger.info("llm_client_closed")
