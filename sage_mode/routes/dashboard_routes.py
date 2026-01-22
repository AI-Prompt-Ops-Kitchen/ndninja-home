from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict
from sage_mode.database import get_db
from sage_mode.models.session_model import ExecutionSession, SessionDecision
from sage_mode.models.task_model import AgentTask, TaskDecision
from sage_mode.models.team_model import Team, TeamMembership
from sage_mode.services.session_service import SessionService
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
session_service = SessionService()


# Response models
class TeamStats(BaseModel):
    team_id: int
    team_name: str
    total_sessions: int
    active_sessions: int
    completed_sessions: int
    total_decisions: int
    model_config = ConfigDict(from_attributes=True)


class RecentDecision(BaseModel):
    id: int
    decision_text: str
    category: Optional[str]
    confidence: str
    session_feature: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AgentStatus(BaseModel):
    agent_role: str
    total_tasks: int
    pending_tasks: int
    completed_tasks: int
    failed_tasks: int
    avg_duration_seconds: Optional[float]
    model_config = ConfigDict(from_attributes=True)


class DashboardOverview(BaseModel):
    status: str
    version: str
    total_teams: int
    total_sessions: int
    total_decisions: int
    model_config = ConfigDict(from_attributes=True)


def get_current_user_id(request: Request, db: Session = Depends(get_db)) -> int:
    """Get current user ID from session"""
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = session_service.get_session(session_id)
    if not user_id:
        raise HTTPException(status_code=401, detail="Session invalid")
    return user_id


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


@router.get("", response_model=DashboardOverview)
def dashboard_overview(
    request: Request,
    db: Session = Depends(get_db)
):
    """Dashboard overview with health check and counts"""
    user_id = get_current_user_id(request, db)

    # Get teams user has access to (owned + member of)
    owned_team_ids = db.query(Team.id).filter(Team.owner_id == user_id).all()
    owned_team_ids = [t[0] for t in owned_team_ids]

    member_team_ids = db.query(TeamMembership.team_id).filter(
        TeamMembership.user_id == user_id
    ).all()
    member_team_ids = [t[0] for t in member_team_ids]

    accessible_team_ids = list(set(owned_team_ids + member_team_ids))
    total_teams = len(accessible_team_ids)

    # Count sessions for accessible teams
    total_sessions = 0
    total_decisions = 0
    if accessible_team_ids:
        total_sessions = db.query(func.count(ExecutionSession.id)).filter(
            ExecutionSession.team_id.in_(accessible_team_ids)
        ).scalar() or 0

        # Count decisions for sessions in accessible teams
        session_ids = db.query(ExecutionSession.id).filter(
            ExecutionSession.team_id.in_(accessible_team_ids)
        ).all()
        session_ids = [s[0] for s in session_ids]

        if session_ids:
            total_decisions = db.query(func.count(SessionDecision.id)).filter(
                SessionDecision.session_id.in_(session_ids)
            ).scalar() or 0

    return DashboardOverview(
        status="healthy",
        version="3.0",
        total_teams=total_teams,
        total_sessions=total_sessions,
        total_decisions=total_decisions
    )


@router.get("/teams/{team_id}/stats", response_model=TeamStats)
def get_team_stats(
    team_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get statistics for a specific team"""
    user_id = get_current_user_id(request, db)

    # Check team access
    if not user_has_team_access(db, user_id, team_id):
        raise HTTPException(status_code=403, detail="Access denied to team")

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Get session counts
    total_sessions = db.query(func.count(ExecutionSession.id)).filter(
        ExecutionSession.team_id == team_id
    ).scalar() or 0

    active_sessions = db.query(func.count(ExecutionSession.id)).filter(
        ExecutionSession.team_id == team_id,
        ExecutionSession.status == "active"
    ).scalar() or 0

    completed_sessions = db.query(func.count(ExecutionSession.id)).filter(
        ExecutionSession.team_id == team_id,
        ExecutionSession.status == "completed"
    ).scalar() or 0

    # Get decision count for this team's sessions
    session_ids = db.query(ExecutionSession.id).filter(
        ExecutionSession.team_id == team_id
    ).all()
    session_ids = [s[0] for s in session_ids]

    total_decisions = 0
    if session_ids:
        total_decisions = db.query(func.count(SessionDecision.id)).filter(
            SessionDecision.session_id.in_(session_ids)
        ).scalar() or 0

    return TeamStats(
        team_id=team.id,
        team_name=team.name,
        total_sessions=total_sessions,
        active_sessions=active_sessions,
        completed_sessions=completed_sessions,
        total_decisions=total_decisions
    )


@router.get("/teams/{team_id}/decisions", response_model=List[RecentDecision])
def get_recent_decisions(
    team_id: int,
    request: Request,
    db: Session = Depends(get_db),
    limit: int = 20
):
    """Get recent decisions for a team"""
    user_id = get_current_user_id(request, db)

    # Check team access
    if not user_has_team_access(db, user_id, team_id):
        raise HTTPException(status_code=403, detail="Access denied to team")

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Get session IDs for this team
    session_ids = db.query(ExecutionSession.id).filter(
        ExecutionSession.team_id == team_id
    ).all()
    session_ids = [s[0] for s in session_ids]

    if not session_ids:
        return []

    # Get decisions with session feature name using a join
    decisions = db.query(
        SessionDecision,
        ExecutionSession.feature_name
    ).join(
        ExecutionSession,
        SessionDecision.session_id == ExecutionSession.id
    ).filter(
        SessionDecision.session_id.in_(session_ids)
    ).order_by(
        SessionDecision.created_at.desc()
    ).limit(limit).all()

    return [
        RecentDecision(
            id=d[0].id,
            decision_text=d[0].decision_text,
            category=d[0].category,
            confidence=d[0].confidence,
            session_feature=d[1] or "Unknown",
            created_at=d[0].created_at
        )
        for d in decisions
    ]


@router.get("/teams/{team_id}/agents", response_model=List[AgentStatus])
def get_agent_status(
    team_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get agent task status summary for a team"""
    user_id = get_current_user_id(request, db)

    # Check team access
    if not user_has_team_access(db, user_id, team_id):
        raise HTTPException(status_code=403, detail="Access denied to team")

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Get session IDs for this team
    session_ids = db.query(ExecutionSession.id).filter(
        ExecutionSession.team_id == team_id
    ).all()
    session_ids = [s[0] for s in session_ids]

    if not session_ids:
        return []

    # Get all tasks for sessions and aggregate manually for better compatibility
    tasks = db.query(AgentTask).filter(
        AgentTask.session_id.in_(session_ids)
    ).all()

    if not tasks:
        return []

    # Aggregate by agent_role
    agent_data = {}
    for task in tasks:
        role = task.agent_role
        if role not in agent_data:
            agent_data[role] = {
                'total': 0,
                'pending': 0,
                'completed': 0,
                'failed': 0,
                'durations': []
            }
        agent_data[role]['total'] += 1
        if task.status == 'pending':
            agent_data[role]['pending'] += 1
        elif task.status == 'completed':
            agent_data[role]['completed'] += 1
        elif task.status == 'failed':
            agent_data[role]['failed'] += 1
        if task.duration_seconds is not None:
            agent_data[role]['durations'].append(task.duration_seconds)

    result = []
    for role, data in sorted(agent_data.items()):
        avg_duration = None
        if data['durations']:
            avg_duration = sum(data['durations']) / len(data['durations'])
        result.append(AgentStatus(
            agent_role=role,
            total_tasks=data['total'],
            pending_tasks=data['pending'],
            completed_tasks=data['completed'],
            failed_tasks=data['failed'],
            avg_duration_seconds=avg_duration
        ))

    return result
