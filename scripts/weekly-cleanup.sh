#!/bin/bash
# Weekly disk cleanup script
# Runs: Docker prune, journal vacuum, APT cache clean

LOG_FILE="/var/log/weekly-cleanup.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

log() {
    echo "[$DATE] $1" | tee -a "$LOG_FILE"
}

log "=== Starting weekly cleanup ==="

# Get initial disk usage
BEFORE=$(df / --output=used | tail -1)

# Docker cleanup (remove unused images, containers, networks, build cache)
log "Cleaning Docker..."
docker system prune -a -f >> "$LOG_FILE" 2>&1

# Journal logs (keep last 100MB)
log "Vacuuming journal logs..."
journalctl --vacuum-size=100M >> "$LOG_FILE" 2>&1

# APT cache
log "Cleaning APT cache..."
apt clean >> "$LOG_FILE" 2>&1

# Get final disk usage
AFTER=$(df / --output=used | tail -1)
FREED=$(( (BEFORE - AFTER) / 1024 ))

log "=== Cleanup complete ==="
log "Space freed: ${FREED}MB"
log "Current disk usage: $(df -h / --output=pcent | tail -1 | tr -d ' ')"
