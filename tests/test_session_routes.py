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
from datetime import datetime, timedelta, timezone

client = TestClient(app)
user_service = UserService()


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables and cleanup after each test"""
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup
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
        username=f"testuser_{suffix or id(db)}",
        email=f"test_{suffix or id(db)}@test.com",
        password_hash=user_service.hash_password("password")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    # Return user and a mock session_id (will be patched in tests)
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


class TestSessionRoutes:
    """Test suite for execution session routes"""

    @patch.object(SessionService, 'get_session')
    def test_start_session(self, mock_get_session):
        """Test starting an execution session"""
        db = SessionLocal()
        try:
            user, session_id = create_authenticated_user(db, "start_session")
            mock_get_session.return_value = user.id

            team = create_team_for_user(db, user, "Dev Team")

            response = client.post(
                "/sessions",
                json={"team_id": team.id, "feature_name": "User Authentication"},
                cookies={"session_id": session_id}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["team_id"] == team.id
            assert data["user_id"] == user.id
            assert data["feature_name"] == "User Authentication"
            assert data["status"] == "active"
            assert data["started_at"] is not None
            assert data["ended_at"] is None
            assert data["duration_seconds"] is None
        finally:
            db.close()

    @patch.object(SessionService, 'get_session')
    def test_start_session_invalid_team(self, mock_get_session):
        """Test that starting a session fails if user can't access team"""
        db = SessionLocal()
        try:
            # Create user without team access
            user, session_id = create_authenticated_user(db, "no_access")
            mock_get_session.return_value = user.id

            # Create another user who owns the team
            other_user = User(
                username="team_owner",
                email="team_owner@test.com",
                password_hash=user_service.hash_password("password")
            )
            db.add(other_user)
            db.commit()

            team = create_team_for_user(db, other_user, "Other's Team")

            response = client.post(
                "/sessions",
                json={"team_id": team.id, "feature_name": "Some Feature"},
                cookies={"session_id": session_id}
            )

            assert response.status_code == 403
            assert "access" in response.json()["detail"].lower()
        finally:
            db.close()

    @patch.object(SessionService, 'get_session')
    def test_start_session_as_member(self, mock_get_session):
        """Test that team members (not just owners) can start sessions"""
        db = SessionLocal()
        try:
            # Create team owner
            owner = User(
                username="owner_member_test",
                email="owner_member@test.com",
                password_hash=user_service.hash_password("password")
            )
            db.add(owner)
            db.commit()

            team = create_team_for_user(db, owner, "Shared Team", is_shared=True)

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

            response = client.post(
                "/sessions",
                json={"team_id": team.id, "feature_name": "Member Feature"},
                cookies={"session_id": session_id}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["team_id"] == team.id
            assert data["user_id"] == member.id
        finally:
            db.close()

    @patch.object(SessionService, 'get_session')
    def test_list_sessions(self, mock_get_session):
        """Test listing user's execution sessions"""
        db = SessionLocal()
        try:
            user, session_id = create_authenticated_user(db, "list_sessions")
            mock_get_session.return_value = user.id

            team = create_team_for_user(db, user, "Dev Team")

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

            response = client.get(
                "/sessions",
                cookies={"session_id": session_id}
            )

            assert response.status_code == 200
            sessions = response.json()
            assert len(sessions) == 2
            feature_names = [s["feature_name"] for s in sessions]
            assert "Feature 1" in feature_names
            assert "Feature 2" in feature_names
        finally:
            db.close()

    @patch.object(SessionService, 'get_session')
    def test_get_session(self, mock_get_session):
        """Test getting session details"""
        db = SessionLocal()
        try:
            user, session_id = create_authenticated_user(db, "get_session")
            mock_get_session.return_value = user.id

            team = create_team_for_user(db, user)

            exec_session = ExecutionSession(
                team_id=team.id,
                user_id=user.id,
                feature_name="My Feature",
                status="active"
            )
            db.add(exec_session)
            db.commit()
            db.refresh(exec_session)

            response = client.get(
                f"/sessions/{exec_session.id}",
                cookies={"session_id": session_id}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == exec_session.id
            assert data["feature_name"] == "My Feature"
            assert data["status"] == "active"
        finally:
            db.close()

    @patch.object(SessionService, 'get_session')
    def test_get_session_not_owner(self, mock_get_session):
        """Test that getting another user's session fails"""
        db = SessionLocal()
        try:
            # Create session owner
            owner = User(
                username="session_owner",
                email="session_owner@test.com",
                password_hash=user_service.hash_password("password")
            )
            db.add(owner)
            db.commit()

            team = create_team_for_user(db, owner)

            exec_session = ExecutionSession(
                team_id=team.id,
                user_id=owner.id,
                feature_name="Owner's Feature",
                status="active"
            )
            db.add(exec_session)
            db.commit()
            db.refresh(exec_session)

            # Create another user trying to access
            other_user, session_id = create_authenticated_user(db, "not_owner")
            mock_get_session.return_value = other_user.id

            response = client.get(
                f"/sessions/{exec_session.id}",
                cookies={"session_id": session_id}
            )

            assert response.status_code == 403
        finally:
            db.close()

    @patch.object(SessionService, 'get_session')
    def test_complete_session(self, mock_get_session):
        """Test completing a session and verifying duration is calculated"""
        db = SessionLocal()
        try:
            user, session_id = create_authenticated_user(db, "complete_session")
            mock_get_session.return_value = user.id

            team = create_team_for_user(db, user)

            # Create session with a known start time
            start_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1, minutes=30)
            exec_session = ExecutionSession(
                team_id=team.id,
                user_id=user.id,
                feature_name="Feature to Complete",
                status="active",
                started_at=start_time
            )
            db.add(exec_session)
            db.commit()
            db.refresh(exec_session)

            response = client.put(
                f"/sessions/{exec_session.id}/complete",
                cookies={"session_id": session_id}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert data["ended_at"] is not None
            assert data["duration_seconds"] is not None
            # Should be approximately 5400 seconds (1.5 hours)
            assert data["duration_seconds"] >= 5398  # Allow small variance
            assert data["duration_seconds"] <= 5410
        finally:
            db.close()

    @patch.object(SessionService, 'get_session')
    def test_add_decision(self, mock_get_session):
        """Test adding a decision to a session"""
        db = SessionLocal()
        try:
            user, session_id = create_authenticated_user(db, "add_decision")
            mock_get_session.return_value = user.id

            team = create_team_for_user(db, user)

            exec_session = ExecutionSession(
                team_id=team.id,
                user_id=user.id,
                feature_name="Feature with Decisions",
                status="active"
            )
            db.add(exec_session)
            db.commit()
            db.refresh(exec_session)

            response = client.post(
                f"/sessions/{exec_session.id}/decisions",
                json={
                    "decision_text": "Use PostgreSQL for the database",
                    "category": "architecture",
                    "confidence": "high"
                },
                cookies={"session_id": session_id}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == exec_session.id
            assert data["decision_text"] == "Use PostgreSQL for the database"
            assert data["category"] == "architecture"
            assert data["confidence"] == "high"
        finally:
            db.close()

    @patch.object(SessionService, 'get_session')
    def test_list_decisions(self, mock_get_session):
        """Test getting all decisions for a session"""
        db = SessionLocal()
        try:
            user, session_id = create_authenticated_user(db, "list_decisions")
            mock_get_session.return_value = user.id

            team = create_team_for_user(db, user)

            exec_session = ExecutionSession(
                team_id=team.id,
                user_id=user.id,
                feature_name="Feature with Many Decisions",
                status="active"
            )
            db.add(exec_session)
            db.commit()
            db.refresh(exec_session)

            # Create some decisions
            decision1 = SessionDecision(
                session_id=exec_session.id,
                decision_text="Use REST API",
                category="api",
                confidence="high"
            )
            decision2 = SessionDecision(
                session_id=exec_session.id,
                decision_text="Implement pagination",
                category="performance",
                confidence="medium"
            )
            db.add_all([decision1, decision2])
            db.commit()

            response = client.get(
                f"/sessions/{exec_session.id}/decisions",
                cookies={"session_id": session_id}
            )

            assert response.status_code == 200
            decisions = response.json()
            assert len(decisions) == 2
            decision_texts = [d["decision_text"] for d in decisions]
            assert "Use REST API" in decision_texts
            assert "Implement pagination" in decision_texts
        finally:
            db.close()

    @patch.object(SessionService, 'get_session')
    def test_get_session_not_found(self, mock_get_session):
        """Test getting a non-existent session returns 404"""
        db = SessionLocal()
        try:
            user, session_id = create_authenticated_user(db, "not_found")
            mock_get_session.return_value = user.id

            response = client.get(
                "/sessions/99999",
                cookies={"session_id": session_id}
            )

            assert response.status_code == 404
        finally:
            db.close()

    def test_session_unauthenticated(self):
        """Test that accessing sessions without auth fails"""
        response = client.get("/sessions")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    @patch.object(SessionService, 'get_session')
    def test_invalid_session(self, mock_get_session):
        """Test that invalid session returns 401"""
        mock_get_session.return_value = None

        response = client.get(
            "/sessions",
            cookies={"session_id": "invalid_session"}
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    @patch.object(SessionService, 'get_session')
    def test_list_tasks(self, mock_get_session):
        """Test getting all agent tasks for a session"""
        db = SessionLocal()
        try:
            user, session_id = create_authenticated_user(db, "list_tasks")
            mock_get_session.return_value = user.id

            team = create_team_for_user(db, user)

            exec_session = ExecutionSession(
                team_id=team.id,
                user_id=user.id,
                feature_name="Feature with Tasks",
                status="active"
            )
            db.add(exec_session)
            db.commit()
            db.refresh(exec_session)

            # Create some agent tasks
            task1 = AgentTask(
                session_id=exec_session.id,
                agent_role="Architect",
                task_description="Design system architecture",
                status="completed",
                duration_seconds=120
            )
            task2 = AgentTask(
                session_id=exec_session.id,
                agent_role="Frontend Dev",
                task_description="Implement UI components",
                status="running"
            )
            db.add_all([task1, task2])
            db.commit()

            response = client.get(
                f"/sessions/{exec_session.id}/tasks",
                cookies={"session_id": session_id}
            )

            assert response.status_code == 200
            tasks = response.json()
            assert len(tasks) == 2
            agent_roles = [t["agent_role"] for t in tasks]
            assert "Architect" in agent_roles
            assert "Frontend Dev" in agent_roles
            # Check specific task fields
            architect_task = next(t for t in tasks if t["agent_role"] == "Architect")
            assert architect_task["task_description"] == "Design system architecture"
            assert architect_task["status"] == "completed"
            assert architect_task["duration_seconds"] == 120
        finally:
            db.close()

    @patch.object(SessionService, 'get_session')
    def test_list_tasks_empty(self, mock_get_session):
        """Test getting tasks when session has no tasks"""
        db = SessionLocal()
        try:
            user, session_id = create_authenticated_user(db, "list_tasks_empty")
            mock_get_session.return_value = user.id

            team = create_team_for_user(db, user)

            exec_session = ExecutionSession(
                team_id=team.id,
                user_id=user.id,
                feature_name="Feature without Tasks",
                status="active"
            )
            db.add(exec_session)
            db.commit()
            db.refresh(exec_session)

            response = client.get(
                f"/sessions/{exec_session.id}/tasks",
                cookies={"session_id": session_id}
            )

            assert response.status_code == 200
            tasks = response.json()
            assert len(tasks) == 0
        finally:
            db.close()

    @patch.object(SessionService, 'get_session')
    def test_list_tasks_not_owner(self, mock_get_session):
        """Test that getting another user's session tasks fails"""
        db = SessionLocal()
        try:
            # Create session owner
            owner = User(
                username="task_session_owner",
                email="task_session_owner@test.com",
                password_hash=user_service.hash_password("password")
            )
            db.add(owner)
            db.commit()

            team = create_team_for_user(db, owner)

            exec_session = ExecutionSession(
                team_id=team.id,
                user_id=owner.id,
                feature_name="Owner's Feature with Tasks",
                status="active"
            )
            db.add(exec_session)
            db.commit()
            db.refresh(exec_session)

            # Create another user trying to access
            other_user, session_id = create_authenticated_user(db, "not_task_owner")
            mock_get_session.return_value = other_user.id

            response = client.get(
                f"/sessions/{exec_session.id}/tasks",
                cookies={"session_id": session_id}
            )

            assert response.status_code == 403
        finally:
            db.close()

    @patch.object(SessionService, 'get_session')
    def test_list_tasks_session_not_found(self, mock_get_session):
        """Test getting tasks for non-existent session returns 404"""
        db = SessionLocal()
        try:
            user, session_id = create_authenticated_user(db, "tasks_not_found")
            mock_get_session.return_value = user.id

            response = client.get(
                "/sessions/99999/tasks",
                cookies={"session_id": session_id}
            )

            assert response.status_code == 404
        finally:
            db.close()
