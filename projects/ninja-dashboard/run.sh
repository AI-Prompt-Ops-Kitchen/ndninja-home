#!/usr/bin/env bash
# Production: build frontend → serve everything from FastAPI on port 8090
set -e

# Load environment variables (API keys, etc.)
[ -f "$HOME/.env" ] && set -a && source "$HOME/.env" && set +a

PROJ=/home/ndninja/projects/ninja-dashboard

echo "🔨 Building frontend…"
cd "$PROJ/frontend"
npm run build

echo "🥷 Starting The Dojo on http://0.0.0.0:8090"
cd "$PROJ/backend"
python3 -m uvicorn main:app \
  --host 0.0.0.0 \
  --port 8090 \
  --workers 1
