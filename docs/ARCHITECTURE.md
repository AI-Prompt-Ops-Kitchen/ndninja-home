# Sage Mode Architecture

## High-Level Overview

Sage Mode is a multi-agent development team simulator built on a microservices architecture. It orchestrates 7 specialized AI agents that collaborate on software development tasks, with a FastAPI backend handling API requests and Celery managing distributed task execution.

```
+-------------------+     +-------------------+     +-------------------+
|                   |     |                   |     |                   |
|   React Frontend  |<--->|   FastAPI Backend |<--->|    PostgreSQL     |
|   (Vite + TS)     |     |   (REST + WS)     |     |    (Database)     |
|                   |     |                   |     |                   |
+-------------------+     +--------+----------+     +-------------------+
                                   |
                                   v
                         +-------------------+
                         |                   |
                         |   Redis           |
                         |   (Broker/Cache)  |
                         |                   |
                         +--------+----------+
                                   |
                    +--------------+--------------+
                    |                             |
           +--------v--------+           +--------v--------+
           |                 |           |                 |
           |  Celery Worker  |           |  Celery Beat    |
           |  (Agent Tasks)  |           |  (Scheduler)    |
           |                 |           |                 |
           +-----------------+           +-----------------+
```

## Component Architecture

### Frontend (React)

```
frontend/src/
  components/
    auth/          # Login, signup forms
    teams/         # Team management UI
    sessions/      # Session execution views
    dashboard/     # Analytics and stats
  pages/           # Route-level components
  api/             # Axios API client
  hooks/           # Custom React hooks (useAuth, useTeams, etc.)
  context/         # AuthContext, SessionContext
```

The frontend uses:
- **React Router** for SPA navigation
- **Axios** for HTTP requests with automatic cookie handling
- **Tailwind CSS** for utility-first styling
- **Vitest** for unit testing

### Backend (FastAPI)

```
sage_mode/
  main.py          # FastAPI app with CORS and router setup
  database.py      # SQLAlchemy engine and session factory
  celery_app.py    # Celery application instance
  celery_config.py # Celery settings (broker, queues, retries)

  routes/
    auth_routes.py       # POST /auth/signup, login, logout, GET /me
    team_routes.py       # CRUD /teams, POST /teams/{id}/invite
    session_routes.py    # CRUD /sessions, decisions, tasks
    dashboard_routes.py  # GET /dashboard stats
    websocket_routes.py  # WS /ws/sessions/{id}

  models/
    user_model.py        # User entity
    team_model.py        # Team, TeamMembership
    session_model.py     # ExecutionSession, SessionDecision
    task_model.py        # AgentTask, TaskDecision, AgentSnapshot

  services/
    user_service.py      # Password hashing, user operations
    session_service.py   # Redis session management
    execution_service.py # Session orchestration

  agents/
    base_agent.py                # Abstract agent with capabilities
    architect_agent.py           # Software Architect
    frontend_agent.py            # Frontend Developer
    backend_agent.py             # Backend Developer
    ui_ux_designer_agent.py      # UI/UX Designer
    dba_agent.py                 # Database Administrator
    it_admin_agent.py            # IT Administrator
    security_specialist_agent.py # Security Specialist

  tasks/
    agent_tasks.py      # Celery task: execute_agent_task
    orchestration.py    # Celery chain orchestration
    snapshots.py        # Agent state snapshot tasks
```

### Agent System

Each agent inherits from `BaseAgent` and implements:

```python
class BaseAgent(ABC):
    role: AgentRole              # Enum identifying agent type
    name: str                    # Display name
    description: str             # Role description
    context: Dict[str, Any]      # Execution context
    decisions: List[Decision]    # Decisions made during execution
    capabilities: List[Capability]  # What the agent can do

    @abstractmethod
    def execute_task(self, task_description: str) -> Dict[str, Any]:
        pass
```

**Agent Capabilities by Role:**

| Agent | Capabilities |
|-------|--------------|
| Architect | Design, Review, Document |
| Frontend Dev | Design, Implement, Test, Review |
| Backend Dev | Implement, Test, Review, Optimize |
| UI/UX Designer | Design, Review, Document |
| DBA | Design, Implement, Optimize, Audit |
| IT Admin | Deploy, Audit, Optimize |
| Security Specialist | Audit, Review, Document |

### Task Queue (Celery)

Tasks are routed to dedicated queues:

```python
task_routes = {
    "sage_mode.tasks.agent_tasks.*": {"queue": "agents"},
    "sage_mode.tasks.orchestration.*": {"queue": "orchestration"},
}
```

Task execution flow:
1. API creates `AgentTask` record in database
2. Celery task `execute_agent_task` is queued
3. Worker picks up task, instantiates appropriate agent
4. Agent executes with context, stores decisions
5. Result and status updated in database
6. WebSocket broadcast notifies connected clients

## Data Flow

### Session Execution

```
1. User starts session via POST /sessions
   |
   v
2. Backend creates ExecutionSession record
   |
   v
3. AgentTask records created for each agent
   |
   v
4. Celery tasks queued for parallel execution
   |
   v
5. Workers execute agents, store results
   |
   v
6. WebSocket broadcasts progress to clients
   |
   v
7. User completes session via PUT /sessions/{id}/complete
```

### Authentication Flow

```
1. POST /auth/signup - Create user with hashed password
2. POST /auth/login - Verify credentials, create Redis session
3. Session ID stored in httponly cookie
4. Subsequent requests validated via cookie -> Redis lookup
5. POST /auth/logout - Delete Redis session, clear cookie
```

## Database Schema

```
users
  id BIGINT PK
  username VARCHAR(255) UNIQUE
  email VARCHAR(255) UNIQUE
  password_hash VARCHAR(255)
  created_at TIMESTAMP
  updated_at TIMESTAMP

teams
  id BIGINT PK
  name VARCHAR(255)
  owner_id BIGINT FK -> users.id
  is_shared BOOLEAN
  description TEXT
  created_at TIMESTAMP
  updated_at TIMESTAMP

team_memberships
  id BIGINT PK
  team_id BIGINT FK -> teams.id
  user_id BIGINT FK -> users.id
  role VARCHAR(50)
  joined_at TIMESTAMP
  UNIQUE(team_id, user_id)

execution_sessions
  id BIGINT PK
  team_id BIGINT FK -> teams.id
  user_id BIGINT FK -> users.id
  feature_name VARCHAR(255)
  status VARCHAR(50)
  started_at TIMESTAMP
  ended_at TIMESTAMP
  duration_seconds INTEGER
  celery_chain_id VARCHAR(255)
  created_at TIMESTAMP

session_decisions
  id BIGINT PK
  session_id BIGINT FK -> execution_sessions.id
  decision_text TEXT
  category VARCHAR(100)
  confidence VARCHAR(50)
  created_at TIMESTAMP

agent_tasks
  id BIGINT PK
  session_id BIGINT FK -> execution_sessions.id
  agent_role VARCHAR(100)
  task_description TEXT
  input_data JSON
  output_data JSON
  status VARCHAR(50)
  started_at TIMESTAMP
  completed_at TIMESTAMP
  duration_seconds INTEGER
  error_message TEXT
  retry_count INTEGER
  celery_task_id VARCHAR(255)
  created_at TIMESTAMP

task_decisions
  id BIGINT PK
  agent_task_id BIGINT FK -> agent_tasks.id
  decision_text TEXT
  rationale TEXT
  category VARCHAR(100)
  created_at TIMESTAMP

agent_snapshots
  id BIGINT PK
  agent_task_id BIGINT FK -> agent_tasks.id
  agent_role VARCHAR(100)
  context_state JSON
  capabilities JSON
  decisions JSON
  execution_metadata JSON
  created_at TIMESTAMP
```

**Key Indexes:**
- `idx_teams_owner` - teams.owner_id
- `idx_sessions_team` - execution_sessions.team_id
- `idx_sessions_status` - execution_sessions.status
- `idx_agent_tasks_session` - agent_tasks.session_id
- `idx_agent_tasks_status` - agent_tasks.status

## Technology Choices

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Backend Framework | FastAPI | Async support, automatic OpenAPI docs, Pydantic validation |
| ORM | SQLAlchemy 2.0 | Mature, async support, migration via Alembic |
| Task Queue | Celery + Redis | Distributed execution, retries, monitoring |
| Database | PostgreSQL | JSON support, robust transactions, proven reliability |
| Frontend | React + TypeScript | Type safety, component ecosystem, Vite dev experience |
| Styling | Tailwind CSS | Utility-first, rapid prototyping, small bundle size |
| Containerization | Docker Compose | Consistent dev/prod environments, easy orchestration |

## Security Considerations

- Passwords hashed with bcrypt (via passlib)
- Session tokens stored in Redis with expiration
- httponly cookies prevent XSS token theft
- CORS configured for frontend origin
- Database queries use ORM to prevent SQL injection
- Non-root user in Docker containers
