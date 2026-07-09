"""
Structured JSON request/response logging middleware.

Logs every request with:
  - request_id (propagated from app state or generated)
  - method, path, status_code
  - latency_ms
  - client IP
  - user_agent

Output is newline-delimited JSON, compatible with log aggregation tools
(Loki, Datadog, CloudWatch, etc.).
"""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("amd_router.access")


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Emit one structured JSON log record per HTTP request/response cycle."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        # Attach request_id to the request state so route handlers can read it
        request.state.request_id = request_id

        # Process the request
        response: Response = await call_next(request)

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        logger.info(
            "request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query": str(request.url.query),
                "status_code": response.status_code,
                "latency_ms": latency_ms,
                "client_host": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", ""),
            },
        )

        # Propagate request_id in response headers for client-side tracing
        response.headers["X-Request-ID"] = request_id
        return response
