"""Sage Mode FastAPI application.

Production-ready setup with security middleware stack.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from sage_mode.routes.auth_routes import router as auth_router
from sage_mode.routes.team_routes import router as team_router
from sage_mode.routes.session_routes import router as session_router
from sage_mode.routes.dashboard_routes import router as dashboard_router
from sage_mode.routes.websocket_routes import router as websocket_router
from sage_mode.security import (
    SecurityHeadersMiddleware,
    get_settings,
    limiter,
    rate_limit_exceeded_handler,
)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Sage Mode",
        description="Development Team Simulator",
        version="3.0",
    )

    # === Middleware Stack (order matters: last added = first executed) ===

    # 1. Security Headers (runs last, adds headers to response)
    app.add_middleware(SecurityHeadersMiddleware)

    # 2. CORS (handles preflight and adds CORS headers)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # === Rate Limiting ===
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    # === Routes ===
    app.include_router(auth_router)
    app.include_router(team_router)
    app.include_router(session_router)
    app.include_router(dashboard_router)
    app.include_router(websocket_router)

    @app.get("/health")
    def health_check():
        """Health check endpoint (no auth required)."""
        return {"status": "healthy", "version": "3.0"}

    return app


# Create the application instance
app = create_app()
