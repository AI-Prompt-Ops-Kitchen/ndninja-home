"""Security configuration using Pydantic Settings.

Loads configuration from environment variables with sensible defaults.
Required variables will cause startup failure if missing.
"""

import json
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class SecuritySettings(BaseSettings):
    """Security configuration loaded from environment."""

    # === JWT Configuration (required) ===
    jwt_secret_key: str  # No default - must be set
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # === CORS Configuration ===
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # === Rate Limiting ===
    rate_limit_enabled: bool = True
    rate_limit_auth: str = "5/minute"
    rate_limit_api_read: str = "60/minute"
    rate_limit_api_write: str = "30/minute"
    rate_limit_llm: str = "10/minute"

    # === Database ===
    database_url: str = "postgresql://localhost/sage_mode"

    # === Redis ===
    redis_url: str = "redis://localhost:6379"

    # === LLM (optional) ===
    anthropic_api_key: str | None = None

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from JSON string or list."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # Treat as comma-separated list
                return [origin.strip() for origin in v.split(",")]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Singleton instance - import this in other modules
_settings: SecuritySettings | None = None


def get_settings() -> SecuritySettings:
    """Get the security settings singleton.

    Raises clear error if JWT_SECRET_KEY is not set.
    """
    global _settings
    if _settings is None:
        try:
            _settings = SecuritySettings()
        except Exception as e:
            if "jwt_secret_key" in str(e).lower():
                raise ValueError(
                    "JWT_SECRET_KEY environment variable is required. "
                    "Generate one with: openssl rand -hex 32"
                ) from e
            raise
    return _settings


def reset_settings() -> None:
    """Reset settings singleton (useful for testing)."""
    global _settings
    _settings = None
