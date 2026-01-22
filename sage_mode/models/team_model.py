from sqlalchemy import Column, BigInteger, String, Boolean, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sage_mode.database import Base

class Team(Base):
    __tablename__ = 'teams'
    id = Column(BigInteger, primary_key=True)
    name = Column(String(255), nullable=False)
    owner_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    is_shared = Column(Boolean, default=False)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Team {self.name}>"

class TeamMembership(Base):
    __tablename__ = 'team_memberships'
    id = Column(BigInteger, primary_key=True)
    team_id = Column(BigInteger, ForeignKey('teams.id'), nullable=False)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    role = Column(String(50), default='member')
    joined_at = Column(DateTime, server_default=func.now())
    __table_args__ = (UniqueConstraint('team_id', 'user_id'),)

    def __repr__(self):
        return f"<Membership team={self.team_id} user={self.user_id}>"
