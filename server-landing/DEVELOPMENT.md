# Server Landing Page - Development Guide

This guide explains the development setup, architecture, and important conventions for the server landing page project.

## Table of Contents

- [Network Configuration](#network-configuration)
- [Architecture](#architecture)
- [Development Setup](#development-setup)
- [Protection Mechanisms](#protection-mechanisms)
- [Adding New Services](#adding-new-services)
- [Troubleshooting](#troubleshooting)

## Network Configuration

### Tailscale IP Requirement

**CRITICAL**: All service URLs MUST use the Tailscale IP `100.77.248.9` instead of localhost.

#### Why?

- **Mobile Access**: Mobile apps need to connect to services from remote devices
- **Team Access**: Remote team members access services via Tailscale network
- **Network Consistency**: Single IP address works across all contexts
- **Service Discovery**: Frontend knows where to find services

#### Wrong vs Right

```bash
# ❌ WRONG - Will not work from mobile/remote
http://localhost:8888
http://127.0.0.1:8888

# ✅ CORRECT - Works everywhere on Tailscale network
http://100.77.248.9:8888
```

### Docker Network Architecture

When running in Docker, two IPs are relevant:

1. **Tailscale IP (100.77.248.9)**: Used for service URLs shown to users
2. **Docker Gateway (172.23.0.1)**: Used internally for status checks from backend container to host services

## Architecture

### Backend (FastAPI)

```
backend/
├── app/
│   ├── main.py          # FastAPI app with startup validation
│   ├── config.py        # Centralized network configuration
│   ├── services.py      # Service loading and status checks
│   ├── validators.py    # Localhost URL detection and blocking
│   ├── models.py        # Pydantic models
│   └── system.py        # System metrics collection
```

**Key Files:**

- `config.py`: Single source of truth for `TAILSCALE_IP` and network configuration
- `validators.py`: Runtime validation to prevent localhost URLs
- `main.py`: Startup validation ensures app won't run with invalid config

### Frontend (Next.js)

```
frontend/
├── app/                 # Next.js app directory
├── components/          # React components
└── lib/
    └── api.ts          # API client (must use Tailscale IP)
```

## Development Setup

### Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

**Important**: The `.env` file should already have correct Tailscale IPs. Never change URLs to localhost.

### Running Locally

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f backend

# Rebuild after changes
docker compose build
docker compose up -d
```

### Verification

After starting services:

```bash
# Check backend started successfully
curl http://100.77.248.9:80/api/services | jq

# Verify all URLs use Tailscale IP
curl -s http://100.77.248.9:80/api/services | jq '.[].url'
# Should output only http://100.77.248.9:* URLs
```

## Protection Mechanisms

This project has **6 layers of protection** to prevent localhost URLs:

### Layer 1: Centralized Configuration

`backend/app/config.py` provides:
- `TAILSCALE_IP` constant
- `get_service_url(port)` function
- `get_status_check_host()` function

**Always use these helpers** instead of hardcoding IPs.

### Layer 2: Runtime Validation

`backend/app/validators.py` validates:
- Environment variable `SERVICES_CONFIG`
- Parsed service objects
- Default services

If localhost URLs are detected, the app **refuses to start**.

### Layer 3: Startup Validation

`main.py` validates configuration on startup:

```python
@app.on_event("startup")
async def validate_configuration():
    """Validate configuration on startup to ensure no localhost URLs."""
    try:
        services = load_services_config()
        print(f"✓ Configuration validated: {len(services)} services loaded")
    except LocalhostDetectionError as e:
        print(str(e))
        sys.exit(1)
```

**Result**: Application cannot start with localhost URLs.

### Layer 4: Hookify Rules (Claude Code)

Four hookify rules protect files:

1. `hookify.localhost-in-files.local.md` - Blocks localhost in any file edit
2. `hookify.protect-env-files.local.md` - Protects `.env` files specifically
3. `hookify.protect-services-py.local.md` - Protects `services.py` specifically
4. `hookify.use-tailscale-ip.local.md` - Verification checklist on session end

**Result**: Claude Code cannot accidentally introduce localhost URLs.

### Layer 5: Documentation

This file and README.md explain why Tailscale IP is required.

### Layer 6: Code Review

When reviewing PRs, verify no localhost URLs were introduced.

## Adding New Services

### Method 1: Environment Variable (Recommended)

Edit `.env` file:

```bash
SERVICES_CONFIG=[
  {
    "name": "My New Service",
    "url": "http://100.77.248.9:9999",
    "port": 9999,
    "description": "Description of service",
    "icon": "cpu"
  },
  # ... other services
]
```

**IMPORTANT**: Always use `100.77.248.9`, never `localhost`.

### Method 2: Update Default Services

Edit `backend/app/services.py`:

```python
def get_default_services() -> List[ServiceInfo]:
    """Return default services configuration."""
    services = [
        # ... existing services ...
        ServiceInfo(
            name="My New Service",
            url=get_service_url(9999),  # ✅ Use helper function
            port=9999,
            description="Description",
            icon="cpu"
        ),
    ]
    validate_services(services)
    return services
```

**NEVER hardcode URLs** - always use `get_service_url(port)`.

## Troubleshooting

### Application Won't Start

**Error**: `FATAL ERROR: Localhost URL detected`

**Cause**: Configuration contains localhost URLs

**Fix**:
```bash
# Check .env file
grep localhost .env

# Replace with Tailscale IP
sed -i 's/localhost/100.77.248.9/g' .env

# Restart
docker compose restart backend
```

### Services Show as Offline

**Symptom**: All services show red/offline status

**Causes**:
1. Services not actually running on host
2. Docker network misconfigured
3. Firewall blocking connections

**Debug**:
```bash
# Check if services are running on host
netstat -tlnp | grep :8888

# Check Docker can reach host
docker compose exec backend ping -c 3 172.23.0.1

# Check backend logs
docker compose logs backend
```

### Frontend Can't Connect to Backend

**Symptom**: Frontend shows loading forever or errors

**Cause**: API URL might be wrong

**Fix**:
```bash
# Verify backend is accessible
curl http://100.77.248.9:80/api/services

# Check frontend API configuration
grep -r "localhost" frontend/lib/
# Should return nothing or only comments
```

### Claude Code Blocks My Edit

**Message**: `⛔ BLOCKED: Localhost URL detected`

**This is intentional!** You're trying to add a localhost URL.

**Fix**: Use `100.77.248.9` instead:
```bash
# Wrong
http://localhost:8888

# Correct
http://100.77.248.9:8888
```

## Best Practices

1. **Never hardcode IPs** - Use `get_service_url(port)` from `config.py`
2. **Always use Tailscale IP** - Never use localhost in production config
3. **Run validation** - Before committing, run:
   ```bash
   grep -ri "localhost" .env .env.example backend/app/services.py
   # Should return nothing
   ```
4. **Test deployment** - After changes, verify:
   ```bash
   curl http://100.77.248.9:80/api/services | jq '.[].url'
   # All URLs should be http://100.77.248.9:*
   ```

## Getting Help

If you encounter issues:

1. Check this guide first
2. Verify protection mechanisms are working
3. Run verification commands from README
4. Check Docker logs: `docker compose logs`

## Development Workflow

1. Make changes to code
2. Run `docker compose build` if needed
3. Run `docker compose up -d`
4. Check logs: `docker compose logs -f backend`
5. Verify services: `curl http://100.77.248.9:80/api/services`
6. Test frontend: Open `http://100.77.248.9:80`

## Security Notes

- The Tailscale IP is only accessible on your Tailscale network
- Services are not exposed to the public internet
- Only devices on your Tailscale network can access services
- Use Tailscale ACLs to further restrict access if needed
