from datetime import datetime, timezone
from typing import Dict, Any, List
from app.schemas import CompressResponse


class StatsTracker:
    """
    In-memory session statistics manager for real-time dashboard analytics.
    Persists data strictly in-memory during server execution for privacy compliance.
    """
    def __init__(self):
        self.reset_stats()

    def reset_stats(self) -> None:
        self.total_requests: int = 0
        self.total_original_tokens: int = 0
        self.total_compressed_tokens: int = 0
        self.total_tokens_saved: int = 0
        self.total_cost_before_usd: float = 0.0
        self.total_cost_after_usd: float = 0.0
        self.total_cost_saved_usd: float = 0.0
        self.request_history: List[Dict[str, Any]] = []

    def log_compression(self, response: CompressResponse) -> None:
        self.total_requests += 1
        self.total_original_tokens += response.original_tokens
        self.total_compressed_tokens += response.compressed_tokens
        self.total_tokens_saved += response.tokens_saved
        self.total_cost_before_usd = round(self.total_cost_before_usd + response.cost_before_usd, 8)
        self.total_cost_after_usd = round(self.total_cost_after_usd + response.cost_after_usd, 8)
        self.total_cost_saved_usd = round(self.total_cost_saved_usd + response.cost_saved_usd, 8)

        log_entry = {
            "id": self.total_requests,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "original_tokens": response.original_tokens,
            "compressed_tokens": response.compressed_tokens,
            "tokens_saved": response.tokens_saved,
            "cost_before_usd": response.cost_before_usd,
            "cost_after_usd": response.cost_after_usd,
            "cost_saved_usd": response.cost_saved_usd,
            "compression_ratio": response.compression_ratio
        }
        self.request_history.append(log_entry)

    def get_stats(self) -> Dict[str, Any]:
        if self.total_original_tokens > 0:
            avg_compression_ratio = round(
                (1.0 - (self.total_compressed_tokens / self.total_original_tokens)) * 100.0, 2
            )
        else:
            avg_compression_ratio = 0.0

        return {
            "total_requests": self.total_requests,
            "total_original_tokens": self.total_original_tokens,
            "total_compressed_tokens": self.total_compressed_tokens,
            "total_tokens_saved": self.total_tokens_saved,
            "total_cost_before_usd": round(self.total_cost_before_usd, 8),
            "total_cost_after_usd": round(self.total_cost_after_usd, 8),
            "total_cost_saved_usd": round(self.total_cost_saved_usd, 8),
            "avg_compression_ratio": avg_compression_ratio,
            "request_history": list(self.request_history)
        }


stats_tracker = StatsTracker()
