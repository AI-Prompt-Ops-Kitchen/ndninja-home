"""Security and observability middleware for FastAPI.

Provides:
- Security headers on all responses
- Correlation ID tracking for request tracing
- Global error handling with structured logging
"""

import time
import uuid
from typing import Callable

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from sage_mode.log_config import correlation_id_var, get_logger

logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # XSS protection (legacy, but still useful for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Prevent caching of sensitive data
        if request.url.path.startswith("/auth") or request.url.path.startswith("/api"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"

        return response


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Add correlation ID to requests for distributed tracing.

    - Reads X-Correlation-ID header if present (from upstream services)
    - Generates a new UUID if not present
    - Adds correlation ID to response headers
    - Makes correlation ID available in contextvars for logging
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())

        # Store in context var for logging
        correlation_id_var.set(correlation_id)

        # Store in request state for access in route handlers
        request.state.correlation_id = correlation_id

        # Process request
        response = await call_next(request)

        # Add to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests with timing information.

    Logs:
    - Request method, path, and query params
    - Response status code
    - Request duration in milliseconds
    - Slow request warnings (>1 second)
    """

    SLOW_REQUEST_THRESHOLD_MS = 1000

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()

        # Skip logging for health checks
        if request.url.path == "/health":
            return await call_next(request)

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000

        log_data = {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
        }

        # Add user ID if available
        if hasattr(request.state, "user_id"):
            log_data["user_id"] = request.state.user_id

        # Add query params for non-auth routes
        if request.query_params and not request.url.path.startswith("/auth"):
            log_data["query"] = str(request.query_params)

        if duration_ms > self.SLOW_REQUEST_THRESHOLD_MS:
            logger.warning("Slow request", **log_data)
        else:
            logger.info("Request completed", **log_data)

        return response


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Global error handler that catches unhandled exceptions.

    - Logs full exception details with stack trace
    - Returns sanitized error response to client
    - Includes correlation ID in error response
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            # Get correlation ID for error tracking
            correlation_id = getattr(request.state, "correlation_id", None)

            # Log full error details
            logger.exception(
                "Unhandled exception",
                path=request.url.path,
                method=request.method,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )

            # Return sanitized error response
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "An internal error occurred. Please try again later.",
                    "correlation_id": correlation_id,
                },
            )
