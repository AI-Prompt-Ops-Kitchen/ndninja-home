#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
source .env 2>/dev/null || true

cleanup() {
    echo "Shutting down..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null
}
trap cleanup EXIT

echo "=== Starting ROYS dev mode ==="

cd backend
uvicorn main:app --host 0.0.0.0 --port 8070 --reload &
BACKEND_PID=$!
cd ..

cd frontend
npm install
npm run dev &
FRONTEND_PID=$!
cd ..

echo "Backend:  http://localhost:8070"
echo "Frontend: http://localhost:5173"

wait
