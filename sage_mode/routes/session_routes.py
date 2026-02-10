"""Session routes with JWT authentication.

Provides CRUD operations for execution sessions, decisions, and tasks.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sage_mode.database import get_db
from sage_mode.models.session_model import ExecutionSession, SessionDecision
from sage_mode.models.task_model import AgentTask
from sage_mode.models.team_model import Team, TeamMembership
from sage_mode.security import require_auth, AuthenticatedUser
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional, List

router = APIRouter(prefix="/sessions", tags=["sessions"])


class SessionRequest(BaseModel):
    team_id: int
    feature_name: str


class SessionResponse(BaseModel):
    id: int
    team_id: int
    user_id: int
    feature_name: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


class DecisionRequest(BaseModel):
    decision_text: str
    category: Optional[str] = None
    confidence: str = "high"


class DecisionResponse(BaseModel):
    id: int
    session_id: int
    decision_text: str
    category: Optional[str] = None
    confidence: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AgentTaskResponse(BaseModel):
    id: int
    session_id: int
    agent_role: str
    task_description: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


def user_has_team_access(db: Session, user_id: int, team_id: int) -> bool:
    """Check if user is owner or member of the team"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        return False

    # Check if user is owner
    if team.owner_id == user_id:
        return True

    # Check if user is member
    membership = db.query(TeamMembership).filter(
        TeamMembership.team_id == team_id,
        TeamMembership.user_id == user_id
    ).first()

    return membership is not None


@router.post("", response_model=SessionResponse)
def start_session(
    session_data: SessionRequest,
    current_user: AuthenticatedUser = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Start a new execution session"""
    user_id = current_user.id

    # Validate team access
    if not user_has_team_access(db, user_id, session_data.team_id):
        raise HTTPException(status_code=403, detail="Access denied to team")

    exec_session = ExecutionSession(
        team_id=session_data.team_id,
        user_id=user_id,
        feature_name=session_data.feature_name,
        status="active"
    )
    db.add(exec_session)
    db.commit()
    db.refresh(exec_session)

    return SessionResponse(
        id=exec_session.id,
        team_id=exec_session.team_id,
        user_id=exec_session.user_id,
        feature_name=exec_session.feature_name,
        status=exec_session.status,
        started_at=exec_session.started_at,
        ended_at=exec_session.ended_at,
        duration_seconds=exec_session.duration_seconds
    )


@router.get("", response_model=List[SessionResponse])
def list_sessions(
    current_user: AuthenticatedUser = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """List user's execution sessions"""
    user_id = current_user.id

    sessions = db.query(ExecutionSession).filter(
        ExecutionSession.user_id == user_id
    ).order_by(ExecutionSession.started_at.desc()).all()

    return [
        SessionResponse(
            id=s.id,
            team_id=s.team_id,
            user_id=s.user_id,
            feature_name=s.feature_name,
            status=s.status,
            started_at=s.started_at,
            ended_at=s.ended_at,
            duration_seconds=s.duration_seconds
        )
        for s in sessions
    ]


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: int,
    current_user: AuthenticatedUser = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get session details"""
    user_id = current_user.id

    exec_session = db.query(ExecutionSession).filter(
        ExecutionSession.id == session_id
    ).first()

    if not exec_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Only session owner can view
    if exec_session.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return SessionResponse(
        id=exec_session.id,
        team_id=exec_session.team_id,
        user_id=exec_session.user_id,
        feature_name=exec_session.feature_name,
        status=exec_session.status,
        started_at=exec_session.started_at,
        ended_at=exec_session.ended_at,
        duration_seconds=exec_session.duration_seconds
    )


@router.put("/{session_id}/complete", response_model=SessionResponse)
def complete_session(
    session_id: int,
    current_user: AuthenticatedUser = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Mark session as completed and calculate duration"""
    user_id = current_user.id

    exec_session = db.query(ExecutionSession).filter(
        ExecutionSession.id == session_id
    ).first()

    if not exec_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Only session owner can complete
    if exec_session.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Set ended_at and calculate duration
    exec_session.ended_at = datetime.now(timezone.utc).replace(tzinfo=None)
    exec_session.status = "completed"

    # Calculate duration in seconds
    if exec_session.started_at:
        duration = exec_session.ended_at - exec_session.started_at
        exec_session.duration_seconds = int(duration.total_seconds())

    db.commit()
    db.refresh(exec_session)

    return SessionResponse(
        id=exec_session.id,
        team_id=exec_session.team_id,
        user_id=exec_session.user_id,
        feature_name=exec_session.feature_name,
        status=exec_session.status,
        started_at=exec_session.started_at,
        ended_at=exec_session.ended_at,
        duration_seconds=exec_session.duration_seconds
    )


@router.post("/{session_id}/decisions", response_model=DecisionResponse)
def add_decision(
    session_id: int,
    decision_data: DecisionRequest,
    current_user: AuthenticatedUser = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Add a decision to the session"""
    user_id = current_user.id

    exec_session = db.query(ExecutionSession).filter(
        ExecutionSession.id == session_id
    ).first()

    if not exec_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Only session owner can add decisions
    if exec_session.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    decision = SessionDecision(
        session_id=session_id,
        decision_text=decision_data.decision_text,
        category=decision_data.category,
        confidence=decision_data.confidence
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)

    return DecisionResponse(
        id=decision.id,
        session_id=decision.session_id,
        decision_text=decision.decision_text,
        category=decision.category,
        confidence=decision.confidence,
        created_at=decision.created_at
    )


@router.get("/{session_id}/decisions", response_model=List[DecisionResponse])
def list_decisions(
    session_id: int,
    current_user: AuthenticatedUser = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """List all decisions for a session"""
    user_id = current_user.id

    exec_session = db.query(ExecutionSession).filter(
        ExecutionSession.id == session_id
    ).first()

    if not exec_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Only session owner can view decisions
    if exec_session.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    decisions = db.query(SessionDecision).filter(
        SessionDecision.session_id == session_id
    ).order_by(SessionDecision.created_at.asc()).all()

    return [
        DecisionResponse(
            id=d.id,
            session_id=d.session_id,
            decision_text=d.decision_text,
            category=d.category,
            confidence=d.confidence,
            created_at=d.created_at
        )
        for d in decisions
    ]


@router.get("/{session_id}/tasks", response_model=List[AgentTaskResponse])
def list_tasks(
    session_id: int,
    current_user: AuthenticatedUser = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """List all agent tasks for a session"""
    user_id = current_user.id

    exec_session = db.query(ExecutionSession).filter(
        ExecutionSession.id == session_id
    ).first()

    if not exec_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Only session owner can view tasks
    if exec_session.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    tasks = db.query(AgentTask).filter(
        AgentTask.session_id == session_id
    ).order_by(AgentTask.created_at.asc()).all()

    return [
        AgentTaskResponse(
            id=t.id,
            session_id=t.session_id,
            agent_role=t.agent_role,
            task_description=t.task_description,
            status=t.status,
            started_at=t.started_at,
            completed_at=t.completed_at,
            duration_seconds=t.duration_seconds,
            error_message=t.error_message,
            created_at=t.created_at
        )
        for t in tasks
    ]
