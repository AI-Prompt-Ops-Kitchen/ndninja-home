"""Security module for Sage Mode.

Provides authentication, authorization, and security middleware.
"""

from .config import SecuritySettings, get_settings, reset_settings
from .jwt import (
    TokenPayload,
    TokenPair,
    create_access_token,
    create_refresh_token,
    create_token_pair,
    verify_access_token,
    verify_refresh_token,
)
from .dependencies import (
    AuthenticatedUser,
    get_current_user,
    get_optional_user,
    require_auth,
    require_admin,
    require_team_member,
)
from .middleware import (
    SecurityHeadersMiddleware,
    CorrelationIdMiddleware,
    RequestLoggingMiddleware,
    ErrorHandlerMiddleware,
)
from .rate_limit import (
    limiter,
    rate_limit_exceeded_handler,
    limit_auth,
    limit_api_read,
    limit_api_write,
    limit_llm,
)


__all__ = [
    # Config
    "SecuritySettings",
    "get_settings",
    "reset_settings",
    # JWT
    "TokenPayload",
    "TokenPair",
    "create_access_token",
    "create_refresh_token",
    "create_token_pair",
    "verify_access_token",
    "verify_refresh_token",
    # Dependencies
    "AuthenticatedUser",
    "get_current_user",
    "get_optional_user",
    "require_auth",
    "require_admin",
    "require_team_member",
    # Middleware
    "SecurityHeadersMiddleware",
    "CorrelationIdMiddleware",
    "RequestLoggingMiddleware",
    "ErrorHandlerMiddleware",
    # Rate Limiting
    "limiter",
    "rate_limit_exceeded_handler",
    "limit_auth",
    "limit_api_read",
    "limit_api_write",
    "limit_llm",
]
