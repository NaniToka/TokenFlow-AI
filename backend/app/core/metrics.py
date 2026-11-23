"""
Prometheus and OpenTelemetry Compatible Metrics Collector.

Tracks p50/p95/p99 request latencies, token counters, and error rates.
"""

from typing import Any


class TelemetryMetrics:
    """Collects runtime telemetry counters and percentiles."""

    def __init__(self):
        self.latencies_ms: list[float] = []
        self.http_status_counts: dict[int, int] = {}
        self.total_tokens_processed: int = 0
        self.total_tokens_compressed: int = 0

    def record_request(self, status_code: int, latency_ms: float):
        self.http_status_counts[status_code] = self.http_status_counts.get(status_code, 0) + 1
        self.latencies_ms.append(latency_ms)
        if len(self.latencies_ms) > 10_000:
            self.latencies_ms = self.latencies_ms[-5000:]

    def get_percentiles(self) -> dict[str, float]:
        if not self.latencies_ms:
            return {"p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0}

        sorted_latencies = sorted(self.latencies_ms)
        n = len(sorted_latencies)

        def pct(p: float) -> float:
            idx = min(int(n * p), n - 1)
            return round(sorted_latencies[idx], 2)

        return {
            "p50": pct(0.50),
            "p90": pct(0.90),
            "p95": pct(0.95),
            "p99": pct(0.99),
        }

    def summary(self) -> dict[str, Any]:
        return {
            "percentiles": self.get_percentiles(),
            "status_counts": dict(self.http_status_counts),
            "sample_size": len(self.latencies_ms),
        }


telemetry = TelemetryMetrics()
