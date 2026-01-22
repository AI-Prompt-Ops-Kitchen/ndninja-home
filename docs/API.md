# Sage Mode API Reference

Base URL: `http://localhost:8000`

## Authentication

All endpoints except `/auth/signup` and `/auth/login` require authentication via session cookie.

### POST /auth/signup

Register a new user.

**Request**
```json
{
  "username": "developer",
  "email": "dev@example.com",
  "password": "securepassword"
}
```

**Response** `200 OK`
```json
{
  "id": 1,
  "username": "developer",
  "email": "dev@example.com"
}
```

**Errors**
- `400` - User already exists

---

### POST /auth/login

Authenticate and receive session cookie.

**Request**
```json
{
  "username": "developer",
  "password": "securepassword"
}
```

**Response** `200 OK`
```json
{
  "session_id": "abc123...",
  "user_id": 1
}
```

Sets `session_id` cookie (httponly).

**Errors**
- `401` - Invalid credentials

---

### GET /auth/me

Get current authenticated user.

**Response** `200 OK`
```json
{
  "id": 1,
  "username": "developer",
  "email": "dev@example.com"
}
```

**Errors**
- `401` - Not authenticated

---

### POST /auth/logout

End current session.

**Response** `200 OK`
```json
{
  "message": "Logged out"
}
```

---

## Teams

### POST /teams

Create a new team.

**Request**
```json
{
  "name": "Frontend Team",
  "description": "UI/UX focused development"
}
```

**Response** `200 OK`
```json
{
  "id": 1,
  "name": "Frontend Team",
  "is_shared": false,
  "owner_id": 1
}
```

---

### GET /teams

List all accessible teams (owned + member of).

**Response** `200 OK`
```json
[
  {
    "id": 1,
    "name": "Frontend Team",
    "is_shared": false,
    "owner_id": 1
  }
]
```

---

### GET /teams/{team_id}

Get team details.

**Response** `200 OK`
```json
{
  "id": 1,
  "name": "Frontend Team",
  "is_shared": false,
  "owner_id": 1
}
```

**Errors**
- `403` - Access denied
- `404` - Team not found

---

### PUT /teams/{team_id}

Update team (owner only).

**Request**
```json
{
  "name": "Updated Name",
  "description": "New description",
  "is_shared": true
}
```

All fields optional.

**Response** `200 OK`
```json
{
  "id": 1,
  "name": "Updated Name",
  "is_shared": true,
  "owner_id": 1
}
```

**Errors**
- `403` - Only owner can update
- `404` - Team not found

---

### DELETE /teams/{team_id}

Delete team (owner only).

**Response** `200 OK`
```json
{
  "message": "Team deleted successfully"
}
```

**Errors**
- `403` - Only owner can delete
- `404` - Team not found

---

### POST /teams/{team_id}/invite

Add user to shared team.

**Request**
```json
{
  "user_id": 2
}
```

**Response** `200 OK`
```json
{
  "message": "User john added to team"
}
```

**Errors**
- `400` - Team not shared / User already member
- `403` - Only owner can invite
- `404` - Team or user not found

---

## Sessions

### POST /sessions

Start a new execution session.

**Request**
```json
{
  "team_id": 1,
  "feature_name": "User Authentication"
}
```

**Response** `200 OK`
```json
{
  "id": 1,
  "team_id": 1,
  "user_id": 1,
  "feature_name": "User Authentication",
  "status": "active",
  "started_at": "2024-01-20T10:00:00",
  "ended_at": null,
  "duration_seconds": null
}
```

**Errors**
- `403` - Access denied to team

---

### GET /sessions

List user's execution sessions.

**Response** `200 OK`
```json
[
  {
    "id": 1,
    "team_id": 1,
    "user_id": 1,
    "feature_name": "User Authentication",
    "status": "active",
    "started_at": "2024-01-20T10:00:00",
    "ended_at": null,
    "duration_seconds": null
  }
]
```

---

### GET /sessions/{session_id}

Get session details.

**Response** `200 OK`
```json
{
  "id": 1,
  "team_id": 1,
  "user_id": 1,
  "feature_name": "User Authentication",
  "status": "active",
  "started_at": "2024-01-20T10:00:00",
  "ended_at": null,
  "duration_seconds": null
}
```

**Errors**
- `403` - Access denied
- `404` - Session not found

---

### PUT /sessions/{session_id}/complete

Mark session as completed.

**Response** `200 OK`
```json
{
  "id": 1,
  "team_id": 1,
  "user_id": 1,
  "feature_name": "User Authentication",
  "status": "completed",
  "started_at": "2024-01-20T10:00:00",
  "ended_at": "2024-01-20T12:30:00",
  "duration_seconds": 9000
}
```

**Errors**
- `403` - Access denied
- `404` - Session not found

---

### POST /sessions/{session_id}/decisions

Add decision to session.

**Request**
```json
{
  "decision_text": "Use JWT for authentication",
  "category": "architecture",
  "confidence": "high"
}
```

`category` and `confidence` are optional.

**Response** `200 OK`
```json
{
  "id": 1,
  "session_id": 1,
  "decision_text": "Use JWT for authentication",
  "category": "architecture",
  "confidence": "high",
  "created_at": "2024-01-20T10:15:00"
}
```

---

### GET /sessions/{session_id}/decisions

List session decisions.

**Response** `200 OK`
```json
[
  {
    "id": 1,
    "session_id": 1,
    "decision_text": "Use JWT for authentication",
    "category": "architecture",
    "confidence": "high",
    "created_at": "2024-01-20T10:15:00"
  }
]
```

---

### GET /sessions/{session_id}/tasks

List agent tasks for session.

**Response** `200 OK`
```json
[
  {
    "id": 1,
    "session_id": 1,
    "agent_role": "backend_developer",
    "task_description": "Implement JWT authentication",
    "status": "completed",
    "started_at": "2024-01-20T10:20:00",
    "completed_at": "2024-01-20T10:45:00",
    "duration_seconds": 1500,
    "error_message": null,
    "created_at": "2024-01-20T10:20:00"
  }
]
```

---

## Dashboard

### GET /dashboard

Dashboard overview with statistics.

**Response** `200 OK`
```json
{
  "status": "healthy",
  "version": "3.0",
  "total_teams": 3,
  "total_sessions": 15,
  "total_decisions": 47
}
```

---

### GET /dashboard/teams/{team_id}/stats

Get team statistics.

**Response** `200 OK`
```json
{
  "team_id": 1,
  "team_name": "Frontend Team",
  "total_sessions": 5,
  "active_sessions": 1,
  "completed_sessions": 4,
  "total_decisions": 23
}
```

---

### GET /dashboard/teams/{team_id}/decisions

Get recent decisions for team.

**Query Parameters**
- `limit` (optional, default: 20)

**Response** `200 OK`
```json
[
  {
    "id": 1,
    "decision_text": "Use React Query for data fetching",
    "category": "frontend",
    "confidence": "high",
    "session_feature": "User Dashboard",
    "created_at": "2024-01-20T14:30:00"
  }
]
```

---

### GET /dashboard/teams/{team_id}/agents

Get agent task statistics for team.

**Response** `200 OK`
```json
[
  {
    "agent_role": "backend_developer",
    "total_tasks": 12,
    "pending_tasks": 1,
    "completed_tasks": 10,
    "failed_tasks": 1,
    "avg_duration_seconds": 450.5
  }
]
```

---

## WebSocket

### WS /ws/sessions/{session_id}

Real-time session updates.

**Connection**
```
ws://localhost:8000/ws/sessions/1?token=SESSION_COOKIE_VALUE
```

**Message Types**

*Connected*
```json
{
  "type": "connected",
  "session_id": 1,
  "user_id": 1
}
```

*Task Started*
```json
{
  "type": "task_started",
  "task_id": 1,
  "agent_role": "backend_developer"
}
```

*Task Completed*
```json
{
  "type": "task_completed",
  "task_id": 1,
  "agent_role": "backend_developer",
  "result": {...}
}
```

*Decision Made*
```json
{
  "type": "decision_made",
  "decision_id": 1,
  "decision_text": "Use PostgreSQL for storage"
}
```

*Session Completed*
```json
{
  "type": "session_completed",
  "session_id": 1,
  "duration_seconds": 3600
}
```

**Ping/Pong**
```json
// Send
{"type": "ping"}
// Receive
{"type": "pong"}
```

**Connection Close Codes**
- `4001` - Unauthorized

---

## Health Check

### GET /health

Service health status.

**Response** `200 OK`
```json
{
  "status": "healthy",
  "version": "3.0"
}
```
