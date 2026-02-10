# Production Hardening: Security Design

**Date:** 2026-01-22
**Status:** Approved
**Scope:** Self-hosted deployment, small team support

## Overview

This design addresses security hardening for Sage Mode production deployment. The current implementation has several security gaps that need to be addressed before production use.

### Current Issues

- CORS allows all origins (`*`)
- Routes have no auth protection middleware
- Session cookies lack `Secure` and `SameSite` flags
- No rate limiting (vulnerable to brute force)
- Hardcoded/missing configuration (no `.env` structure)
- No CSRF protection

## Architecture

```
┌─────────────────────────────────────────────┐
│              Rate Limiter                    │
│         (slowapi - per IP/user)             │
├─────────────────────────────────────────────┤
│            CORS Middleware                   │
│      (configurable allowed origins)          │
├─────────────────────────────────────────────┤
│          Auth Middleware                     │
│   (JWT tokens, protected route decorator)    │
├─────────────────────────────────────────────┤
│            Route Handlers                    │
│     (input validation via Pydantic)          │
└─────────────────────────────────────────────┘
```

## JWT Authentication

### Why JWT over Cookie Sessions

- Stateless - no server-side session storage needed
- Works well with API clients and mobile apps
- Easy to include in Authorization header
- Can embed user claims (id, team_id, role)

### Token Structure

```python
# Access Token Payload (short-lived: 15 min)
{
    "sub": "user_id",
    "team_id": "team_id or null",
    "role": "admin|member",
    "exp": "expiration timestamp",
    "type": "access"
}

# Refresh Token Payload (long-lived: 7 days)
{
    "sub": "user_id",
    "exp": "expiration timestamp",
    "type": "refresh"
}
```

### Auth Flow

1. Login → Returns `access_token` + `refresh_token`
2. API calls → Include `Authorization: Bearer <access_token>`
3. Token expires → Call `/auth/refresh` with refresh token
4. Logout → Client discards tokens

## Route Protection

### Auth Dependency Levels

1. `require_auth` - Any authenticated user
2. `require_admin` - Must have admin role
3. `require_team_member(team_id)` - Must belong to specific team

### Route Protection Matrix

| Route | Protection |
|-------|------------|
| `POST /auth/signup` | Public (rate limited) |
| `POST /auth/login` | Public (rate limited) |
| `POST /auth/refresh` | Public (has refresh token) |
| `GET /auth/me` | `require_auth` |
| `GET /sessions/*` | `require_auth` |
| `POST /sessions/*` | `require_auth` |
| `GET /teams/*` | `require_auth` |
| `DELETE /teams/*` | `require_admin` |
| `GET /dashboard/*` | `require_auth` |
| `GET /health` | Public |

### Error Responses

- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Valid token but insufficient permissions

## Rate Limiting

Using `slowapi` (built on `limits`, integrates with FastAPI).

### Rate Limit Tiers

| Endpoint Type | Limit | Rationale |
|---------------|-------|-----------|
| Auth endpoints (login/signup) | 5 req/min per IP | Prevent brute force |
| Auth refresh | 10 req/min per IP | Slightly more lenient |
| API reads (GET) | 60 req/min per user | Normal usage |
| API writes (POST/PUT/DELETE) | 30 req/min per user | Prevent abuse |
| LLM endpoints | 10 req/min per user | Cost control (Claude API) |

### Response on Limit Exceeded

- Status: `429 Too Many Requests`
- Header: `Retry-After` with seconds until reset
- Body: `{"detail": "Rate limit exceeded", "retry_after": 45}`

## Environment Configuration

### Pydantic Settings

```python
class SecuritySettings(BaseSettings):
    # JWT (required)
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Rate Limiting
    rate_limit_enabled: bool = True

    # Database
    database_url: str = "postgresql://localhost/sage_mode"

    # Redis
    redis_url: str = "redis://localhost:6379"

    class Config:
        env_file = ".env"
```

### Environment Files

```
├── .env.example      # Template (committed)
├── .env              # Actual secrets (gitignored)
├── .env.production   # Production overrides (gitignored)
```

### .env.example Template

```bash
# === REQUIRED ===
JWT_SECRET_KEY=generate-with-openssl-rand-hex-32

# === DATABASE ===
DATABASE_URL=postgresql://user:pass@localhost:5432/sage_mode

# === REDIS ===
REDIS_URL=redis://localhost:6379

# === OPTIONAL ===
CORS_ORIGINS=["http://localhost:3000"]
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
RATE_LIMIT_ENABLED=true

# === LLM ===
ANTHROPIC_API_KEY=sk-ant-...
```

## Security Headers

All responses include:

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
```

## Password Requirements

- Minimum 8 characters
- At least one letter and one number

## Implementation Plan

### New Files

```
sage_mode/security/
├── __init__.py
├── config.py          # Pydantic Settings
├── jwt.py             # Token create/verify
├── dependencies.py    # require_auth, require_admin
├── middleware.py      # Security headers
└── rate_limit.py      # Slowapi setup
```

### Files to Modify

- `sage_mode/main.py` - Add middleware, rate limiter
- `sage_mode/routes/auth_routes.py` - JWT flow, password validation
- `sage_mode/routes/session_routes.py` - Add auth dependencies
- `sage_mode/routes/team_routes.py` - Add auth dependencies
- `sage_mode/routes/dashboard_routes.py` - Add auth dependencies
- `requirements.txt` - Add dependencies
- `.gitignore` - Ensure `.env` excluded

### New Dependencies

- `python-jose[cryptography]` - JWT handling
- `slowapi` - Rate limiting

### Test Coverage

- JWT token creation/validation
- Auth middleware (valid/invalid/expired tokens)
- Rate limiting triggers
- Protected route access
