#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
source .env 2>/dev/null || true

echo "=== Building frontend ==="
cd frontend
npm install
npm run build
cd ..

echo "=== Starting ROYS on port 8070 ==="
cd backend
uvicorn main:app --host 0.0.0.0 --port 8070 --workers 2
