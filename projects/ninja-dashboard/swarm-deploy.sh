#!/usr/bin/env bash
# NDN Services — Build, push to local registry, and deploy to Docker Swarm
# Usage: bash swarm-deploy.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REGISTRY="192.168.68.80:5000"
STACK_NAME="ndn_services"

echo "=== NDN Services Swarm Deploy ==="
echo "Dir:      $SCRIPT_DIR"
echo "Registry: $REGISTRY"
echo ""

# ── 1. Build Dojo image (multi-stage: Node + Python) ─────────────────────
echo ">> Building Dojo image..."
docker build -t "${REGISTRY}/ndn-dojo:latest" \
    -f "$SCRIPT_DIR/Dockerfile" \
    "$SCRIPT_DIR"

# ── 2. Build Preview/Upload image ────────────────────────────────────────
PREVIEW_DIR="$SCRIPT_DIR/../preview-upload"
if [ -d "$PREVIEW_DIR" ]; then
    echo ""
    echo ">> Building Preview/Upload image..."
    docker build -t "${REGISTRY}/ndn-preview-upload:latest" \
        -f "$PREVIEW_DIR/Dockerfile" \
        "$PREVIEW_DIR"
fi

# ── 3. Build Content Worker image ────────────────────────────────────────
WORKER_DIR="$SCRIPT_DIR/../content-worker"
if [ -d "$WORKER_DIR" ]; then
    echo ""
    echo ">> Building Content Worker image..."
    docker build -t "${REGISTRY}/ndn-content-worker:latest" \
        -f "$WORKER_DIR/Dockerfile" \
        "$WORKER_DIR"
fi

# ── 4. Push to local registry ────────────────────────────────────────────
echo ""
echo ">> Pushing images to local registry..."
docker push "${REGISTRY}/ndn-dojo:latest"
docker image inspect "${REGISTRY}/ndn-preview-upload:latest" &>/dev/null && \
    docker push "${REGISTRY}/ndn-preview-upload:latest"
docker image inspect "${REGISTRY}/ndn-content-worker:latest" &>/dev/null && \
    docker push "${REGISTRY}/ndn-content-worker:latest"
echo ">> Images pushed"

# ── 5. Load env if present ───────────────────────────────────────────────
ENV_FILE="$SCRIPT_DIR/.env.swarm"
if [ -f "$ENV_FILE" ]; then
    echo ">> Loading env from $ENV_FILE"
    set -a
    source "$ENV_FILE"
    set +a
fi

# ── 6. Deploy / update stack ─────────────────────────────────────────────
echo ""
echo ">> Deploying stack: $STACK_NAME"

docker stack deploy \
    --with-registry-auth \
    -c "$SCRIPT_DIR/docker-compose.ndn-services.yml" \
    "$STACK_NAME"

echo ""
echo "=== Deploy complete ==="
echo ""
echo "Useful commands:"
echo "  docker stack services $STACK_NAME"
echo "  docker service logs ${STACK_NAME}_dojo"
echo "  docker service logs ${STACK_NAME}_preview"
echo "  docker service logs ${STACK_NAME}_upload"
echo "  docker service logs ${STACK_NAME}_content_worker"
echo "  docker stack rm $STACK_NAME"
