"""
3-State Circuit Breaker for Resilient Upstream LLM Calls.

Prevents cascading timeout stalls when external LLM APIs degrade:
- CLOSED: Normal operation; tracks consecutive failure count.
- OPEN: Short-circuits immediately to offline fallback after threshold failures.
- HALF_OPEN: Allows a single probe request after cooldown to test recovery.
"""

from __future__ import annotations

import threading
import time
from enum import Enum


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class LLMCircuitBreaker:
    """Thread-safe 3-state circuit breaker."""

    def __init__(self, failure_threshold: int = 3, recovery_timeout_sec: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout_sec = recovery_timeout_sec
        self._lock = threading.Lock()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_ts = 0.0
        self._total_trips = 0

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if (
                self._state == CircuitState.OPEN
                and (time.time() - self._last_failure_ts) >= self.recovery_timeout_sec
            ):
                self._state = CircuitState.HALF_OPEN
            return self._state

    def allow_request(self) -> bool:
        """Return True if an upstream request should be attempted."""
        current = self.state
        return current in {CircuitState.CLOSED, CircuitState.HALF_OPEN}

    def record_success(self) -> None:
        with self._lock:
            self._failure_count = 0
            self._state = CircuitState.CLOSED

    def record_failure(self) -> None:
        with self._lock:
            self._failure_count += 1
            self._last_failure_ts = time.time()
            if self._failure_count >= self.failure_threshold:
                if self._state != CircuitState.OPEN:
                    self._total_trips += 1
                self._state = CircuitState.OPEN

    def reset(self) -> None:
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._last_failure_ts = 0.0

    def status(self) -> dict[str, object]:
        current = self.state
        return {
            "state": current.value,
            "failure_count": self._failure_count,
            "failure_threshold": self.failure_threshold,
            "total_trips": self._total_trips,
        }


llm_circuit_breaker = LLMCircuitBreaker()
