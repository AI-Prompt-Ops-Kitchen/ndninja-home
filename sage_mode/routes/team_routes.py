"""Team routes with JWT authentication.

Provides CRUD operations for teams and team membership.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from sage_mode.database import get_db
from sage_mode.models.user_model import User
from sage_mode.models.team_model import Team, TeamMembership
from sage_mode.security import require_auth, AuthenticatedUser
from sqlalchemy.orm import Session

router = APIRouter(prefix="/teams", tags=["teams"])


class TeamRequest(BaseModel):
    name: str
    description: Optional[str] = None


class TeamUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_shared: Optional[bool] = None


class TeamResponse(BaseModel):
    id: int
    name: str
    is_shared: bool
    owner_id: int

    model_config = ConfigDict(from_attributes=True)


class InviteRequest(BaseModel):
    user_id: int


@router.post("", response_model=TeamResponse)
def create_team(
    team_data: TeamRequest,
    current_user: AuthenticatedUser = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Create a new team"""
    user_id = current_user.id

    team = Team(
        name=team_data.name,
        description=team_data.description,
        owner_id=user_id,
        is_shared=False
    )
    db.add(team)
    db.commit()
    db.refresh(team)

    return TeamResponse(
        id=team.id,
        name=team.name,
        is_shared=team.is_shared,
        owner_id=team.owner_id
    )


@router.get("", response_model=List[TeamResponse])
def list_teams(
    current_user: AuthenticatedUser = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """List all teams user can access (owned + member of)"""
    user_id = current_user.id

    # Get teams owned by user
    owned_teams = db.query(Team).filter(Team.owner_id == user_id).all()

    # Get teams user is a member of
    member_team_ids = db.query(TeamMembership.team_id).filter(
        TeamMembership.user_id == user_id
    ).all()
    member_team_ids = [t[0] for t in member_team_ids]

    member_teams = db.query(Team).filter(
        Team.id.in_(member_team_ids)
    ).all() if member_team_ids else []

    # Combine and deduplicate
    all_teams = {t.id: t for t in owned_teams}
    for team in member_teams:
        if team.id not in all_teams:
            all_teams[team.id] = team

    return [
        TeamResponse(
            id=t.id,
            name=t.name,
            is_shared=t.is_shared,
            owner_id=t.owner_id
        )
        for t in all_teams.values()
    ]


@router.get("/{team_id}", response_model=TeamResponse)
def get_team(
    team_id: int,
    current_user: AuthenticatedUser = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get specific team details"""
    user_id = current_user.id

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Check user has access (owner or member)
    is_owner = team.owner_id == user_id
    is_member = db.query(TeamMembership).filter(
        TeamMembership.team_id == team_id,
        TeamMembership.user_id == user_id
    ).first() is not None

    if not is_owner and not is_member:
        raise HTTPException(status_code=403, detail="Access denied")

    return TeamResponse(
        id=team.id,
        name=team.name,
        is_shared=team.is_shared,
        owner_id=team.owner_id
    )


@router.put("/{team_id}", response_model=TeamResponse)
def update_team(
    team_id: int,
    update_data: TeamUpdateRequest,
    current_user: AuthenticatedUser = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Update team (name, description, is_shared) - only owner"""
    user_id = current_user.id

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Only owner can update
    if team.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Only owner can update team")

    # Update fields if provided
    if update_data.name is not None:
        team.name = update_data.name
    if update_data.description is not None:
        team.description = update_data.description
    if update_data.is_shared is not None:
        team.is_shared = update_data.is_shared

    db.commit()
    db.refresh(team)

    return TeamResponse(
        id=team.id,
        name=team.name,
        is_shared=team.is_shared,
        owner_id=team.owner_id
    )


@router.delete("/{team_id}")
def delete_team(
    team_id: int,
    current_user: AuthenticatedUser = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Delete team (only owner)"""
    user_id = current_user.id

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Only owner can delete
    if team.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Only owner can delete team")

    # Delete memberships first (foreign key constraint)
    db.query(TeamMembership).filter(TeamMembership.team_id == team_id).delete()

    # Delete team
    db.delete(team)
    db.commit()

    return {"message": "Team deleted successfully"}


@router.post("/{team_id}/invite")
def invite_to_team(
    team_id: int,
    invite_data: InviteRequest,
    current_user: AuthenticatedUser = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Add user to shared team - only owner can invite"""
    user_id = current_user.id

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Only owner can invite
    if team.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Only owner can invite users")

    # Team must be shared
    if not team.is_shared:
        raise HTTPException(status_code=400, detail="Team is not shared. Enable sharing first.")

    # Verify user to invite exists
    invitee = db.query(User).filter(User.id == invite_data.user_id).first()
    if not invitee:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if already a member
    existing = db.query(TeamMembership).filter(
        TeamMembership.team_id == team_id,
        TeamMembership.user_id == invite_data.user_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="User is already a member")

    # Create membership
    membership = TeamMembership(
        team_id=team_id,
        user_id=invite_data.user_id,
        role="member"
    )
    db.add(membership)
    db.commit()

    return {"message": f"User {invitee.username} added to team"}
