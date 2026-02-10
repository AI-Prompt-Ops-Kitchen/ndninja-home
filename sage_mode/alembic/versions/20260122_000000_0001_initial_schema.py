"""Initial schema - baseline migration.

Revision ID: 0001
Revises:
Create Date: 2026-01-22

Creates all tables for Sage Mode application:
- users
- teams
- team_memberships
- execution_sessions
- session_decisions
- agent_tasks
- task_decisions
- agent_snapshots
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables."""
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('username', sa.String(255), unique=True, nullable=False),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Teams table
    op.create_table(
        'teams',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('owner_id', sa.BigInteger(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('is_shared', sa.Boolean(), default=False),
        sa.Column('description', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Team memberships table
    op.create_table(
        'team_memberships',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('team_id', sa.BigInteger(), sa.ForeignKey('teams.id'), nullable=False),
        sa.Column('user_id', sa.BigInteger(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('role', sa.String(50), default='member'),
        sa.Column('joined_at', sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('team_id', 'user_id'),
    )

    # Execution sessions table
    op.create_table(
        'execution_sessions',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('team_id', sa.BigInteger(), sa.ForeignKey('teams.id'), nullable=False),
        sa.Column('user_id', sa.BigInteger(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('feature_name', sa.String(255)),
        sa.Column('status', sa.String(50), default='active'),
        sa.Column('started_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('ended_at', sa.DateTime()),
        sa.Column('duration_seconds', sa.Integer()),
        sa.Column('celery_chain_id', sa.String(255)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Session decisions table
    op.create_table(
        'session_decisions',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('session_id', sa.BigInteger(), sa.ForeignKey('execution_sessions.id'), nullable=False),
        sa.Column('decision_text', sa.Text(), nullable=False),
        sa.Column('category', sa.String(100)),
        sa.Column('confidence', sa.String(50), default='high'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Agent tasks table
    op.create_table(
        'agent_tasks',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('session_id', sa.BigInteger(), sa.ForeignKey('execution_sessions.id'), nullable=False),
        sa.Column('agent_role', sa.String(100), nullable=False),
        sa.Column('task_description', sa.Text(), nullable=False),
        sa.Column('input_data', sa.JSON()),
        sa.Column('output_data', sa.JSON()),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('started_at', sa.DateTime()),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('duration_seconds', sa.Integer()),
        sa.Column('error_message', sa.Text()),
        sa.Column('retry_count', sa.Integer(), default=0),
        sa.Column('celery_task_id', sa.String(255)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Task decisions table
    op.create_table(
        'task_decisions',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('agent_task_id', sa.BigInteger(), sa.ForeignKey('agent_tasks.id'), nullable=False),
        sa.Column('decision_text', sa.Text(), nullable=False),
        sa.Column('rationale', sa.Text()),
        sa.Column('category', sa.String(100)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Agent snapshots table
    op.create_table(
        'agent_snapshots',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('agent_task_id', sa.BigInteger(), sa.ForeignKey('agent_tasks.id'), nullable=False),
        sa.Column('agent_role', sa.String(100), nullable=False),
        sa.Column('context_state', sa.JSON(), nullable=False),
        sa.Column('capabilities', sa.JSON(), nullable=False),
        sa.Column('decisions', sa.JSON(), nullable=False),
        sa.Column('execution_metadata', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    """Drop all tables in reverse order."""
    op.drop_table('agent_snapshots')
    op.drop_table('task_decisions')
    op.drop_table('agent_tasks')
    op.drop_table('session_decisions')
    op.drop_table('execution_sessions')
    op.drop_table('team_memberships')
    op.drop_table('teams')
    op.drop_table('users')
