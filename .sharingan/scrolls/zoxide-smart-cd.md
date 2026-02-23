---
name: zoxide-smart-cd
domain: CLI/Navigation
level: 2-tomoe
description: Smart cd replacement — learns your navigation patterns and lets you fuzzy-jump to any directory with partial names. Massive time saver for deep project trees.
sources:
  - type: youtube
    title: "10 CLI tools I use with Claude Code"
    url: "https://youtu.be/3NzCBIcIqD0"
    date: "2026-02-23"
    confidence: high
  - type: web
    title: "Zoxide GitHub"
    url: "https://github.com/ajeetdsouza/zoxide"
    date: "2026-02-23"
    confidence: high
sources_count: 2
last_updated: 2026-02-23
can_do_from_cli: true
---

# Zoxide — Smart Directory Jumper

## Mental Model
Zoxide replaces `cd` with a frecency-based directory database. Every time you visit a directory, zoxide remembers it. Then you can jump to any directory by typing just a partial name — `z dojo` instead of `cd /home/ndninja/projects/ninja-dashboard/`. It ranks by frequency + recency (frecency).

## Installation & Setup
```bash
# Already installed (v0.9.7)
# Shell init already in ~/.bashrc:
eval "$(zoxide init bash)"
```

## Core Commands
| Command | What it does |
|---------|-------------|
| `z <query>` | Jump to best-matching directory |
| `z <q1> <q2>` | Fuzzy match with multiple terms |
| `zi <query>` | Interactive mode (fzf picker) |
| `z -` | Jump to previous directory |
| `zoxide query <query>` | Show what would match (dry run) |
| `zoxide query -ls` | List all known directories + scores |
| `zoxide add <path>` | Manually add a path to the database |
| `zoxide remove <path>` | Remove a path from the database |

## How Frecency Works
- Each directory gets a score based on frequency (how often) + recency (how recently)
- Recent visits get exponentially more weight
- Scores decay over time for directories you stop visiting
- Multiple query terms are AND-matched against path segments

## Expected Shortcuts After Training

Once zoxide learns your patterns:
| You type | It jumps to |
|----------|------------|
| `z dojo` | `/home/ndninja/projects/ninja-dashboard/` |
| `z rasengan` | `/home/ndninja/rasengan/` |
| `z scrolls` | `/home/ndninja/.sharingan/scrolls/` |
| `z glitch` | `/home/ndninja/projects/glitch/` |
| `z scripts` | `/home/ndninja/scripts/` |
| `z backend` | `/home/ndninja/projects/ninja-dashboard/backend/` |
| `z frontend` | `/home/ndninja/projects/ninja-dashboard/frontend/` |
| `z output` | `/home/ndninja/output/` |
| `z spike` | `/home/ndninja/projects/spike/` |
| `z remotion` | `/home/ndninja/projects/remotion-video/` |
| `z youtube` | `/home/ndninja/scripts/youtube/` |

## Kickstart Training
Seed the database with frequently-used paths:
```bash
zoxide add /home/ndninja/projects/ninja-dashboard
zoxide add /home/ndninja/projects/ninja-dashboard/backend
zoxide add /home/ndninja/projects/ninja-dashboard/frontend
zoxide add /home/ndninja/rasengan
zoxide add /home/ndninja/.sharingan/scrolls
zoxide add /home/ndninja/projects/glitch
zoxide add /home/ndninja/scripts
zoxide add /home/ndninja/scripts/youtube
zoxide add /home/ndninja/output
zoxide add /home/ndninja/projects/remotion-video
zoxide add /home/ndninja/projects/spike
zoxide add /home/ndninja/sage_mode
```

## Tips
- `zi` (interactive) requires `fzf` — install with `sudo apt install fzf` if needed
- Database stored at `~/.local/share/zoxide/db.zo`
- Works instantly — no background process, just a shell function
- Supports bash, zsh, fish, PowerShell, Nushell
- Pairs well with `ranger` — navigate in ranger, `z` jumps back later
