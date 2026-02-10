# Sage Mode Deployment Guide

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum (8GB recommended for multiple Celery workers)
- Ports 3000, 5432, 6379, 8000 available

## Quick Docker Deployment

```bash
# Clone repository
git clone <repository-url>
cd sage-mode-framework

# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps

# Check logs
docker-compose logs -f
```

Services will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Environment Variables

### Backend (FastAPI + Celery)

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://sage_user:sage_password@postgres:5432/sage_mode` | PostgreSQL connection string |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection string |
| `CELERY_BROKER_URL` | Same as REDIS_URL | Celery message broker |
| `CELERY_RESULT_BACKEND` | Same as REDIS_URL | Celery result storage |
| `PYTHONPATH` | `/app` | Python module path |
| `ENV` | `development` | Environment mode |

### Frontend (React)

| Variable | Default | Description |
|----------|---------|-------------|
| `NODE_ENV` | `development` | Node environment |
| `VITE_API_URL` | `http://localhost:8000` | Backend API URL |

### PostgreSQL

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_DB` | `sage_mode` | Database name |
| `POSTGRES_USER` | `sage_user` | Database user |
| `POSTGRES_PASSWORD` | `sage_password` | Database password |

## Production Deployment

### 1. Update Environment Variables

Create a `.env` file:

```bash
# Database
POSTGRES_DB=sage_mode_prod
POSTGRES_USER=sage_prod_user
POSTGRES_PASSWORD=<strong-password>

# Redis
REDIS_PASSWORD=<strong-password>

# Application
DATABASE_URL=postgresql://sage_prod_user:<password>@postgres:5432/sage_mode_prod
REDIS_URL=redis://:<redis-password>@redis:6379/0
ENV=production
```

### 2. Modify docker-compose for Production

Create `docker-compose.prod.yml`:

```yaml
services:
  postgres:
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  redis:
    command: redis-server --requirepass ${REDIS_PASSWORD}
    restart: always

  fastapi:
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
      ENV: production
    # Remove volume mounts for production
    command: ["uvicorn", "sage_mode.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
    restart: always

  celery_worker:
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
      ENV: production
    command: ["celery", "-A", "sage_mode.celery_app", "worker", "-l", "warning", "-c", "8"]
    restart: always

  react:
    build:
      target: production
    environment:
      NODE_ENV: production
      VITE_API_URL: https://api.yourdomain.com
    restart: always
```

### 3. Deploy with Production Config

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### 4. Run Database Migrations

```bash
docker-compose exec fastapi alembic upgrade head
```

### 5. Scale Celery Workers

```bash
# Scale to 4 worker containers
docker-compose up -d --scale celery_worker=4
```

## Reverse Proxy Setup (Nginx)

Example Nginx configuration:

```nginx
upstream fastapi {
    server localhost:8000;
}

upstream react {
    server localhost:3000;
}

server {
    listen 80;
    server_name yourdomain.com;

    location /api {
        proxy_pass http://fastapi;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://fastapi;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    location / {
        proxy_pass http://react;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Health Checks

### Service Health

```bash
# Check all services
docker-compose ps

# FastAPI health
curl http://localhost:8000/health
# Response: {"status": "healthy", "version": "3.0"}

# PostgreSQL health
docker-compose exec postgres pg_isready -U sage_user -d sage_mode

# Redis health
docker-compose exec redis redis-cli ping
```

### Database Connection Test

```bash
docker-compose exec fastapi python -c "
from sage_mode.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('Database OK:', result.scalar())
"
```

## Monitoring Setup

### Celery Flower (Task Monitoring)

Add to docker-compose.yml:

```yaml
flower:
  build:
    context: .
    dockerfile: Dockerfile
  container_name: sage_mode_flower
  command: celery -A sage_mode.celery_app flower --port=5555
  ports:
    - "5555:5555"
  environment:
    CELERY_BROKER_URL: redis://redis:6379/0
  depends_on:
    - redis
  networks:
    - sage_network
```

Access at: http://localhost:5555

### Log Aggregation

View service logs:

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f fastapi
docker-compose logs -f celery_worker

# Last 100 lines
docker-compose logs --tail=100 fastapi
```

### Prometheus Metrics (Optional)

Add prometheus-fastapi-instrumentator to requirements.txt and configure in main.py for metrics export.

## Backup and Restore

### Database Backup

```bash
# Create backup
docker-compose exec postgres pg_dump -U sage_user sage_mode > backup_$(date +%Y%m%d).sql

# Restore backup
docker-compose exec -T postgres psql -U sage_user sage_mode < backup_20240120.sql
```

### Volume Backup

```bash
# Backup volumes
docker run --rm -v sage-mode_postgres_data:/data -v $(pwd):/backup alpine tar cvf /backup/postgres_data.tar /data
docker run --rm -v sage-mode_redis_data:/data -v $(pwd):/backup alpine tar cvf /backup/redis_data.tar /data
```

## Troubleshooting

### Common Issues

**Database connection refused**
```bash
# Check PostgreSQL is running and healthy
docker-compose ps postgres
docker-compose logs postgres
```

**Celery tasks not processing**
```bash
# Check worker status
docker-compose logs celery_worker

# Verify Redis connectivity
docker-compose exec celery_worker redis-cli -h redis ping
```

**Frontend can't reach API**
```bash
# Check CORS settings in sage_mode/main.py
# Verify VITE_API_URL environment variable
docker-compose logs react
```

**WebSocket connection fails**
```bash
# Ensure token query param matches session cookie
# Check browser console for 4001 (Unauthorized) errors
```

### Reset Development Environment

```bash
# Stop and remove all containers, volumes
docker-compose down -v

# Rebuild and start fresh
docker-compose up -d --build
```
