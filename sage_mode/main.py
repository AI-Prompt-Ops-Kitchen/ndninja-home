"""Sage Mode FastAPI application.

Production-ready setup with security middleware stack,
structured logging, and observability.
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from sage_mode.database import SessionLocal
from sage_mode.log_config import configure_logging, get_logger
from sage_mode.routes.auth_routes import router as auth_router
from sage_mode.routes.team_routes import router as team_router
from sage_mode.routes.session_routes import router as session_router
from sage_mode.routes.dashboard_routes import router as dashboard_router
from sage_mode.routes.websocket_routes import router as websocket_router
from sage_mode.security import (
    SecurityHeadersMiddleware,
    CorrelationIdMiddleware,
    RequestLoggingMiddleware,
    ErrorHandlerMiddleware,
    get_settings,
    limiter,
    rate_limit_exceeded_handler,
)


logger = get_logger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    # Configure structured logging
    json_logs = os.getenv("LOG_FORMAT", "json") == "json"
    log_level = os.getenv("LOG_LEVEL", "INFO")
    configure_logging(json_format=json_logs, log_level=log_level)

    app = FastAPI(
        title="Sage Mode",
        description="Development Team Simulator",
        version="3.0",
    )

    # === Middleware Stack (order matters: last added = first executed) ===
    # Request flow: ErrorHandler -> CorrelationId -> RequestLogging -> CORS -> SecurityHeaders -> Route

    # 1. Security Headers (runs last in request, adds headers to response)
    app.add_middleware(SecurityHeadersMiddleware)

    # 2. CORS (handles preflight and adds CORS headers)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 3. Request Logging (logs all requests with timing)
    app.add_middleware(RequestLoggingMiddleware)

    # 4. Correlation ID (adds tracing ID to requests)
    app.add_middleware(CorrelationIdMiddleware)

    # 5. Error Handler (catches unhandled exceptions, runs first)
    app.add_middleware(ErrorHandlerMiddleware)

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
        """Health check endpoint with DB connectivity (no auth required)."""
        health_status = {
            "status": "healthy",
            "version": "3.0",
            "checks": {},
        }

        # Check database connectivity
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
            health_status["checks"]["database"] = "ok"
        except Exception as e:
            health_status["status"] = "degraded"
            health_status["checks"]["database"] = f"error: {type(e).__name__}"
            logger.warning("Health check: database unavailable", error=str(e))

        return health_status

    @app.on_event("startup")
    async def startup_event():
        """Log application startup."""
        logger.info(
            "Sage Mode starting",
            version="3.0",
            log_format="json" if json_logs else "console",
            log_level=log_level,
        )

    @app.on_event("shutdown")
    async def shutdown_event():
        """Log application shutdown."""
        logger.info("Sage Mode shutting down")

    return app


# Create the application instance
app = create_app()
