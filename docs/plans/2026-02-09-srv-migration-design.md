# Home Directory Migration to /srv (1.8TB Drive)

**Date:** 2026-02-09
**Beads:** clawd-mqq
**Status:** In Progress

## Context

The NVMe (468GB) hosts `/home/ndninja`. The 1.8TB SATA drive is mounted at `/srv`. Goal: move large directories to `/srv/home/` and symlink back to keep paths working.

## Prior Work (Feb 7)

Already migrated 51GB:
- **Caches** (18GB): `.cache`, `.chromium-browser-snapshots`, `.npm` → `/srv/home/cache/`
- **Toolchains** (7.3GB): `.bun`, `.cargo`, `.npm-global`, `.nvm`, `.rustup` → `/srv/home/toolchains/`
- **Projects** (26GB): `ai-tools-manager`, `clawd`, `dashboard`, `exo`, `n8n`, `ninja_hub_api`, `project-hummingbird`, `server-landing` → `/srv/home/projects/`

## Remaining Migration

### Phase 1: Cleanup
- Delete `.cache-old` (15GB stale cache backup)

### Phase 2: Migrate `.local` (3.2GB)
- Destination: `/srv/home/cache/.local`
- Contains: exo models (1.1GB), claude data (636MB), pipx (288MB), uv (219MB), bin (87MB), lib (938MB)

### Phase 3: Migrate `.claude` (2.5GB)
- Destination: `/srv/home/cache/.claude`
- Contains: plugin cache (bulk), hooks, skills, settings

### Phase 4: Migrate `.clawdbot` (281MB)
- Destination: `/srv/home/projects/.clawdbot`
- Requires: stop/start `clawdbot-gateway.service` (systemd user unit)

### Phase 5: Migrate `go/` (39MB)
- Destination: `/srv/home/toolchains/go`

### Phase 6: Verify & Close
- Confirm all symlinks resolve
- Test: clawdbot, claude, node/bun/cargo, go
- Close beads issue

## Result

NVMe freed: ~21GB. Only small config files remain in actual home directory.
