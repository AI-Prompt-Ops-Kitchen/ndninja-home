# The Dojo — Multi-stage build: React frontend + FastAPI backend

# Stage 1: Build React frontend
FROM node:20-alpine AS frontend-build

WORKDIR /src
# Copy both frontend and backend dirs so vite's outDir (../backend/static) resolves
COPY frontend/ ./frontend/
COPY backend/ ./backend/

WORKDIR /src/frontend
RUN npm ci --ignore-scripts
RUN npm run build
# Output lands in /src/backend/static/

# Stage 2: Python backend + static frontend
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./

# Overwrite with freshly built frontend
COPY --from=frontend-build /src/backend/static/ ./static/

EXPOSE 8090

HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=10s \
    CMD curl -f http://localhost:8090/api/jobs || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8090", "--workers", "1"]
