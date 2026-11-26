"""
In-Memory Structured Telemetry Audit Log Ring Buffer.

Retains the most recent 100 request telemetry entries (correlation ID, route,
latency, status, token counts — NEVER raw user prompt text) for live inspection.
"""

from __future__ import annotations

import threading
from collections import deque
from datetime import datetime, timezone
from typing import Any


class AuditLogBuffer:
    """Thread-safe bounded ring buffer for runtime observability."""

    def __init__(self, maxlen: int = 100):
        self._lock = threading.Lock()
        self._entries: deque[dict[str, Any]] = deque(maxlen=maxlen)

    def append(
        self,
        event: str,
        correlation_id: str | None = None,
        status_code: int = 200,
        latency_ms: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        with self._lock:
            self._entries.appendleft({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": event,
                "correlation_id": correlation_id or "internal",
                "status_code": status_code,
                "latency_ms": round(latency_ms, 2),
                "metadata": metadata or {},
            })

    def list_recent(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._entries)[:limit]

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


audit_log_buffer = AuditLogBuffer(maxlen=100)
