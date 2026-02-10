"""FastAPI authentication dependencies.

Provides dependency injection for route protection:
- require_auth: Any authenticated user
- require_admin: Admin role required
- require_team_member: Must belong to specified team
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from sage_mode.database import get_db
from sage_mode.models.user_model import User
from .jwt import verify_access_token, TokenPayload


# HTTP Bearer token extractor
bearer_scheme = HTTPBearer(auto_error=False)


class AuthenticatedUser:
    """Wrapper for authenticated user with token claims."""

    def __init__(self, user: User, token: TokenPayload):
        self.user = user
        self.token = token
        self.id = user.id
        self.username = user.username
        self.email = user.email
        self.team_id = token.team_id
        self.role = token.role


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Optional[AuthenticatedUser]:
    """Extract and validate user from JWT token.

    Returns None if no token or invalid token.
    Use require_auth for routes that need authentication.
    """
    if not credentials:
        return None

    token_payload = verify_access_token(credentials.credentials)
    if not token_payload:
        return None

    user = db.query(User).filter(User.id == int(token_payload.sub)).first()
    if not user:
        return None

    return AuthenticatedUser(user, token_payload)


async def require_auth(
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user),
) -> AuthenticatedUser:
    """Require authenticated user.

    Raises 401 if not authenticated.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


async def require_admin(
    current_user: AuthenticatedUser = Depends(require_auth),
) -> AuthenticatedUser:
    """Require admin role.

    Raises 403 if not admin.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def require_team_member(team_id: int):
    """Factory for team membership requirement.

    Usage:
        @router.get("/teams/{team_id}/data")
        def get_team_data(
            team_id: int,
            user: AuthenticatedUser = Depends(require_team_member(team_id))
        ):
            ...
    """

    async def check_team_membership(
        current_user: AuthenticatedUser = Depends(require_auth),
    ) -> AuthenticatedUser:
        if current_user.team_id != team_id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this team",
            )
        return current_user

    return check_team_membership


# Convenience alias
get_optional_user = get_current_user
