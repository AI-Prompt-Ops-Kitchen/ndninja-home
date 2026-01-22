import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sage_mode.main import app
from sage_mode.database import SessionLocal, engine, Base
from sage_mode.models.user_model import User
from sage_mode.models.team_model import Team, TeamMembership
from sage_mode.models.session_model import ExecutionSession, SessionDecision
from sage_mode.models.task_model import AgentTask
from sage_mode.services.user_service import UserService
from sage_mode.services.session_service import SessionService
from datetime import datetime, timezone

client = TestClient(app)
user_service = UserService()


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables and cleanup after each test"""
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup in correct order (respect foreign keys)
    db = SessionLocal()
    db.query(AgentTask).delete()
    db.query(SessionDecision).delete()
    db.query(ExecutionSession).delete()
    db.query(TeamMembership).delete()
    db.query(Team).delete()
    db.query(User).delete()
    db.commit()
    db.close()


def create_authenticated_user(db, suffix=""):
    """Helper to create user and return session_id with mock Redis"""
    user = User(
        username=f"dashboard_user_{suffix or id(db)}",
        email=f"dashboard_{suffix or id(db)}@test.com",
        password_hash=user_service.hash_password("password")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    session_id = f"mock_session_{user.id}"
    return user, session_id


def create_team_for_user(db, user, name="Test Team", is_shared=False):
    """Helper to create a team owned by user"""
    team = Team(
        name=name,
        owner_id=user.id,
        is_shared=is_shared
    )
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


class TestDashboardRoutes:
    """Test suite for dashboard routes"""

    @patch.object(SessionService, 'get_session')
    def test_dashboard_root_endpoint(self, mock_get_session):
        """Test dashboard overview endpoint (health check + counts)"""
        db = SessionLocal()
        try:
            user, session_id = create_authenticated_user(db, "root")
            mock_get_session.return_value = user.id

            response = client.get(
                "/dashboard",
                cookies={"session_id": session_id}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["version"] == "3.0"
            assert "total_teams" in data
            assert "total_sessions" in data
            assert "total_decisions" in data
        finally:
            db.close()

    @patch.object(SessionService, 'get_session')
    def test_dashboard_get_team_stats(self, mock_get_session):
        """Test getting statistics for a team"""
        db = SessionLocal()
        try:
            user, session_id = create_authenticated_user(db, "stats")
            mock_get_session.return_value = user.id

            team = create_team_for_user(db, user, "Stats Team")

            # Create some sessions
            session1 = ExecutionSession(
                team_id=team.id,
                user_id=user.id,
                feature_name="Feature 1",
                status="active"
            )
            session2 = ExecutionSession(
                team_id=team.id,
                user_id=user.id,
                feature_name="Feature 2",
                status="completed"
            )
            db.add_all([session1, session2])
            db.commit()
            db.refresh(session1)
            db.refresh(session2)

            # Create decisions
            decision1 = SessionDecision(
                session_id=session1.id,
                decision_text="Decision 1",
                category="architecture",
                confidence="high"
            )
            decision2 = SessionDecision(
                session_id=session1.id,
                decision_text="Decision 2",
                category="performance",
                confidence="medium"
            )
            db.add_all([decision1, decision2])
            db.commit()

            response = client.get(
                f"/dashboard/teams/{team.id}/stats",
                cookies={"session_id": session_id}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["team_id"] == team.id
            assert data["team_name"] == "Stats Team"
            assert data["total_sessions"] == 2
            assert data["active_sessions"] == 1
            assert data["completed_sessions"] == 1
            assert data["total_decisions"] == 2
        finally:
            db.close()

    @patch.object(SessionService, 'get_session')
    def test_dashboard_get_recent_decisions(self, mock_get_session):
        """Test getting recent decisions for a team"""
        db = SessionLocal()
        try:
            user, session_id = create_authenticated_user(db, "decisions")
            mock_get_session.return_value = user.id

            team = create_team_for_user(db, user, "Decisions Team")

            # Create session
            exec_session = ExecutionSession(
                team_id=team.id,
                user_id=user.id,
                feature_name="Auth Feature",
                status="active"
            )
            db.add(exec_session)
            db.commit()
            db.refresh(exec_session)

            # Create decisions
            decision1 = SessionDecision(
                session_id=exec_session.id,
                decision_text="Use JWT tokens",
                category="security",
                confidence="high"
            )
            decision2 = SessionDecision(
                session_id=exec_session.id,
                decision_text="Implement OAuth2",
                category="authentication",
                confidence="medium"
            )
            db.add_all([decision1, decision2])
            db.commit()

            response = client.get(
                f"/dashboard/teams/{team.id}/decisions",
                cookies={"session_id": session_id}
            )

            assert response.status_code == 200
            decisions = response.json()
            assert len(decisions) == 2
            decision_texts = [d["decision_text"] for d in decisions]
            assert "Use JWT tokens" in decision_texts
            assert "Implement OAuth2" in decision_texts
            # Verify session_feature is included
            assert all(d["session_feature"] == "Auth Feature" for d in decisions)
        finally:
            db.close()

    @patch.object(SessionService, 'get_session')
    def test_dashboard_get_agent_status(self, mock_get_session):
        """Test getting agent task summary for a team"""
        db = SessionLocal()
        try:
            user, session_id = create_authenticated_user(db, "agents")
            mock_get_session.return_value = user.id

            team = create_team_for_user(db, user, "Agent Team")

            # Create session
            exec_session = ExecutionSession(
                team_id=team.id,
                user_id=user.id,
                feature_name="Agent Feature",
                status="active"
            )
            db.add(exec_session)
            db.commit()
            db.refresh(exec_session)

            # Create agent tasks
            task1 = AgentTask(
                session_id=exec_session.id,
                agent_role="architect",
                task_description="Design system",
                status="completed",
                duration_seconds=120
            )
            task2 = AgentTask(
                session_id=exec_session.id,
                agent_role="architect",
                task_description="Review design",
                status="pending"
            )
            task3 = AgentTask(
                session_id=exec_session.id,
                agent_role="backend",
                task_description="Implement API",
                status="failed",
                error_message="Connection error"
            )
            db.add_all([task1, task2, task3])
            db.commit()

            response = client.get(
                f"/dashboard/teams/{team.id}/agents",
                cookies={"session_id": session_id}
            )

            assert response.status_code == 200
            agents = response.json()
            assert len(agents) == 2

            # Find architect stats
            architect = next((a for a in agents if a["agent_role"] == "architect"), None)
            assert architect is not None
            assert architect["total_tasks"] == 2
            assert architect["completed_tasks"] == 1
            assert architect["pending_tasks"] == 1
            assert architect["failed_tasks"] == 0
            assert architect["avg_duration_seconds"] == 120.0

            # Find backend stats
            backend = next((a for a in agents if a["agent_role"] == "backend"), None)
            assert backend is not None
            assert backend["total_tasks"] == 1
            assert backend["failed_tasks"] == 1
        finally:
            db.close()

    def test_dashboard_unauthorized(self):
        """Test that accessing dashboard without auth fails"""
        response = client.get("/dashboard")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    @patch.object(SessionService, 'get_session')
    def test_dashboard_invalid_session(self, mock_get_session):
        """Test that invalid session returns 401"""
        mock_get_session.return_value = None

        response = client.get(
            "/dashboard",
            cookies={"session_id": "invalid_session"}
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    @patch.object(SessionService, 'get_session')
    def test_dashboard_invalid_team(self, mock_get_session):
        """Test that accessing a team without access fails"""
        db = SessionLocal()
        try:
            # Create user without team access
            user, session_id = create_authenticated_user(db, "no_access")
            mock_get_session.return_value = user.id

            # Create another user who owns the team
            other_user = User(
                username="team_owner_dashboard",
                email="team_owner_dashboard@test.com",
                password_hash=user_service.hash_password("password")
            )
            db.add(other_user)
            db.commit()

            team = create_team_for_user(db, other_user, "Other's Team")

            response = client.get(
                f"/dashboard/teams/{team.id}/stats",
                cookies={"session_id": session_id}
            )

            assert response.status_code == 403
            assert "access" in response.json()["detail"].lower()
        finally:
            db.close()

    @patch.object(SessionService, 'get_session')
    def test_dashboard_team_not_found(self, mock_get_session):
        """Test that accessing non-existent team returns 403 (access denied)"""
        db = SessionLocal()
        try:
            user, session_id = create_authenticated_user(db, "not_found")
            mock_get_session.return_value = user.id

            response = client.get(
                "/dashboard/teams/99999/stats",
                cookies={"session_id": session_id}
            )

            # Returns 403 because user_has_team_access returns False for non-existent teams
            assert response.status_code == 403
        finally:
            db.close()

    @patch.object(SessionService, 'get_session')
    def test_dashboard_team_member_access(self, mock_get_session):
        """Test that team members (not just owners) can access dashboard"""
        db = SessionLocal()
        try:
            # Create team owner
            owner = User(
                username="owner_dashboard_test",
                email="owner_dashboard@test.com",
                password_hash=user_service.hash_password("password")
            )
            db.add(owner)
            db.commit()

            team = create_team_for_user(db, owner, "Shared Dashboard Team", is_shared=True)

            # Create member user
            member, session_id = create_authenticated_user(db, "member")
            mock_get_session.return_value = member.id

            # Add member to team
            membership = TeamMembership(
                team_id=team.id,
                user_id=member.id,
                role="member"
            )
            db.add(membership)
            db.commit()

            response = client.get(
                f"/dashboard/teams/{team.id}/stats",
                cookies={"session_id": session_id}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["team_id"] == team.id
        finally:
            db.close()

    @patch.object(SessionService, 'get_session')
    def test_dashboard_empty_decisions(self, mock_get_session):
        """Test getting decisions for team with no sessions returns empty list"""
        db = SessionLocal()
        try:
            user, session_id = create_authenticated_user(db, "empty")
            mock_get_session.return_value = user.id

            team = create_team_for_user(db, user, "Empty Team")

            response = client.get(
                f"/dashboard/teams/{team.id}/decisions",
                cookies={"session_id": session_id}
            )

            assert response.status_code == 200
            decisions = response.json()
            assert decisions == []
        finally:
            db.close()

    @patch.object(SessionService, 'get_session')
    def test_dashboard_empty_agents(self, mock_get_session):
        """Test getting agent status for team with no tasks returns empty list"""
        db = SessionLocal()
        try:
            user, session_id = create_authenticated_user(db, "empty_agents")
            mock_get_session.return_value = user.id

            team = create_team_for_user(db, user, "Empty Agent Team")

            response = client.get(
                f"/dashboard/teams/{team.id}/agents",
                cookies={"session_id": session_id}
            )

            assert response.status_code == 200
            agents = response.json()
            assert agents == []
        finally:
            db.close()

    @patch.object(SessionService, 'get_session')
    def test_dashboard_overview_with_data(self, mock_get_session):
        """Test dashboard overview reflects accurate counts"""
        db = SessionLocal()
        try:
            user, session_id = create_authenticated_user(db, "overview")
            mock_get_session.return_value = user.id

            # Create 2 teams
            team1 = create_team_for_user(db, user, "Team 1")
            team2 = create_team_for_user(db, user, "Team 2")

            # Create sessions
            session1 = ExecutionSession(
                team_id=team1.id,
                user_id=user.id,
                feature_name="Feature 1",
                status="active"
            )
            session2 = ExecutionSession(
                team_id=team2.id,
                user_id=user.id,
                feature_name="Feature 2",
                status="completed"
            )
            db.add_all([session1, session2])
            db.commit()
            db.refresh(session1)

            # Create decision
            decision = SessionDecision(
                session_id=session1.id,
                decision_text="Test decision",
                category="test",
                confidence="high"
            )
            db.add(decision)
            db.commit()

            response = client.get(
                "/dashboard",
                cookies={"session_id": session_id}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total_teams"] == 2
            assert data["total_sessions"] == 2
            assert data["total_decisions"] == 1
        finally:
            db.close()
