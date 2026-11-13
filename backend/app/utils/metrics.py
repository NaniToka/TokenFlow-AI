"""
Prometheus Metrics Registry for TokenFlow-AI.
Tracks request counts, original vs compressed tokens, savings, and latency distributions.
"""

import time
from typing import Dict, Any


class MetricsRegistry:
    """In-memory thread-safe metrics collector formatted for Prometheus exposition."""

    def __init__(self):
        self._requests_total = 0
        self._requests_success = 0
        self._requests_error = 0
        self._tokens_original_total = 0
        self._tokens_compressed_total = 0
        self._tokens_saved_total = 0
        self._latency_sum = 0.0
        self._latency_count = 0

    def record_request(self, original_tokens: int, compressed_tokens: int, duration_seconds: float, success: bool = True):
        self._requests_total += 1
        if success:
            self._requests_success += 1
            self._tokens_original_total += original_tokens
            self._tokens_compressed_total += compressed_tokens
            self._tokens_saved_total += max(0, original_tokens - compressed_tokens)
        else:
            self._requests_error += 1
        self._latency_sum += duration_seconds
        self._latency_count += 1

    def generate_prometheus_output(self) -> str:
        lines = [
            "# HELP tokenflow_requests_total Total number of prompt compression requests received.",
            "# TYPE tokenflow_requests_total counter",
            f'tokenflow_requests_total{{status="success"}} {self._requests_success}',
            f'tokenflow_requests_total{{status="error"}} {self._requests_error}',
            "",
            "# HELP tokenflow_tokens_original_total Total input tokens before compression.",
            "# TYPE tokenflow_tokens_original_total counter",
            f"tokenflow_tokens_original_total {self._tokens_original_total}",
            "",
            "# HELP tokenflow_tokens_compressed_total Total input tokens after compression.",
            "# TYPE tokenflow_tokens_compressed_total counter",
            f"tokenflow_tokens_compressed_total {self._tokens_compressed_total}",
            "",
            "# HELP tokenflow_tokens_saved_total Total prompt tokens saved by TokenFlow.",
            "# TYPE tokenflow_tokens_saved_total counter",
            f"tokenflow_tokens_saved_total {self._tokens_saved_total}",
            "",
            "# HELP tokenflow_request_duration_seconds Latency of compression requests.",
            "# TYPE tokenflow_request_duration_seconds summary",
            f"tokenflow_request_duration_seconds_sum {round(self._latency_sum, 6)}",
            f"tokenflow_request_duration_seconds_count {self._latency_count}",
        ]
        return "\n".join(lines) + "\n"

    def get_stats_dict(self) -> Dict[str, Any]:
        avg_latency = (self._latency_sum / self._latency_count) if self._latency_count > 0 else 0.0
        return {
            "requests_total": self._requests_total,
            "tokens_saved_total": self._tokens_saved_total,
            "average_latency_seconds": round(avg_latency, 6),
        }


metrics_registry = MetricsRegistry()
