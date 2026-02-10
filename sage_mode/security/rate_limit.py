"""Rate limiting using slowapi.

Provides rate limiting for auth, API, and LLM endpoints.
"""

from typing import Callable

from fastapi import Request, Response
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.responses import JSONResponse

from .config import get_settings


def get_user_id_or_ip(request: Request) -> str:
    """Get rate limit key: user ID if authenticated, otherwise IP.

    This ensures authenticated users get their own rate limit bucket,
    while unauthenticated requests are limited by IP.
    """
    # Check if user was set by auth middleware
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.id}"
    return get_remote_address(request)


def create_limiter() -> Limiter:
    """Create the rate limiter instance."""
    settings = get_settings()

    if not settings.rate_limit_enabled:
        # Return a no-op limiter when disabled
        return Limiter(
            key_func=get_remote_address,
            enabled=False,
        )

    return Limiter(
        key_func=get_remote_address,
        default_limits=[settings.rate_limit_api_read],
        storage_uri=settings.redis_url,
    )


# Global limiter instance
limiter = create_limiter()


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """Custom handler for rate limit exceeded errors."""
    # Extract retry-after from the exception message
    retry_after = 60  # Default
    if hasattr(exc, "detail"):
        # Try to parse the retry time from the message
        try:
            parts = str(exc.detail).split()
            for i, part in enumerate(parts):
                if part.isdigit():
                    retry_after = int(part)
                    break
        except (ValueError, IndexError):
            pass

    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded",
            "retry_after": retry_after,
        },
        headers={"Retry-After": str(retry_after)},
    )


# Decorators for different rate limit tiers
def limit_auth(func: Callable) -> Callable:
    """Rate limit for auth endpoints (login/signup)."""
    settings = get_settings()
    return limiter.limit(settings.rate_limit_auth)(func)


def limit_api_read(func: Callable) -> Callable:
    """Rate limit for API read operations."""
    settings = get_settings()
    return limiter.limit(settings.rate_limit_api_read, key_func=get_user_id_or_ip)(func)


def limit_api_write(func: Callable) -> Callable:
    """Rate limit for API write operations."""
    settings = get_settings()
    return limiter.limit(settings.rate_limit_api_write, key_func=get_user_id_or_ip)(func)


def limit_llm(func: Callable) -> Callable:
    """Rate limit for LLM endpoints (cost control)."""
    settings = get_settings()
    return limiter.limit(settings.rate_limit_llm, key_func=get_user_id_or_ip)(func)
