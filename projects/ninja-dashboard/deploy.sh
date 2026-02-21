#!/bin/bash
# Safe deployment: build, validate, deploy, smoke test + pipeline tests
set -euo pipefail

COMPOSE_FILE="/home/ndninja/projects/ninja-dashboard/docker-compose.ndn-services.yml"
STACK_NAME="ndn_services"
ENV_FILE="/home/ndninja/projects/ninja-dashboard/.env.swarm"

echo "=== NDN Services Deploy ==="

# 1. Source env and validate required vars BEFORE deploying
set -a; source "$ENV_FILE"; set +a

REQUIRED_VARS="DOJO_DATABASE_URL ANTHROPIC_API_KEY ELEVENLABS_API_KEY GOOGLE_CLOUD_PROJECT"
for var in $REQUIRED_VARS; do
    if [ -z "${!var:-}" ]; then
        echo "FATAL: $var is empty in $ENV_FILE"
        exit 1
    fi
done

# Check fal key (either name)
if [ -z "${FAL_KEY:-}" ] && [ -z "${FAL_AI_API_KEY:-}" ]; then
    echo "FATAL: Neither FAL_KEY nor FAL_AI_API_KEY set in $ENV_FILE"
    exit 1
fi

echo "Env vars validated OK"

# 2. Build images
echo "Building images..."
docker build -t 192.168.68.80:5000/ndn-dojo:latest /home/ndninja/projects/ninja-dashboard/
docker build -t 192.168.68.80:5000/ndn-content-worker:latest /home/ndninja/projects/content-worker/
docker push 192.168.68.80:5000/ndn-dojo:latest
docker push 192.168.68.80:5000/ndn-content-worker:latest
echo "Images built and pushed"

# 3. Deploy stack
echo "Deploying stack..."
docker stack deploy -c "$COMPOSE_FILE" "$STACK_NAME"

# 4. Wait for services to stabilize
echo "Waiting for services..."
sleep 15

# 5. Smoke test — use httpx (curl hangs on Swarm ingress IPv6)
echo "Running smoke test..."
HTTP_CODE=$(python3 -c "
import httpx
r = httpx.get('http://127.0.0.1:8090/api/jobs', timeout=10)
print(r.status_code)
" 2>/dev/null || echo "000")

if [ "$HTTP_CODE" != "200" ]; then
    echo "SMOKE TEST FAILED: Dojo API returned $HTTP_CODE"
    echo "Check logs: docker service logs ${STACK_NAME}_dojo --tail 30"
    exit 1
fi
echo "Dojo API: OK (HTTP $HTTP_CODE)"

# Content worker running
WORKER_COUNT=$(docker service ps "${STACK_NAME}_content_worker" --filter desired-state=running -q 2>/dev/null | wc -l)
if [ "$WORKER_COUNT" -lt 1 ]; then
    echo "SMOKE TEST FAILED: Content worker not running"
    docker service logs "${STACK_NAME}_content_worker" --tail 30
    exit 1
fi
echo "Content worker: $WORKER_COUNT replica(s)"

# 6. Run pipeline test harness inside content worker container
echo ""
echo "Running pipeline test harness..."
WORKER_CONTAINER=$(docker ps --filter "name=${STACK_NAME}_content_worker" --format '{{.ID}}' | head -1)
if [ -z "$WORKER_CONTAINER" ]; then
    echo "WARN: Could not find content worker container for pytest"
else
    if docker exec "$WORKER_CONTAINER" python3 -m pytest /app/tests/ -v --tb=short; then
        echo "Pipeline tests: PASSED"
    else
        echo "PIPELINE TESTS FAILED"
        echo "Check logs: docker service logs ${STACK_NAME}_content_worker --tail 50"
        exit 1
    fi
fi

echo ""
echo "=== DEPLOY SUCCESSFUL ==="
echo "Dojo: http://localhost:8090"
echo "Content worker: $WORKER_COUNT replica(s)"
echo "Pipeline tests: PASSED"
