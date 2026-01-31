# TOOLS.md - Local Notes

Skills define *how* tools work. This file is for *your* specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:
- Camera names and locations
- SSH hosts and aliases  
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras
- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH
- home-server → 192.168.1.100, user: admin

### TTS
- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

### iCloud Calendar (CalDAV)
- Credentials: `.env.calendar` (chmod 600)
- Python venv: `.venv` (has `caldav` library)
- Calendars: Home, Content Creation, Health/Self-Care, Work, Reminders
- Server: caldav.icloud.com (auto-redirects to p175-caldav.icloud.com)
- Usage: `source .venv/bin/activate && python3 <script>`

### Email (Himalaya)
- Account: iCloud (jeramie_higgins@icloud.com)
- Config: `~/.config/himalaya/config.toml`
- Password: reuses `.env.calendar` credential
- IMAP: imap.mail.me.com:993 (TLS)
- SMTP: smtp.mail.me.com:587 (STARTTLS)

### GitHub
- Account: AI-Prompt-Ops-Kitchen
- CLI: `gh` (authenticated)

### Coding Agent
- Claude Code CLI v2.1.19
- Path: `~/.local/bin/claude`

### Vengeance (RTX 4090)
- SSH: `ssh vengeance` (Steam@100.98.226.75 via Tailscale)
- GPU: RTX 4090 24GB VRAM
- WSL2 Ubuntu, conda env: `musetalk`
- MuseTalk: `/mnt/d/musetalk/`
- CogVideoX: TODO setup

### CapCut API Server
- Service: `systemctl --user status capcut-api`
- Port: 9000
- Auto-starts on boot (linger enabled)
- Logs: `journalctl --user -u capcut-api -f`
- Restart: `systemctl --user restart capcut-api`

### GSD (Get Shit Done) - Claude Code Framework
- **Location:** `~/.claude/commands/GSD/`
- **Source:** https://github.com/OutcomefocusAi/GSD
- **Purpose:** Multi-agent project planning & execution for Claude Code
- **Use:** Run `/gsd:help` in Claude Code to see all commands
- **Key flow:** `/gsd:new-project` → `/gsd:plan-phase 1` → `/gsd:execute-phase 1`

### Higgsfield (Kling Avatar)
- SDK: `pip install higgsfield-client`
- Auth: `HF_KEY="api-key:api-secret"` or `HF_API_KEY` + `HF_API_SECRET`
- Docs: https://docs.higgsfield.ai
- Console: https://cloud.higgsfield.ai
- Key model: **Kling Avatar 2.0** - image + audio → lip-synced video (up to 5 min)
- Test script: `scripts/higgsfield_test.py`

Add whatever helps you do your job. This is your cheat sheet.
