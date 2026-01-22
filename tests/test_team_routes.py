"""Tests for team management routes with JWT authentication."""

import os
import pytest
from fastapi.testclient import TestClient

# Set test environment variables before importing
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")

from sage_mode.main import app
from sage_mode.database import SessionLocal, engine, Base
from sage_mode.models.user_model import User
from sage_mode.models.team_model import Team, TeamMembership
from sage_mode.services.user_service import UserService
from sage_mode.security import create_token_pair

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


def create_authenticated_user(db, suffix=""):
    """Helper to create user and return JWT token"""
    user = User(
        username=f"testuser_{suffix or id(db)}",
        email=f"test_{suffix or id(db)}@test.com",
        password_hash=user_service.hash_password("password")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    # Create JWT token for the user
    tokens = create_token_pair(user_id=user.id, role="member")
    return user, tokens.access_token


def auth_header(token: str) -> dict:
    """Helper to create authorization header"""
    return {"Authorization": f"Bearer {token}"}


class TestTeamRoutes:
    """Test suite for team management routes"""

    def test_create_team(self):
        """Test creating a team successfully"""
        db = SessionLocal()
        try:
            user, token = create_authenticated_user(db, "create")

            response = client.post(
                "/teams",
                json={"name": "Test Team", "description": "A test team"},
                headers=auth_header(token)
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Test Team"
            assert data["owner_id"] == user.id
            assert data["is_shared"] == False
        finally:
            db.close()

    def test_create_team_unauthenticated(self):
        """Test that creating a team without auth fails"""
        response = client.post(
            "/teams",
            json={"name": "Test Team"}
        )

        assert response.status_code == 401

    def test_list_teams(self):
        """Test listing user's teams (owned + member of)"""
        db = SessionLocal()
        try:
            user, token = create_authenticated_user(db, "list")

            # Create a team owned by user
            owned_team = Team(name="Owned Team", owner_id=user.id, is_shared=False)
            db.add(owned_team)
            db.commit()

            # Create another user and their team
            other_user = User(
                username="other_user_list",
                email="other_list@test.com",
                password_hash=user_service.hash_password("password")
            )
            db.add(other_user)
            db.commit()

            shared_team = Team(name="Shared Team", owner_id=other_user.id, is_shared=True)
            db.add(shared_team)
            db.commit()

            # Add user as member of shared team
            membership = TeamMembership(team_id=shared_team.id, user_id=user.id, role="member")
            db.add(membership)
            db.commit()

            response = client.get(
                "/teams",
                headers=auth_header(token)
            )

            assert response.status_code == 200
            teams = response.json()
            assert len(teams) == 2
            team_names = [t["name"] for t in teams]
            assert "Owned Team" in team_names
            assert "Shared Team" in team_names
        finally:
            db.close()

    def test_get_team(self):
        """Test getting a specific team"""
        db = SessionLocal()
        try:
            user, token = create_authenticated_user(db, "get")

            team = Team(name="My Team", owner_id=user.id, description="Test description")
            db.add(team)
            db.commit()
            db.refresh(team)

            response = client.get(
                f"/teams/{team.id}",
                headers=auth_header(token)
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "My Team"
            assert data["owner_id"] == user.id
        finally:
            db.close()

    def test_get_team_not_found(self):
        """Test getting a non-existent team returns 404"""
        db = SessionLocal()
        try:
            user, token = create_authenticated_user(db, "notfound")

            response = client.get(
                "/teams/99999",
                headers=auth_header(token)
            )

            assert response.status_code == 404
        finally:
            db.close()

    def test_update_team(self):
        """Test updating team name and description"""
        db = SessionLocal()
        try:
            user, token = create_authenticated_user(db, "update")

            team = Team(name="Original Name", owner_id=user.id, is_shared=False)
            db.add(team)
            db.commit()
            db.refresh(team)

            response = client.put(
                f"/teams/{team.id}",
                json={"name": "Updated Name", "description": "New description", "is_shared": True},
                headers=auth_header(token)
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Name"
            assert data["is_shared"] == True
        finally:
            db.close()

    def test_update_team_not_owner(self):
        """Test that non-owners cannot update team"""
        db = SessionLocal()
        try:
            # Create owner
            owner = User(
                username="owner_update",
                email="owner_update@test.com",
                password_hash=user_service.hash_password("password")
            )
            db.add(owner)
            db.commit()

            team = Team(name="Owner's Team", owner_id=owner.id)
            db.add(team)
            db.commit()
            db.refresh(team)

            # Create another user
            user, token = create_authenticated_user(db, "non_owner_update")

            response = client.put(
                f"/teams/{team.id}",
                json={"name": "Hacked Name"},
                headers=auth_header(token)
            )

            assert response.status_code == 403
        finally:
            db.close()

    def test_delete_team(self):
        """Test deleting an owned team"""
        db = SessionLocal()
        try:
            user, token = create_authenticated_user(db, "delete")

            team = Team(name="To Delete", owner_id=user.id)
            db.add(team)
            db.commit()
            db.refresh(team)
            team_id = team.id

            response = client.delete(
                f"/teams/{team_id}",
                headers=auth_header(token)
            )

            assert response.status_code == 200

            # Verify team is deleted
            deleted_team = db.query(Team).filter(Team.id == team_id).first()
            assert deleted_team is None
        finally:
            db.close()

    def test_delete_team_not_owner(self):
        """Test that non-owners cannot delete team"""
        db = SessionLocal()
        try:
            # Create owner
            owner = User(
                username="owner_delete",
                email="owner_delete@test.com",
                password_hash=user_service.hash_password("password")
            )
            db.add(owner)
            db.commit()

            team = Team(name="Owner's Team", owner_id=owner.id)
            db.add(team)
            db.commit()
            db.refresh(team)

            # Create another user trying to delete
            user, token = create_authenticated_user(db, "non_owner_delete")

            response = client.delete(
                f"/teams/{team.id}",
                headers=auth_header(token)
            )

            assert response.status_code == 403
        finally:
            db.close()

    def test_invite_to_team(self):
        """Test inviting another user to a shared team"""
        db = SessionLocal()
        try:
            owner, token = create_authenticated_user(db, "owner_invite")

            # Create a shared team
            team = Team(name="Shared Team", owner_id=owner.id, is_shared=True)
            db.add(team)
            db.commit()
            db.refresh(team)

            # Create user to invite
            invitee = User(
                username="invitee",
                email="invitee@test.com",
                password_hash=user_service.hash_password("password")
            )
            db.add(invitee)
            db.commit()
            db.refresh(invitee)

            response = client.post(
                f"/teams/{team.id}/invite",
                json={"user_id": invitee.id},
                headers=auth_header(token)
            )

            assert response.status_code == 200

            # Verify membership was created
            membership = db.query(TeamMembership).filter(
                TeamMembership.team_id == team.id,
                TeamMembership.user_id == invitee.id
            ).first()
            assert membership is not None
            assert membership.role == "member"
        finally:
            db.close()

    def test_invite_to_non_shared_team_fails(self):
        """Test that inviting to a non-shared team fails"""
        db = SessionLocal()
        try:
            owner, token = create_authenticated_user(db, "owner_non_shared")

            # Create a non-shared team
            team = Team(name="Private Team", owner_id=owner.id, is_shared=False)
            db.add(team)
            db.commit()
            db.refresh(team)

            # Create user to invite
            invitee = User(
                username="invitee_non_shared",
                email="invitee_ns@test.com",
                password_hash=user_service.hash_password("password")
            )
            db.add(invitee)
            db.commit()
            db.refresh(invitee)

            response = client.post(
                f"/teams/{team.id}/invite",
                json={"user_id": invitee.id},
                headers=auth_header(token)
            )

            assert response.status_code == 400
            assert "not shared" in response.json()["detail"].lower()
        finally:
            db.close()

    def test_invite_not_owner_fails(self):
        """Test that non-owners cannot invite users"""
        db = SessionLocal()
        try:
            # Create owner and shared team
            owner = User(
                username="owner_invite_fail",
                email="owner_inv_fail@test.com",
                password_hash=user_service.hash_password("password")
            )
            db.add(owner)
            db.commit()

            team = Team(name="Shared Team", owner_id=owner.id, is_shared=True)
            db.add(team)
            db.commit()
            db.refresh(team)

            # Create non-owner user
            non_owner, token = create_authenticated_user(db, "non_owner_invite")

            # Add non-owner as member (but not owner)
            membership = TeamMembership(team_id=team.id, user_id=non_owner.id, role="member")
            db.add(membership)
            db.commit()

            # Create user to invite
            invitee = User(
                username="invitee_fail",
                email="invitee_fail@test.com",
                password_hash=user_service.hash_password("password")
            )
            db.add(invitee)
            db.commit()
            db.refresh(invitee)

            response = client.post(
                f"/teams/{team.id}/invite",
                json={"user_id": invitee.id},
                headers=auth_header(token)
            )

            assert response.status_code == 403
        finally:
            db.close()

    def test_invalid_token(self):
        """Test that invalid token returns 401"""
        response = client.get(
            "/teams",
            headers=auth_header("invalid-token")
        )

        assert response.status_code == 401
