"""JWT token creation and validation.

Handles access tokens (short-lived) and refresh tokens (long-lived).
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from pydantic import BaseModel

from .config import get_settings


class TokenPayload(BaseModel):
    """Decoded token payload."""

    sub: str  # User ID
    team_id: Optional[int] = None
    role: str = "member"
    exp: datetime
    type: str  # "access" or "refresh"


class TokenPair(BaseModel):
    """Access and refresh token pair returned on login."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


def create_access_token(
    user_id: int,
    team_id: Optional[int] = None,
    role: str = "member",
) -> str:
    """Create a short-lived access token.

    Args:
        user_id: The user's ID
        team_id: Optional team ID
        role: User role (admin/member)

    Returns:
        Encoded JWT string
    """
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    payload = {
        "sub": str(user_id),
        "team_id": team_id,
        "role": role,
        "exp": expire,
        "type": "access",
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(user_id: int) -> str:
    """Create a long-lived refresh token.

    Args:
        user_id: The user's ID

    Returns:
        Encoded JWT string
    """
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )

    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh",
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_token_pair(
    user_id: int,
    team_id: Optional[int] = None,
    role: str = "member",
) -> TokenPair:
    """Create both access and refresh tokens.

    Args:
        user_id: The user's ID
        team_id: Optional team ID
        role: User role

    Returns:
        TokenPair with both tokens
    """
    return TokenPair(
        access_token=create_access_token(user_id, team_id, role),
        refresh_token=create_refresh_token(user_id),
    )


def verify_token(token: str, token_type: str = "access") -> Optional[TokenPayload]:
    """Verify and decode a JWT token.

    Args:
        token: The JWT string
        token_type: Expected type ("access" or "refresh")

    Returns:
        Decoded TokenPayload or None if invalid
    """
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        # Verify token type matches expected
        if payload.get("type") != token_type:
            return None

        return TokenPayload(
            sub=payload["sub"],
            team_id=payload.get("team_id"),
            role=payload.get("role", "member"),
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            type=payload["type"],
        )

    except JWTError:
        return None


def verify_access_token(token: str) -> Optional[TokenPayload]:
    """Verify an access token."""
    return verify_token(token, "access")


def verify_refresh_token(token: str) -> Optional[TokenPayload]:
    """Verify a refresh token."""
    return verify_token(token, "refresh")
