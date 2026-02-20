#!/usr/bin/env bash
# Dev mode: FastAPI on 8090 + Vite on 5173 (proxied)
set -e

PROJ=/home/ndninja/projects/ninja-dashboard

cleanup() {
  echo "⏹  Stopping servers…"
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "🐍 Starting FastAPI backend on http://localhost:8090"
cd "$PROJ/backend"
python3 -m uvicorn main:app \
  --host 0.0.0.0 \
  --port 8090 \
  --workers 1 \
  --reload &
BACKEND_PID=$!

sleep 1

echo "⚡ Starting Vite dev server on http://localhost:5173"
cd "$PROJ/frontend"
npm run dev -- --host &
FRONTEND_PID=$!

echo ""
echo "🥷 The Dojo — Dev Mode"
echo "   Local:    http://localhost:5173"
echo "   Tailscale: http://100.77.248.9:5173"
echo ""

wait
