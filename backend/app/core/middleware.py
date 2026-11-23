"""
Custom middleware stack for request processing.

Includes:
- Correlation ID injection and propagation
- Request timing and metrics collection
- Security headers
"""

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import (
    get_logger,
    set_correlation_id,
    correlation_id_var,
    request_meta_var,
)

logger = get_logger(__name__)

CORRELATION_HEADER = "X-Correlation-ID"
REQUEST_ID_HEADER = "X-Request-ID"
TIMING_HEADER = "X-Response-Time-Ms"


class CorrelationMiddleware(BaseHTTPMiddleware):
    """
    Injects and propagates correlation IDs for distributed tracing.

    If the client sends an X-Correlation-ID header, it is reused.
    Otherwise, a new UUID is generated per request.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Extract or generate correlation ID
        cid = request.headers.get(CORRELATION_HEADER, str(uuid.uuid4()))
        request_id = str(uuid.uuid4())[:8]

        set_correlation_id(cid)
        request_meta_var.set({
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
        })

        response = await call_next(request)

        # Propagate IDs in response headers
        response.headers[CORRELATION_HEADER] = cid
        response.headers[REQUEST_ID_HEADER] = request_id

        # Reset context
        correlation_id_var.set(None)
        request_meta_var.set({})

        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """
    Measures request processing time and logs slow requests.

    Adds X-Response-Time-Ms header to every response.
    Logs a warning for requests exceeding 1 second.
    """

    SLOW_REQUEST_THRESHOLD_MS = 1000

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

        response.headers[TIMING_HEADER] = str(elapsed_ms)

        if elapsed_ms > self.SLOW_REQUEST_THRESHOLD_MS:
            logger.warning(
                "slow_request",
                path=request.url.path,
                method=request.method,
                elapsed_ms=elapsed_ms,
            )

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security headers to all responses.

    Implements OWASP recommended security headers for defense-in-depth.
    """

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
