"""Tests for WebSocket routes with JWT authentication."""

import os
import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket

# Set test environment variables before importing
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")

from sage_mode.main import app
from sage_mode.database import SessionLocal, engine, Base
from sage_mode.models.user_model import User
from sage_mode.models.team_model import Team
from sage_mode.models.session_model import ExecutionSession
from sage_mode.services.user_service import UserService
from sage_mode.security import create_token_pair
from sage_mode.routes.websocket_routes import manager

client = TestClient(app)
user_service = UserService()


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables and cleanup after each test"""
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup
    db = SessionLocal()
    db.query(ExecutionSession).delete()
    db.query(Team).delete()
    db.query(User).delete()
    db.commit()
    db.close()


@pytest.fixture
def reset_manager():
    """Reset the connection manager between tests"""
    manager.active_connections.clear()
    yield
    manager.active_connections.clear()


def create_test_user_and_session(db):
    """Helper to create user, team, execution session, and JWT token"""
    user = User(
        username="testuser_ws",
        email="ws_test@test.com",
        password_hash=user_service.hash_password("password")
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    team = Team(
        name="Test Team",
        owner_id=user.id,
        is_shared=False
    )
    db.add(team)
    db.commit()
    db.refresh(team)

    exec_session = ExecutionSession(
        team_id=team.id,
        user_id=user.id,
        feature_name="WebSocket Test Feature",
        status="active"
    )
    db.add(exec_session)
    db.commit()
    db.refresh(exec_session)

    tokens = create_token_pair(user_id=user.id, role="member")

    return user, team, exec_session, tokens.access_token


class TestWebSocketConnect:
    """Test WebSocket connection functionality"""

    def test_websocket_connect(self):
        """Test connecting to session websocket with valid auth"""
        db = SessionLocal()
        try:
            user, team, exec_session, token = create_test_user_and_session(db)

            with client.websocket_connect(
                f"/ws/sessions/{exec_session.id}?token={token}"
            ) as websocket:
                # Connection should be accepted
                # Send a test message to verify connection
                data = websocket.receive_json()
                assert data["type"] == "connected"
                assert data["session_id"] == exec_session.id

        finally:
            db.close()

    def test_websocket_disconnect(self, reset_manager):
        """Test graceful disconnect from websocket"""
        db = SessionLocal()
        try:
            user, team, exec_session, token = create_test_user_and_session(db)

            with client.websocket_connect(
                f"/ws/sessions/{exec_session.id}?token={token}"
            ) as websocket:
                # Receive connection confirmation
                websocket.receive_json()
                # Connection is active
                assert exec_session.id in manager.active_connections

            # After context manager exits, connection should be cleaned up
            # Note: TestClient may handle cleanup differently, but manager should be clean
            assert exec_session.id not in manager.active_connections or \
                   len(manager.active_connections.get(exec_session.id, set())) == 0

        finally:
            db.close()

    def test_websocket_invalid_token(self):
        """Test that invalid auth token rejects connection"""
        db = SessionLocal()
        try:
            user, team, exec_session, _ = create_test_user_and_session(db)

            with pytest.raises(Exception):  # WebSocket connection should fail
                with client.websocket_connect(
                    f"/ws/sessions/{exec_session.id}?token=invalid_token"
                ) as websocket:
                    websocket.receive_json()  # Should not reach here

        finally:
            db.close()

    def test_websocket_no_token(self):
        """Test that missing token rejects connection"""
        db = SessionLocal()
        try:
            user, team, exec_session, _ = create_test_user_and_session(db)

            with pytest.raises(Exception):
                with client.websocket_connect(
                    f"/ws/sessions/{exec_session.id}"  # No token
                ) as websocket:
                    websocket.receive_json()

        finally:
            db.close()


class TestConnectionManager:
    """Test ConnectionManager class functionality"""

    @pytest.mark.asyncio
    async def test_connection_manager_connect(self, reset_manager):
        """Test that ConnectionManager properly registers connections"""
        mock_websocket = AsyncMock(spec=WebSocket)
        session_id = 123

        await manager.connect(mock_websocket, session_id)

        assert session_id in manager.active_connections
        assert mock_websocket in manager.active_connections[session_id]
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_connection_manager_disconnect(self, reset_manager):
        """Test that ConnectionManager properly removes connections"""
        mock_websocket = AsyncMock(spec=WebSocket)
        session_id = 123

        await manager.connect(mock_websocket, session_id)
        manager.disconnect(mock_websocket, session_id)

        # Session should be removed entirely when last connection disconnects
        assert session_id not in manager.active_connections

    @pytest.mark.asyncio
    async def test_connection_manager_multiple_connections(self, reset_manager):
        """Test that multiple connections to same session are tracked"""
        ws1 = AsyncMock(spec=WebSocket)
        ws2 = AsyncMock(spec=WebSocket)
        session_id = 123

        await manager.connect(ws1, session_id)
        await manager.connect(ws2, session_id)

        assert len(manager.active_connections[session_id]) == 2
        assert ws1 in manager.active_connections[session_id]
        assert ws2 in manager.active_connections[session_id]

        # Disconnect one
        manager.disconnect(ws1, session_id)
        assert len(manager.active_connections[session_id]) == 1
        assert ws2 in manager.active_connections[session_id]

    @pytest.mark.asyncio
    async def test_websocket_broadcast(self, reset_manager):
        """Test broadcast message to all connections watching a session"""
        ws1 = AsyncMock(spec=WebSocket)
        ws2 = AsyncMock(spec=WebSocket)
        session_id = 123

        await manager.connect(ws1, session_id)
        await manager.connect(ws2, session_id)

        test_message = {
            "type": "task_completed",
            "task": "test_task",
            "status": "success"
        }

        await manager.broadcast_to_session(session_id, test_message)

        ws1.send_json.assert_called_once_with(test_message)
        ws2.send_json.assert_called_once_with(test_message)

    @pytest.mark.asyncio
    async def test_connection_manager_cleanup(self, reset_manager):
        """Test that manager cleans up disconnected clients during broadcast"""
        ws_good = AsyncMock(spec=WebSocket)
        ws_bad = AsyncMock(spec=WebSocket)
        # Simulate a failed connection
        ws_bad.send_json.side_effect = Exception("Connection closed")
        session_id = 123

        await manager.connect(ws_good, session_id)
        await manager.connect(ws_bad, session_id)

        test_message = {"type": "test"}

        await manager.broadcast_to_session(session_id, test_message)

        # Good connection should have received message
        ws_good.send_json.assert_called_once_with(test_message)
        # Bad connection should be removed from manager
        assert ws_bad not in manager.active_connections[session_id]
        # Good connection should still be there
        assert ws_good in manager.active_connections[session_id]

    @pytest.mark.asyncio
    async def test_broadcast_to_nonexistent_session(self, reset_manager):
        """Test that broadcasting to non-existent session doesn't error"""
        test_message = {"type": "test"}

        # Should not raise any errors
        await manager.broadcast_to_session(99999, test_message)


class TestWebSocketSessionAccess:
    """Test session access control for WebSocket"""

    def test_websocket_wrong_user_denied(self):
        """Test that user cannot connect to another user's session"""
        db = SessionLocal()
        try:
            # Create owner and session
            owner = User(
                username="owner_ws",
                email="owner_ws@test.com",
                password_hash=user_service.hash_password("password")
            )
            db.add(owner)
            db.commit()
            db.refresh(owner)

            team = Team(
                name="Owner's Team",
                owner_id=owner.id,
                is_shared=False
            )
            db.add(team)
            db.commit()
            db.refresh(team)

            exec_session = ExecutionSession(
                team_id=team.id,
                user_id=owner.id,
                feature_name="Owner's Feature",
                status="active"
            )
            db.add(exec_session)
            db.commit()
            db.refresh(exec_session)

            # Create other user trying to access
            other_user = User(
                username="other_ws",
                email="other_ws@test.com",
                password_hash=user_service.hash_password("password")
            )
            db.add(other_user)
            db.commit()
            db.refresh(other_user)

            # Create token for the other user (valid token, but different user)
            other_tokens = create_token_pair(user_id=other_user.id, role="member")

            with pytest.raises(Exception):  # Should fail access check
                with client.websocket_connect(
                    f"/ws/sessions/{exec_session.id}?token={other_tokens.access_token}"
                ) as websocket:
                    websocket.receive_json()

        finally:
            db.close()

    def test_websocket_nonexistent_session(self):
        """Test connecting to non-existent execution session"""
        db = SessionLocal()
        try:
            user, _, _, token = create_test_user_and_session(db)

            with pytest.raises(Exception):
                with client.websocket_connect(
                    f"/ws/sessions/99999?token={token}"  # Non-existent
                ) as websocket:
                    websocket.receive_json()

        finally:
            db.close()
