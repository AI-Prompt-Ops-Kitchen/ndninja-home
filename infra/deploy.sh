#!/usr/bin/env bash
# NDN Infrastructure — Deploy monitoring stack to Docker Swarm
# Usage: bash deploy.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STACK_NAME="ndn_infra"

echo "=== NDN Monitoring Stack — Swarm Deploy ==="
echo "Dir: $SCRIPT_DIR"
echo ""

# Load env
ENV_FILE="$SCRIPT_DIR/.env.swarm"
if [ -f "$ENV_FILE" ]; then
    echo ">> Loading env from $ENV_FILE"
    set -a
    source "$ENV_FILE"
    set +a
else
    echo "!! WARNING: $ENV_FILE not found — Grafana will use default password"
fi

# Deploy stack
echo ">> Deploying stack: $STACK_NAME"
docker stack deploy \
    --with-registry-auth \
    -c "$SCRIPT_DIR/docker-compose.ndn-infra.yml" \
    "$STACK_NAME"

echo ""
echo "=== Deploy complete ==="
echo ""
echo "Services:"
echo "  VictoriaMetrics  http://100.77.248.9:8428"
echo "  Grafana          http://100.77.248.9:3001  (admin / \$GRAFANA_ADMIN_PASSWORD)"
echo "  node_exporter    http://100.77.248.9:9100/metrics"
echo "  postgres_export  http://100.77.248.9:9187/metrics"
echo ""
echo "Useful commands:"
echo "  docker stack services $STACK_NAME"
echo "  docker service logs ${STACK_NAME}_victoriametrics"
echo "  docker service logs ${STACK_NAME}_grafana"
echo "  docker stack rm $STACK_NAME"
