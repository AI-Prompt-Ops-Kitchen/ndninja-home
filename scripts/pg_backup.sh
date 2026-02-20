#!/usr/bin/env bash
# Nightly PostgreSQL backup — all databases
# Cron: 0 2 * * * /home/ndninja/scripts/pg_backup.sh >> /home/ndninja/.logs/pg-backup.log 2>&1

set -euo pipefail

BACKUP_DIR="/home/ndninja/backups/postgres"
RETENTION_DAYS=14
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DUMP_FILE="${BACKUP_DIR}/pg_dumpall_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

# Dump all databases (compressed) — peer auth via sudo
sudo -u postgres pg_dumpall 2>/dev/null | gzip > "$DUMP_FILE"

# Verify the dump is non-trivial (> 1KB)
SIZE=$(stat -c%s "$DUMP_FILE")
if [ "$SIZE" -lt 1024 ]; then
    echo "[$(date)] ERROR: Backup suspiciously small (${SIZE} bytes): $DUMP_FILE"
    exit 1
fi

echo "[$(date)] OK: Backup created ($(numfmt --to=iec "$SIZE")): $DUMP_FILE"

# Prune old backups
find "$BACKUP_DIR" -name "pg_dumpall_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
REMAINING=$(find "$BACKUP_DIR" -name "pg_dumpall_*.sql.gz" | wc -l)
echo "[$(date)] Retention: ${REMAINING} backups kept (${RETENTION_DAYS}-day window)"
