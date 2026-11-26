"""
Custom middleware stack for request processing.

Includes:
- Correlation ID injection and propagation
- Request timing and metrics collection (feeds telemetry percentiles)
- Security headers
"""

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.log_buffer import audit_log_buffer
from app.core.logging import (
    correlation_id_var,
    get_logger,
    request_meta_var,
    set_correlation_id,
)
from app.core.metrics import telemetry

logger = get_logger(__name__)

CORRELATION_HEADER = "X-Correlation-ID"
REQUEST_ID_HEADER = "X-Request-ID"
TIMING_HEADER = "X-Response-Time-Ms"


class CorrelationMiddleware(BaseHTTPMiddleware):
    """Injects and propagates correlation IDs for distributed tracing."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        cid = request.headers.get(CORRELATION_HEADER, str(uuid.uuid4()))
        request_id = str(uuid.uuid4())[:8]

        set_correlation_id(cid)
        request_meta_var.set({
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
        })

        response = await call_next(request)

        response.headers[CORRELATION_HEADER] = cid
        response.headers[REQUEST_ID_HEADER] = request_id

        correlation_id_var.set(None)
        request_meta_var.set({})

        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """Measures request processing time, records percentiles, and logs slow requests."""

    SLOW_REQUEST_THRESHOLD_MS = 1000

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

        response.headers[TIMING_HEADER] = str(elapsed_ms)
        telemetry.record_request(response.status_code, elapsed_ms)
        audit_log_buffer.append(
            event=f"{request.method} {request.url.path}",
            correlation_id=correlation_id_var.get(),
            status_code=response.status_code,
            latency_ms=elapsed_ms,
        )

        if elapsed_ms > self.SLOW_REQUEST_THRESHOLD_MS:
            logger.warning(
                "slow_request",
                path=request.url.path,
                method=request.method,
                elapsed_ms=elapsed_ms,
            )

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds OWASP recommended security headers to all responses."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )

        return response
