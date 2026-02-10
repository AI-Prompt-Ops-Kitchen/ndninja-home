"""Tests for security module - JWT authentication, rate limiting, and middleware."""

import os
import pytest
from fastapi.testclient import TestClient

# Set test environment variables before importing security module
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["RATE_LIMIT_ENABLED"] = "false"

from sage_mode.main import app
from sage_mode.database import SessionLocal, engine, Base
from sage_mode.models.user_model import User
from sage_mode.models.team_model import Team, TeamMembership
from sage_mode.services.user_service import UserService
from sage_mode.security import (
    create_access_token,
    create_refresh_token,
    create_token_pair,
    verify_access_token,
    verify_refresh_token,
)

client = TestClient(app)
user_service = UserService()


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables and cleanup after each test"""
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup
    db = SessionLocal()
    db.query(TeamMembership).delete()
    db.query(Team).delete()
    db.query(User).delete()
    db.commit()
    db.close()


def create_test_user(db, username="testuser", email="test@test.com"):
    """Helper to create a test user"""
    user = User(
        username=username,
        email=email,
        password_hash=user_service.hash_password("Password123")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_auth_header(token: str) -> dict:
    """Helper to create authorization header"""
    return {"Authorization": f"Bearer {token}"}


class TestJWTTokens:
    """Test JWT token creation and validation"""

    def test_create_access_token(self):
        """Test access token creation"""
        token = create_access_token(user_id=1, role="member")
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self):
        """Test refresh token creation"""
        token = create_refresh_token(user_id=1)
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_token_pair(self):
        """Test token pair creation"""
        tokens = create_token_pair(user_id=1, role="member")
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
        assert tokens.token_type == "bearer"

    def test_verify_access_token_valid(self):
        """Test valid access token verification"""
        token = create_access_token(user_id=42, role="admin")
        payload = verify_access_token(token)

        assert payload is not None
        assert payload.sub == "42"
        assert payload.role == "admin"
        assert payload.type == "access"

    def test_verify_access_token_invalid(self):
        """Test invalid access token returns None"""
        payload = verify_access_token("invalid-token")
        assert payload is None

    def test_verify_refresh_token_valid(self):
        """Test valid refresh token verification"""
        token = create_refresh_token(user_id=42)
        payload = verify_refresh_token(token)

        assert payload is not None
        assert payload.sub == "42"
        assert payload.type == "refresh"

    def test_access_token_cannot_be_used_as_refresh(self):
        """Test that access tokens cannot be used for refresh"""
        token = create_access_token(user_id=1, role="member")
        payload = verify_refresh_token(token)
        assert payload is None

    def test_refresh_token_cannot_be_used_as_access(self):
        """Test that refresh tokens cannot be used for access"""
        token = create_refresh_token(user_id=1)
        payload = verify_access_token(token)
        assert payload is None


class TestAuthRoutes:
    """Test authentication routes"""

    def test_signup_success(self):
        """Test successful user signup"""
        response = client.post(
            "/auth/signup",
            json={
                "username": "newuser",
                "email": "new@test.com",
                "password": "Password123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "tokens" in data
        assert data["user"]["username"] == "newuser"
        assert data["tokens"]["access_token"] is not None
        assert data["tokens"]["refresh_token"] is not None

    def test_signup_duplicate_username(self):
        """Test signup with existing username fails"""
        db = SessionLocal()
        try:
            create_test_user(db, "existing", "existing@test.com")

            response = client.post(
                "/auth/signup",
                json={
                    "username": "existing",
                    "email": "new@test.com",
                    "password": "Password123"
                }
            )

            assert response.status_code == 400
            assert "username" in response.json()["detail"].lower()
        finally:
            db.close()

    def test_signup_duplicate_email(self):
        """Test signup with existing email fails"""
        db = SessionLocal()
        try:
            create_test_user(db, "user1", "duplicate@test.com")

            response = client.post(
                "/auth/signup",
                json={
                    "username": "newuser",
                    "email": "duplicate@test.com",
                    "password": "Password123"
                }
            )

            assert response.status_code == 400
            assert "email" in response.json()["detail"].lower()
        finally:
            db.close()

    def test_signup_weak_password(self):
        """Test signup with weak password fails"""
        response = client.post(
            "/auth/signup",
            json={
                "username": "newuser",
                "email": "new@test.com",
                "password": "short"  # Less than 8 chars
            }
        )

        assert response.status_code == 422  # Validation error

    def test_signup_password_no_number(self):
        """Test signup with password without number fails"""
        response = client.post(
            "/auth/signup",
            json={
                "username": "newuser",
                "email": "new@test.com",
                "password": "PasswordOnly"  # No numbers
            }
        )

        assert response.status_code == 422

    def test_login_success(self):
        """Test successful login"""
        db = SessionLocal()
        try:
            create_test_user(db, "loginuser", "login@test.com")

            response = client.post(
                "/auth/login",
                json={
                    "username": "loginuser",
                    "password": "Password123"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "user" in data
            assert "tokens" in data
            assert data["user"]["username"] == "loginuser"
        finally:
            db.close()

    def test_login_wrong_password(self):
        """Test login with wrong password fails"""
        db = SessionLocal()
        try:
            create_test_user(db, "loginuser2", "login2@test.com")

            response = client.post(
                "/auth/login",
                json={
                    "username": "loginuser2",
                    "password": "WrongPassword123"
                }
            )

            assert response.status_code == 401
        finally:
            db.close()

    def test_login_nonexistent_user(self):
        """Test login with nonexistent user fails"""
        response = client.post(
            "/auth/login",
            json={
                "username": "doesnotexist",
                "password": "Password123"
            }
        )

        assert response.status_code == 401

    def test_refresh_token_success(self):
        """Test token refresh with valid refresh token"""
        db = SessionLocal()
        try:
            user = create_test_user(db, "refreshuser", "refresh@test.com")
            tokens = create_token_pair(user_id=user.id, role="member")

            response = client.post(
                "/auth/refresh",
                json={"refresh_token": tokens.refresh_token}
            )

            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
        finally:
            db.close()

    def test_refresh_token_invalid(self):
        """Test token refresh with invalid token fails"""
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid-token"}
        )

        assert response.status_code == 401

    def test_get_current_user(self):
        """Test getting current user info with valid token"""
        db = SessionLocal()
        try:
            user = create_test_user(db, "meuser", "me@test.com")
            tokens = create_token_pair(user_id=user.id, role="member")

            response = client.get(
                "/auth/me",
                headers=get_auth_header(tokens.access_token)
            )

            assert response.status_code == 200
            data = response.json()
            assert data["username"] == "meuser"
            assert data["email"] == "me@test.com"
        finally:
            db.close()

    def test_get_current_user_no_token(self):
        """Test getting current user without token fails"""
        response = client.get("/auth/me")
        assert response.status_code == 401


class TestProtectedRoutes:
    """Test protected routes require valid authentication"""

    def test_teams_list_requires_auth(self):
        """Test that listing teams requires authentication"""
        response = client.get("/teams")
        assert response.status_code == 401

    def test_teams_list_with_valid_token(self):
        """Test listing teams with valid token succeeds"""
        db = SessionLocal()
        try:
            user = create_test_user(db, "teamuser", "team@test.com")
            tokens = create_token_pair(user_id=user.id, role="member")

            response = client.get(
                "/teams",
                headers=get_auth_header(tokens.access_token)
            )

            assert response.status_code == 200
        finally:
            db.close()

    def test_teams_list_with_invalid_token(self):
        """Test listing teams with invalid token fails"""
        response = client.get(
            "/teams",
            headers=get_auth_header("invalid-token")
        )
        assert response.status_code == 401

    def test_sessions_list_requires_auth(self):
        """Test that listing sessions requires authentication"""
        response = client.get("/sessions")
        assert response.status_code == 401

    def test_dashboard_requires_auth(self):
        """Test that dashboard requires authentication"""
        response = client.get("/dashboard")
        assert response.status_code == 401


class TestSecurityHeaders:
    """Test security headers middleware"""

    def test_security_headers_present(self):
        """Test that security headers are added to responses"""
        response = client.get("/health")

        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    def test_cache_control_on_auth_routes(self):
        """Test that auth routes have cache control headers"""
        response = client.post(
            "/auth/login",
            json={"username": "test", "password": "test"}
        )

        assert response.headers.get("Cache-Control") == "no-store, no-cache, must-revalidate"
        assert response.headers.get("Pragma") == "no-cache"


class TestHealthEndpoint:
    """Test health endpoint (no auth required)"""

    def test_health_check_no_auth(self):
        """Test health check works without authentication"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "3.0"
