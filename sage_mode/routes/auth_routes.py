"""Authentication routes with JWT tokens.

Provides signup, login, token refresh, and user info endpoints.
"""

import re
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy.orm import Session

from sage_mode.database import get_db
from sage_mode.models.user_model import User
from sage_mode.services.user_service import UserService
from sage_mode.security import (
    create_token_pair,
    verify_refresh_token,
    require_auth,
    AuthenticatedUser,
    TokenPair,
    limiter,
    limit_auth,
)


router = APIRouter(prefix="/auth", tags=["auth"])
user_service = UserService()


# === Request/Response Models ===


class SignupRequest(BaseModel):
    username: str
    email: str
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        if len(v) > 50:
            raise ValueError("Username must be at most 50 characters")
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Username can only contain letters, numbers, underscores, and hyphens")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", v):
            raise ValueError("Invalid email format")
        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[a-zA-Z]", v):
            raise ValueError("Password must contain at least one letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number")
        return v


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    """Response for successful authentication."""

    user: UserResponse
    tokens: TokenPair


# === Routes ===


@router.post("/signup", response_model=AuthResponse)
@limiter.limit("5/minute")
async def signup(request: Request, body: SignupRequest, db: Session = Depends(get_db)):
    """Create a new user account.

    Returns JWT tokens on successful registration.
    """
    # Check if username exists
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Check if email exists
    existing_email = db.query(User).filter(User.email == body.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = User(
        username=body.username,
        email=body.email,
        password_hash=user_service.hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate tokens
    tokens = create_token_pair(user_id=user.id, role="member")

    return AuthResponse(
        user=UserResponse(id=user.id, username=user.username, email=user.email),
        tokens=tokens,
    )


@router.post("/login", response_model=AuthResponse)
@limiter.limit("5/minute")
async def login(request: Request, body: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate and receive JWT tokens.

    Returns access and refresh tokens on successful login.
    """
    user = db.query(User).filter(User.username == body.username).first()

    if not user or not user_service.verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Generate tokens
    tokens = create_token_pair(user_id=user.id, role="member")

    return AuthResponse(
        user=UserResponse(id=user.id, username=user.username, email=user.email),
        tokens=tokens,
    )


@router.post("/refresh", response_model=TokenPair)
@limiter.limit("10/minute")
async def refresh_token(request: Request, body: RefreshRequest):
    """Get new access token using refresh token.

    Use this when access token expires.
    """
    payload = verify_refresh_token(body.refresh_token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Generate new token pair
    tokens = create_token_pair(user_id=int(payload.sub), role=payload.role)

    return tokens


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: AuthenticatedUser = Depends(require_auth),
):
    """Get current authenticated user's info.

    Requires valid access token in Authorization header.
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
    )


@router.post("/logout")
async def logout():
    """Log out the current user.

    For JWT, logout is handled client-side by discarding tokens.
    This endpoint exists for API completeness.
    """
    return {"message": "Logged out successfully. Discard your tokens."}
