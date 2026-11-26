"""
Prometheus Metrics Registry for TokenFlow-AI.
Tracks request counts, token savings, latency histogram buckets, and circuit breaker state.
"""

from typing import Any

from app.services.llm.circuit_breaker import CircuitState, llm_circuit_breaker


class MetricsRegistry:
    """In-memory thread-safe metrics collector formatted for Prometheus exposition."""

    HISTOGRAM_BUCKETS = (0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0)

    def __init__(self):
        self._requests_total = 0
        self._requests_success = 0
        self._requests_error = 0
        self._tokens_original_total = 0
        self._tokens_compressed_total = 0
        self._tokens_saved_total = 0
        self._latency_sum = 0.0
        self._latency_count = 0
        self._bucket_counts: dict[float, int] = {b: 0 for b in self.HISTOGRAM_BUCKETS}

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
        for b in self.HISTOGRAM_BUCKETS:
            if duration_seconds <= b:
                self._bucket_counts[b] += 1

    def generate_prometheus_output(self) -> str:
        cb_state = llm_circuit_breaker.state
        cb_val = 0 if cb_state == CircuitState.CLOSED else (1 if cb_state == CircuitState.HALF_OPEN else 2)

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
            "# HELP tokenflow_request_duration_seconds Latency distribution of compression requests.",
            "# TYPE tokenflow_request_duration_seconds histogram",
        ]
        for b in self.HISTOGRAM_BUCKETS:
            lines.append(f'tokenflow_request_duration_seconds_bucket{{le="{b}"}} {self._bucket_counts[b]}')
        lines.append(f'tokenflow_request_duration_seconds_bucket{{le="+Inf"}} {self._latency_count}')
        lines.append(f"tokenflow_request_duration_seconds_sum {round(self._latency_sum, 6)}")
        lines.append(f"tokenflow_request_duration_seconds_count {self._latency_count}")
        lines.extend([
            "",
            "# HELP tokenflow_llm_circuit_breaker_state Upstream LLM circuit breaker (0=CLOSED, 1=HALF_OPEN, 2=OPEN).",
            "# TYPE tokenflow_llm_circuit_breaker_state gauge",
            f"tokenflow_llm_circuit_breaker_state {cb_val}",
        ])
        return "\n".join(lines) + "\n"

    def get_stats_dict(self) -> dict[str, Any]:
        avg_latency = (self._latency_sum / self._latency_count) if self._latency_count > 0 else 0.0
        return {
            "requests_total": self._requests_total,
            "tokens_saved_total": self._tokens_saved_total,
            "average_latency_seconds": round(avg_latency, 6),
            "circuit_breaker": llm_circuit_breaker.status(),
        }


metrics_registry = MetricsRegistry()
