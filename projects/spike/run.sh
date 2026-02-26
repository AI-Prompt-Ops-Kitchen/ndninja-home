#!/usr/bin/env bash
# Spike — Production runner
set -euo pipefail
cd "$(dirname "$0")"

PORT="${SPIKE_PORT:-8091}"

echo "=== Building Spike ==="
npm run build

echo "=== Starting Spike on port $PORT ==="
exec npx next start -p "$PORT"
