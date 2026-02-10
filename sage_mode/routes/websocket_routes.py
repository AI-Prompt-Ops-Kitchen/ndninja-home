from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sage_mode.database import SessionLocal
from sage_mode.models.session_model import ExecutionSession
from sage_mode.security import verify_access_token
from sqlalchemy.orm import Session
from typing import Dict, Set, Optional
import json

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        # Map of session_id -> set of active websocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, execution_session_id: int):
        """Accept and register a WebSocket connection"""
        await websocket.accept()
        if execution_session_id not in self.active_connections:
            self.active_connections[execution_session_id] = set()
        self.active_connections[execution_session_id].add(websocket)

    def disconnect(self, websocket: WebSocket, execution_session_id: int):
        """Remove a WebSocket connection"""
        if execution_session_id in self.active_connections:
            self.active_connections[execution_session_id].discard(websocket)
            if not self.active_connections[execution_session_id]:
                del self.active_connections[execution_session_id]

    async def broadcast_to_session(self, execution_session_id: int, message: dict):
        """Send message to all connections watching a session"""
        if execution_session_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[execution_session_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.append(connection)
            for conn in disconnected:
                self.disconnect(conn, execution_session_id)


manager = ConnectionManager()


def verify_session_access(token: str, execution_session_id: int, db: Session) -> Optional[int]:
    """
    Verify the user has access to the execution session.
    Returns user_id if access is granted, None otherwise.
    """
    if not token:
        return None

    # Validate the JWT access token
    payload = verify_access_token(token)
    if not payload:
        return None

    user_id = int(payload.sub)

    # Check if execution session exists and belongs to the user
    exec_session = db.query(ExecutionSession).filter(
        ExecutionSession.id == execution_session_id
    ).first()

    if not exec_session:
        return None

    # Verify user owns this session
    if exec_session.user_id != user_id:
        return None

    return user_id


@router.websocket("/ws/sessions/{session_id}")
async def websocket_session_endpoint(
    websocket: WebSocket,
    session_id: int,
    token: str = Query(default=None)
):
    """
    WebSocket endpoint for real-time session updates.

    Connect via: ws://host/ws/sessions/{session_id}?token=session_cookie_value

    Message types:
    - "connected": Initial connection confirmation
    - "task_started": A task has started
    - "task_completed": A task has completed
    - "decision_made": A decision was recorded
    - "session_completed": The entire session is complete
    """
    # Create a database session for verification
    db = SessionLocal()
    try:
        # Verify access before accepting the connection
        user_id = verify_session_access(token, session_id, db)

        if not user_id:
            await websocket.close(code=4001, reason="Unauthorized")
            return

        # Accept the connection and register it
        await manager.connect(websocket, session_id)

        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "user_id": user_id
        })

        try:
            # Keep connection alive and listen for client messages
            while True:
                # Wait for any incoming messages (ping/pong or commands)
                data = await websocket.receive_text()
                # Parse client messages if needed
                try:
                    message = json.loads(data)
                    if message.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                except json.JSONDecodeError:
                    pass  # Ignore malformed messages

        except WebSocketDisconnect:
            # Client disconnected
            manager.disconnect(websocket, session_id)

    finally:
        db.close()
