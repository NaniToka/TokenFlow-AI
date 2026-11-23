"""
Enhanced in-memory session statistics tracker with latency tracking.

Thread-safe metrics collection for real-time dashboard analytics.
Persists data strictly in-memory for privacy compliance.
"""

import threading
from datetime import datetime, timezone
from typing import Any

from app.schemas import CompressResponse


class StatsTracker:
    """
    Thread-safe in-memory session statistics manager.

    Collects compression metrics per request and maintains
    running totals for dashboard display.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.reset_stats()

    def reset_stats(self) -> None:
        """Reset all counters and history."""
        with self._lock if hasattr(self, "_lock") else _DummyLock():
            self.total_requests: int = 0
            self.total_original_tokens: int = 0
            self.total_compressed_tokens: int = 0
            self.total_tokens_saved: int = 0
            self.total_cost_before_usd: float = 0.0
            self.total_cost_after_usd: float = 0.0
            self.total_cost_saved_usd: float = 0.0
            self.total_latency_ms: float = 0.0
            self.request_history: list[dict[str, Any]] = []

    def log_compression(
        self, response: CompressResponse, latency_ms: float = 0.0
    ) -> None:
        """Record metrics from a compression response."""
        with self._lock:
            self.total_requests += 1
            self.total_original_tokens += response.original_tokens
            self.total_compressed_tokens += response.compressed_tokens
            self.total_tokens_saved += response.tokens_saved
            self.total_cost_before_usd = round(
                self.total_cost_before_usd + response.cost_before_usd, 8
            )
            self.total_cost_after_usd = round(
                self.total_cost_after_usd + response.cost_after_usd, 8
            )
            self.total_cost_saved_usd = round(
                self.total_cost_saved_usd + response.cost_saved_usd, 8
            )
            self.total_latency_ms += latency_ms

            log_entry = {
                "id": self.total_requests,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "original_tokens": response.original_tokens,
                "compressed_tokens": response.compressed_tokens,
                "tokens_saved": response.tokens_saved,
                "cost_before_usd": response.cost_before_usd,
                "cost_after_usd": response.cost_after_usd,
                "cost_saved_usd": response.cost_saved_usd,
                "compression_ratio": response.compression_ratio,
                "latency_ms": round(latency_ms, 2),
                "ranking_strategy": response.metadata.ranking_strategy,
            }
            self.request_history.append(log_entry)

    def get_stats(self) -> dict[str, Any]:
        """Return current session statistics."""
        with self._lock:
            if self.total_original_tokens > 0:
                avg_ratio = round(
                    (1.0 - self.total_compressed_tokens / self.total_original_tokens)
                    * 100.0,
                    2,
                )
            else:
                avg_ratio = 0.0

            avg_latency = (
                round(self.total_latency_ms / self.total_requests, 2)
                if self.total_requests > 0
                else 0.0
            )

            return {
                "total_requests": self.total_requests,
                "total_original_tokens": self.total_original_tokens,
                "total_compressed_tokens": self.total_compressed_tokens,
                "total_tokens_saved": self.total_tokens_saved,
                "total_cost_before_usd": round(self.total_cost_before_usd, 8),
                "total_cost_after_usd": round(self.total_cost_after_usd, 8),
                "total_cost_saved_usd": round(self.total_cost_saved_usd, 8),
                "avg_compression_ratio": avg_ratio,
                "avg_latency_ms": avg_latency,
                "request_history": list(self.request_history),
            }


class _DummyLock:
    """No-op context manager for init before lock exists."""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


# Module-level singleton (backward compatible)
stats_tracker = StatsTracker()
