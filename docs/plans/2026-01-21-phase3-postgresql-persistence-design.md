# Phase 3: PostgreSQL Persistence & Celery Distribution Design

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:writing-plans to create detailed implementation plan, then superpowers:subagent-driven-development to execute task-by-task.

**Goal:** Build production-ready PostgreSQL persistence layer, Celery distributed execution, and React dashboard for Sage Mode Development Team Simulator.

**Architecture:** PostgreSQL stores full application state (users, teams, sessions, decisions, agent snapshots). Celery distributes agent task execution across workers using session-based chains. React dashboard provides real-time team coordination with WebSocket updates. Authentication via session cookies with Redis backing.

**Tech Stack:**
- Database: PostgreSQL 14+
- Cache/Session: Redis 7+
- Task Queue: Celery 5.3+ with Redis broker
- Backend: FastAPI (expand Phase 1-2 app)
- Frontend: React 18+ with Vite
- WebSocket: Built into FastAPI
- Auth: session-cookie pattern with Flask-Session or similar
- Deployment: Docker + docker-compose

---

## Database Schema (Full State Persistence)

### Core Tables

#### users
```sql
CREATE TABLE users (
  id BIGSERIAL PRIMARY KEY,
  username VARCHAR(255) UNIQUE NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### teams (Hybrid: personal + shared)
```sql
CREATE TABLE teams (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  owner_id BIGINT NOT NULL REFERENCES users(id),
  is_shared BOOLEAN DEFAULT FALSE,
  description TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### team_memberships (Many-to-many for shared teams)
```sql
CREATE TABLE team_memberships (
  id BIGSERIAL PRIMARY KEY,
  team_id BIGINT NOT NULL REFERENCES teams(id),
  user_id BIGINT NOT NULL REFERENCES users(id),
  role VARCHAR(50) DEFAULT 'member',  -- 'owner', 'member', 'viewer'
  joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(team_id, user_id)
);
```

#### execution_sessions (Hyperfocus windows)
```sql
CREATE TABLE execution_sessions (
  id BIGSERIAL PRIMARY KEY,
  team_id BIGINT NOT NULL REFERENCES teams(id),
  user_id BIGINT NOT NULL REFERENCES users(id),
  feature_name VARCHAR(255),
  status VARCHAR(50) DEFAULT 'active',  -- 'active', 'completed', 'error'
  started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  ended_at TIMESTAMP,
  duration_seconds INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### session_decisions (Strategic, session-level)
```sql
CREATE TABLE session_decisions (
  id BIGSERIAL PRIMARY KEY,
  session_id BIGINT NOT NULL REFERENCES execution_sessions(id),
  decision_text TEXT NOT NULL,
  category VARCHAR(100),  -- 'architecture', 'technology', 'design', etc.
  confidence VARCHAR(50) DEFAULT 'high',  -- 'high', 'medium', 'low'
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### agent_tasks (Granular execution records)
```sql
CREATE TABLE agent_tasks (
  id BIGSERIAL PRIMARY KEY,
  session_id BIGINT NOT NULL REFERENCES execution_sessions(id),
  agent_role VARCHAR(100) NOT NULL,  -- 'architect', 'frontend_dev', 'backend_dev', etc.
  task_description TEXT NOT NULL,
  input_data JSONB,
  output_data JSONB,
  status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'running', 'completed', 'error'
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  duration_seconds INT,
  error_message TEXT,
  retry_count INT DEFAULT 0,
  celery_task_id VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### task_decisions (Tactical, task-level)
```sql
CREATE TABLE task_decisions (
  id BIGSERIAL PRIMARY KEY,
  agent_task_id BIGINT NOT NULL REFERENCES agent_tasks(id),
  decision_text TEXT NOT NULL,
  rationale TEXT,
  category VARCHAR(100),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### agent_snapshots (Full state at execution time)
```sql
CREATE TABLE agent_snapshots (
  id BIGSERIAL PRIMARY KEY,
  agent_task_id BIGINT NOT NULL REFERENCES agent_tasks(id),
  agent_role VARCHAR(100) NOT NULL,
  context_state JSONB NOT NULL,  -- Full context dict
  capabilities JSONB NOT NULL,   -- List of AgentCapability enums
  decisions JSONB NOT NULL,      -- All decisions guiding this agent
  execution_metadata JSONB,      -- Timing, environment info
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes for Performance
```sql
CREATE INDEX idx_teams_owner ON teams(owner_id);
CREATE INDEX idx_teams_is_shared ON teams(is_shared);
CREATE INDEX idx_memberships_user ON team_memberships(user_id);
CREATE INDEX idx_memberships_team ON team_memberships(team_id);
CREATE INDEX idx_sessions_team ON execution_sessions(team_id);
CREATE INDEX idx_sessions_user ON execution_sessions(user_id);
CREATE INDEX idx_sessions_status ON execution_sessions(status);
CREATE INDEX idx_agent_tasks_session ON agent_tasks(session_id);
CREATE INDEX idx_agent_tasks_role ON agent_tasks(agent_role);
CREATE INDEX idx_agent_tasks_status ON agent_tasks(status);
CREATE INDEX idx_snapshots_task ON agent_snapshots(agent_task_id);
```

---

## Backend Architecture (FastAPI Expansion)

### New Routes

**Authentication Routes** (`auth_routes.py`)
- `POST /auth/signup` - Register new user
- `POST /auth/login` - Create session, return cookie
- `POST /auth/logout` - Invalidate session
- `GET /auth/me` - Current user profile
- Session stored in Redis, cookie forwarded

**Team Management Routes** (`team_routes.py`)
- `GET /teams` - List user's teams (personal + shared)
- `POST /teams` - Create new team (personal by default)
- `POST /teams/{id}/share` - Convert personal team to shared
- `POST /teams/{id}/invite` - Add user to shared team
- `DELETE /teams/{id}/members/{user_id}` - Remove member from team
- Access control: Check ownership or team_memberships

**Session Routes** (`session_routes.py`)
- `POST /sessions` - Start new execution session (creates record)
- `GET /sessions/{id}` - Get session details with all decisions/tasks
- `GET /sessions/{id}/timeline` - Get ordered execution timeline
- `POST /sessions/{id}/end` - Mark session complete
- `GET /teams/{team_id}/sessions` - List all sessions for team

**Decision Routes** (`decision_routes.py`)
- `POST /sessions/{id}/decisions` - Create session-level decision
- `POST /tasks/{task_id}/decisions` - Create task-level decision
- `GET /sessions/{id}/decisions` - Get decision tree for session
- `GET /sessions/{id}/replay` - Get full replay timeline with decisions

**WebSocket Handler** (`websocket_handler.py`)
- `WS /ws/{session_id}` - Real-time session updates
- Broadcast messages:
  - `{type: "session_started", session: {...}}`
  - `{type: "agent_task_started", task: {...}}`
  - `{type: "agent_task_completed", task: {...}, snapshot: {...}}`
  - `{type: "decision_created", decision: {...}}`
  - `{type: "session_error", error: "..."}`

### Celery Task Architecture

**Task Structure:**
- Each agent role is a task type: `execute_architect_task`, `execute_frontend_task`, etc.
- Tasks receive: `session_id`, `task_description`, `context_data`
- Tasks return: `output_data` + `decisions` list

**Session Execution Chain:**
```python
@app.post("/sessions")
def start_session(team_id, feature_name):
    session = ExecutionSession.create(team_id, feature_name)

    # Build Celery chain with parallel groups
    chain = celery.chain(
        # Group 1: Architect (team lead) - always first
        execute_architect_task.s(session.id, f"Plan {feature_name}"),

        # Group 2: Backend + DBA (parallel)
        celery.group(
            execute_backend_task.s(session.id, "Implement backend"),
            execute_dba_task.s(session.id, "Design database")
        ),

        # Group 3: Frontend + UI/UX (parallel)
        celery.group(
            execute_frontend_task.s(session.id, "Implement frontend"),
            execute_ui_ux_task.s(session.id, "Design UI")
        ),

        # Group 4: Security + IT Admin (parallel)
        celery.group(
            execute_security_task.s(session.id, "Audit security"),
            execute_it_admin_task.s(session.id, "Plan deployment")
        )
    )

    # Execute and track
    result = chain.apply_async()
    session.celery_chain_id = result.id
    session.save()

    return {"session_id": session.id, "status": "starting"}
```

**Per-Agent Task:**
```python
@celery.task(bind=True, max_retries=3)
def execute_backend_task(self, session_id, task_description):
    try:
        session = ExecutionSession.get(session_id)
        task = AgentTask.create(session_id, "backend_dev", task_description)

        # Notify frontend: task started
        broadcast_websocket(session_id, {
            "type": "agent_task_started",
            "agent": "backend_dev",
            "task_id": task.id
        })

        # Execute agent
        backend_agent = BackendAgent()
        backend_agent.set_context(session.get_context())
        result = backend_agent.execute_task(task_description)

        # Save results
        task.output_data = result
        task.status = "completed"
        task.save()

        # Create task-level decision
        TaskDecision.create(task.id, result.get("decision", ""))

        # Create full snapshot
        AgentSnapshot.create(task.id, backend_agent)

        # Notify frontend: task completed
        broadcast_websocket(session_id, {
            "type": "agent_task_completed",
            "agent": "backend_dev",
            "task_id": task.id,
            "output": result,
            "snapshot": AgentSnapshot.to_dict(task)
        })

        return {"task_id": task.id, "status": "completed"}

    except Exception as exc:
        task.status = "error"
        task.error_message = str(exc)
        task.retry_count += 1
        task.save()

        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=5)  # Exponential backoff
        else:
            broadcast_websocket(session_id, {
                "type": "session_error",
                "task_id": task.id,
                "error": str(exc)
            })
            raise
```

### Error Handling

**Task timeout:** 5 minutes per agent task
**Celery retries:** 3x with 5s, 10s, 20s backoff
**Failed session:** Mark as "error", notify frontend via WebSocket
**Database failures:** Logged to stderr, session continues (best-effort)
**WebSocket disconnect:** Client reconnects, receives catch-up events via REST API

---

## React Frontend Architecture

### Component Structure
```
src/
  components/
    Auth/
      LoginForm.tsx
      SignupForm.tsx
    Team/
      TeamSelector.tsx          -- Switch personal/shared teams
      TeamList.tsx
      TeamMembers.tsx           -- Manage shared team members
    Session/
      SessionPanel.tsx          -- Start/stop sessions
      SessionHistory.tsx
    Dashboard/
      TeamExecutionMonitor.tsx  -- Real-time agent status cards
      AgentStateViewer.tsx      -- Click to inspect agent snapshot
      SessionReplay.tsx         -- Timeline replay of execution
    DecisionJournal/
      DecisionTree.tsx          -- Strategic + tactical decisions
      DecisionDetail.tsx
  hooks/
    useWebSocket.ts            -- Real-time updates
    useSession.ts              -- Session state management
    useTeam.ts                 -- Team switching
  pages/
    LoginPage.tsx
    DashboardPage.tsx
    SessionDetailsPage.tsx
```

### Real-Time Flow

1. User logs in → React connects WebSocket to `/ws/{session_id}`
2. User clicks "Start Session" → `POST /sessions`, creates DB record
3. WebSocket receives `{type: "session_started"}`
4. Frontend shows "Session active" UI
5. Celery chain executes agents (backend → parallel groups)
6. Each agent task start → WebSocket broadcasts `agent_task_started`
7. Frontend updates TeamExecutionMonitor card in real-time
8. Task completes → WebSocket broadcasts `agent_task_completed` with snapshot
9. Frontend plays animation, shows completed status
10. User can click agent card → AgentStateViewer loads snapshot from WebSocket message

### Session Replay (Timeline View)

```typescript
// Get all tasks in order
const tasks = await fetch(`/sessions/${sessionId}/timeline`).json();

// Display timeline
tasks.forEach((task, index) => {
  TimelineItem({
    agent: task.agent_role,
    status: task.status,
    startTime: task.started_at,
    duration: task.duration_seconds,
    onInspect: () => {
      // Show AgentStateViewer with task.snapshot
    }
  });
});
```

---

## Authentication & Access Control

### Session Cookie Flow

```
Client: POST /auth/login {username, password}
Server: Validate credentials, create session in Redis
Server: Set-Cookie header with session_id
Client: Store cookie, send on all subsequent requests
Server: Validate cookie on each request via Redis lookup
Client: POST /logout → Server deletes session from Redis
```

### Team Access Control

```python
def get_user_teams(user_id):
    """Get all teams user can access"""
    personal_teams = Team.where(owner_id=user_id, is_shared=False)
    shared_teams = (
        Team.join(TeamMembership)
        .where(TeamMembership.user_id=user_id, Team.is_shared=True)
    )
    return personal_teams + shared_teams

def verify_team_access(user_id, team_id):
    """Check if user can access team"""
    team = Team.get(team_id)
    if team.owner_id == user_id:
        return True  # Owner
    if team.is_shared:
        return TeamMembership.exists(user_id, team_id)
    return False
```

### Session Management

**Immediate revocation:** When user leaves shared team, invalidate all their sessions
```python
def remove_team_member(team_id, user_id):
    TeamMembership.delete(team_id, user_id)
    # Invalidate all sessions for user on this team
    sessions = ExecutionSession.where(team_id, user_id)
    for session in sessions:
        broadcast_websocket(session.id, {"type": "access_revoked"})
        # Client receives this → logs user out
```

---

## Testing Strategy (100+ Tests)

### Unit Tests (40+ tests)
- Database models: Create, read, update, delete operations
- Celery tasks: Task execution, error handling, retries
- API routes: Each endpoint returns correct data
- Auth: Login, logout, session validation

### Integration Tests (40+ tests)
- Full session execution: Start → agents execute → decisions saved
- Multi-team access: User can only see own teams and memberships
- WebSocket: Client connects, receives broadcasts during execution
- Error recovery: Failed task retries, session marks error

### Fixture Data
```python
@pytest.fixture
def user():
    return User.create(username="test", email="test@test.com")

@pytest.fixture
def personal_team(user):
    return Team.create(name="Personal", owner=user, is_shared=False)

@pytest.fixture
def shared_team(user):
    team = Team.create(name="Shared", owner=user, is_shared=True)
    TeamMembership.create(team, user, role="owner")
    return team

@pytest.fixture
def session(personal_team):
    return ExecutionSession.create(personal_team, "Test Feature")
```

---

## Deployment (Docker + docker-compose)

### docker-compose.yml Structure
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: sage_mode
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  fastapi:
    build: ./server
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://user:password@postgres/sage_mode
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis

  celery_worker:
    build: ./server
    command: celery -A sage_mode.celery_app worker -l info
    environment:
      DATABASE_URL: postgresql://user:password@postgres/sage_mode
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis

  react:
    build: ./frontend
    ports:
      - "3000:3000"
```

### Local Development
```bash
# Start all services
docker-compose up

# Run migrations
docker exec sage-mode-api alembic upgrade head

# Create test data
docker exec sage-mode-api python scripts/seed_test_data.py

# Access dashboard at http://localhost:3000
```

---

## Phase 3 Success Criteria

✅ PostgreSQL fully normalized schema (8 tables, full relational integrity)
✅ FastAPI REST + WebSocket endpoints (12+ endpoints)
✅ Celery task chains with parallel grouping
✅ React dashboard with real-time updates
✅ Session cookie auth with Redis backing
✅ 100+ integration tests, 100% passing
✅ Docker deployment ready
✅ Decision capture: session-level + task-level
✅ Agent snapshots: full state audit trail
✅ Team access control: personal + shared with membership verification

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     React Dashboard (Port 3000)             │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │ TeamSelector │  │ SessionPanel     │  │ Exec Monitor │  │
│  └──────────────┘  └──────────────────┘  └──────────────┘  │
│  ┌──────────────┐  ┌──────────────────┐                      │
│  │Decision Tree │  │ Session Replay   │  (WebSocket: /ws)   │
│  └──────────────┘  └──────────────────┘                      │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP REST + WebSocket
┌──────────────────────────▼──────────────────────────────────┐
│              FastAPI Backend (Port 8000)                    │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │ Auth Routes  │  │ Team Routes      │  │ Decision API │  │
│  └──────────────┘  └──────────────────┘  └──────────────┘  │
│  ┌──────────────┐  ┌──────────────────┐                      │
│  │ Session API  │  │ WebSocket Handler│                      │
│  └──────────────┘  └──────────────────┘                      │
│         │                    │                                │
│         ▼                    ▼                                │
│  ┌─────────────────────────────────┐                         │
│  │   Celery Task Orchestration     │                         │
│  │  (Chains + Parallel Groups)     │                         │
│  └─────────────────────────────────┘                         │
└──────────────────────┬────────────────────────────────────────┘
         │             │
         ▼             ▼
    ┌─────────┐   ┌──────────┐
    │Redis    │   │PostgreSQL│
    │         │   │          │
    │Session  │   │Users     │
    │Store    │   │Teams     │
    │Broker   │   │Sessions  │
    │         │   │Decisions │
    │         │   │Tasks     │
    │         │   │Snapshots │
    └─────────┘   └──────────┘
         │             │
         └─────┬───────┘
         Celery Workers
    (Execute Agent Tasks)
```

