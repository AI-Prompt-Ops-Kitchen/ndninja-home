#!/usr/bin/env bash
# Sage Mode — Build, push to local registry, and deploy to Docker Swarm
# Usage: bash swarm-deploy.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
REGISTRY="192.168.68.80:5000"
STACK_NAME="sage_mode"

echo "=== Sage Mode Swarm Deploy ==="
echo "Root:     $ROOT_DIR"
echo "Registry: $REGISTRY"
echo ""

# ── 1. Ensure local registry is running ──────────────────────────────────
if ! docker ps --format '{{.Ports}}' | grep -q '5000->5000'; then
    echo ">> Starting local registry (with auth)..."
    docker run -d -p 5000:5000 --name sage-registry --restart always \
        -v "$HOME/registry/auth:/auth" \
        -v registry_data:/var/lib/registry \
        -e "REGISTRY_AUTH=htpasswd" \
        -e "REGISTRY_AUTH_HTPASSWD_REALM=NDN Registry" \
        -e "REGISTRY_AUTH_HTPASSWD_PATH=/auth/htpasswd" \
        registry:2
    echo ">> Registry running on :5000"
else
    echo ">> Registry already running"
fi

# ── 2. Build backend image ───────────────────────────────────────────────
echo ""
echo ">> Building backend image..."
docker build -t "${REGISTRY}/sage-mode-backend:latest" \
    -f "$ROOT_DIR/Dockerfile" \
    "$ROOT_DIR"

# ── 3. Build frontend image ─────────────────────────────────────────────
echo ""
echo ">> Building frontend image..."
docker build -t "${REGISTRY}/sage-mode-frontend:latest" \
    --target production \
    -f "$ROOT_DIR/frontend/Dockerfile" \
    "$ROOT_DIR/frontend"

# ── 4. Push to local registry ───────────────────────────────────────────
echo ""
echo ">> Pushing images to local registry..."
docker push "${REGISTRY}/sage-mode-backend:latest"
docker push "${REGISTRY}/sage-mode-frontend:latest"
echo ">> Images pushed"

# ── 5. Deploy / update stack ────────────────────────────────────────────
echo ""
echo ">> Deploying stack: $STACK_NAME"

# Load .env if it exists (swarm doesn't auto-load .env files)
ENV_FILE="$ROOT_DIR/.env"
if [ -f "$ENV_FILE" ]; then
    echo ">> Loading env from $ENV_FILE"
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
fi

docker stack deploy \
    --with-registry-auth \
    -c "$SCRIPT_DIR/docker-compose.swarm.yml" \
    "$STACK_NAME"

echo ""
echo "=== Deploy complete ==="
echo ""
echo "Useful commands:"
echo "  docker stack services $STACK_NAME        # list services"
echo "  docker service ps ${STACK_NAME}_celery_worker  # see worker placement"
echo "  docker service logs ${STACK_NAME}_fastapi      # API logs"
echo "  docker stack rm $STACK_NAME              # tear down"
