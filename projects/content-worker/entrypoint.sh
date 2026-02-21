#!/bin/bash
echo "Running preflight check..."
/app/preflight.sh
if [ $? -ne 0 ]; then
    echo "PREFLIGHT FAILED — refusing to start worker"
    # Sleep so Docker doesn't restart-loop us into oblivion
    sleep 300
    exit 1
fi
echo "Preflight passed, starting Celery worker..."
exec celery -A celery_app worker -l info -c 2 -Q content -n "content@%h"
