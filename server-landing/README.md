# Server Landing Page

A unified server landing page featuring the Prompt Reverser image analysis interface, service links grid, and real-time server status dashboard.

## Features

- **Prompt Reverser**: Upload images to analyze and extract generation prompts for Midjourney, DALL-E, Flux, and Nano Banana
- **Service Grid**: Quick access to all running services with live status indicators
- **System Dashboard**: Real-time monitoring of CPU, memory, disk usage, and Docker containers
- **Auto-refresh**: Status updates every 30 seconds

## Tech Stack

- **Frontend**: Next.js 16.1, React 19, TypeScript, Tailwind CSS, Zustand
- **Backend**: FastAPI, Python 3.11
- **Infrastructure**: Docker, Docker Compose, Nginx

## Architecture

```
http://server:80 (nginx)
├── /                          → Next.js frontend (port 3001)
├── /api/health                → Backend health check (port 8011)
├── /api/services              → Service status endpoint
├── /api/system                → System metrics endpoint
└── /api/prompt-reverser/*     → Prompt Reverser API (port 8010)
```

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 2GB+ RAM available
- Port 80 available (system nginx should be stopped)

## Quick Start

1. **Clone and navigate to the project**:
   ```bash
   cd /home/ndninja/server-landing
   ```

2. **Configure services** (optional):
   ```bash
   cp .env.example .env
   nano .env  # Edit SERVICES_CONFIG if needed
   ```

3. **Deploy**:
   ```bash
   ./deploy.sh
   ```

4. **Access**:
   - Landing page: http://100.77.248.9:80
   - Prompt Reverser: Upload images directly on the landing page
   - System status: View metrics at the top of the page

## Network Configuration

**IMPORTANT**: This application uses the Tailscale IP `100.77.248.9` for all service URLs instead of localhost.

### Why Tailscale IP?

- **Mobile Access**: Enables access from mobile devices on the Tailscale network
- **Remote Access**: Team members can access services from anywhere
- **Consistency**: Single IP works across all contexts (local and remote)
- **Service Discovery**: Frontend knows where to find backend services

### Protection Mechanisms

The application has multiple layers to prevent localhost URLs:

1. **Runtime Validation**: App won't start if localhost URLs are detected
2. **Startup Checks**: Configuration validated on application startup
3. **Code Protection**: Hookify rules block file edits with localhost
4. **Centralized Config**: `backend/app/config.py` provides single source of truth

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development guidelines.

## Manual Deployment

If you prefer to deploy manually:

1. **Create Docker networks**:
   ```bash
   docker network create server-landing
   docker network create prompt-reverser
   ```

2. **Stop system nginx** (if running):
   ```bash
   sudo systemctl stop nginx
   sudo systemctl disable nginx
   ```

3. **Build and start containers**:
   ```bash
   docker compose build
   docker compose up -d
   ```

4. **Verify deployment**:
   ```bash
   curl http://100.77.248.9:80
   curl http://100.77.248.9:80/api/health
   ```

## Configuration

### Environment Variables

Edit `.env` to customize configuration:

- **SERVICES_CONFIG**: JSON array of services to display (see `.env.example`)
- **STATUS_CHECK_TIMEOUT**: Service health check timeout (default: 5 seconds)
- **STATUS_REFRESH_INTERVAL**: Auto-refresh interval (default: 30000ms)

### Adding Services

To add a new service to the grid, update `SERVICES_CONFIG` in `.env`:

```json
{
  "name": "My Service",
  "url": "http://100.77.248.9:3000",
  "port": 3000,
  "description": "Service description",
  "icon": "cpu"
}
```

Available icons: `shield`, `cpu`, `document`, `video`, `sparkles`, `workflow`

## Integration with Prompt Reverser

The landing page integrates with the Prompt Reverser API. Ensure Prompt Reverser is running:

1. **Navigate to Prompt Reverser**:
   ```bash
   cd /home/ndninja/projects/prompt-reverser
   ```

2. **Start Prompt Reverser**:
   ```bash
   docker compose up -d
   ```

The Prompt Reverser API will be available on port 8010 and automatically connect to the landing page.

## Management Commands

### View logs
```bash
docker compose logs -f
```

### View specific service logs
```bash
docker compose logs -f frontend
docker compose logs -f backend
docker compose logs -f nginx
```

### Restart services
```bash
docker compose restart
```

### Stop services
```bash
docker compose down
```

### Rebuild after changes
```bash
docker compose build
docker compose up -d
```

### Check service status
```bash
docker compose ps
```

## Troubleshooting

### Port 80 already in use
```bash
# Check what's using port 80
sudo lsof -i :80

# If it's system nginx
sudo systemctl stop nginx
sudo systemctl disable nginx
```

### Frontend not loading
```bash
# Check frontend logs
docker compose logs frontend

# Rebuild frontend
docker compose build frontend
docker compose up -d frontend
```

### Backend API not responding
```bash
# Check backend logs
docker compose logs backend

# Check if backend is healthy
curl http://100.77.248.9:80/api/health
```

### Prompt Reverser integration not working
```bash
# Ensure Prompt Reverser is running
cd /home/ndninja/projects/prompt-reverser
docker compose ps

# Check Prompt Reverser API
curl http://100.77.248.9:8010/api/v1/platforms

# Verify networks
docker network ls | grep -E "server-landing|prompt-reverser"
```

### Services showing as offline
1. Verify the service is actually running on the configured port
2. Check firewall rules aren't blocking the connection
3. Review backend logs: `docker compose logs backend`

## File Structure

```
server-landing/
├── docker-compose.yml         # Service orchestration
├── .env                       # Configuration
├── deploy.sh                  # Deployment script
│
├── frontend/                  # Next.js application
│   ├── app/
│   │   └── page.tsx          # Main landing page
│   ├── components/
│   │   ├── PromptReverser/   # Image upload & results
│   │   ├── ServiceGrid/      # Service cards
│   │   └── ServerStatus/     # System metrics
│   ├── lib/
│   │   ├── api.ts            # API client
│   │   └── types.ts          # TypeScript types
│   ├── stores/               # Zustand state management
│   └── Dockerfile
│
├── backend/                   # FastAPI application
│   ├── app/
│   │   ├── main.py           # API endpoints
│   │   ├── services.py       # Service checker
│   │   ├── system.py         # System metrics
│   │   └── models.py         # Pydantic models
│   ├── requirements.txt
│   └── Dockerfile
│
└── nginx/                     # Nginx reverse proxy
    ├── nginx.conf
    └── Dockerfile
```

## API Endpoints

### Backend API (Port 8011)

- `GET /health` - Health check with uptime
- `GET /services` - Service status array
- `GET /system` - System metrics (CPU, memory, disk, containers)

### Prompt Reverser API (Port 8010)

- `GET /api/v1/platforms` - List available platforms
- `POST /api/v1/analyze` - Synchronous image analysis
- `POST /api/v1/analyze/async` - Asynchronous analysis (returns job_id)
- `GET /api/v1/analyze/{job_id}` - Poll job status

## Development

### Frontend Development
```bash
cd frontend
npm run dev
# Access at http://100.77.248.9:3001
```

### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8011
```

### Hot Reload in Docker
For development with hot reload, update `docker-compose.yml` to mount source directories as volumes.

## Production Deployment

For production deployment:

1. Set `NODE_ENV=production` in frontend environment
2. Update CORS origins in `backend/app/main.py`
3. Configure proper SSL/TLS certificates
4. Set up proper logging and monitoring
5. Configure firewall rules

## Rollback

To rollback to system nginx:

```bash
# Stop server-landing
cd /home/ndninja/server-landing
docker compose down

# Restore system nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Revert Prompt Reverser port (if needed)
cd /home/ndninja/projects/prompt-reverser
# Edit docker-compose.yml: change api port back to 8000:8000
# Remove server-landing network from api service
docker compose down
docker compose up -d
```

## License

MIT

## Support

For issues or questions, check the logs with `docker compose logs -f` or review the troubleshooting section above.
