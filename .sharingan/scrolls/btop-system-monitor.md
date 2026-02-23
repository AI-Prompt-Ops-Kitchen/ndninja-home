---
name: btop-system-monitor
domain: CLI/System
level: 1-tomoe
description: Rich terminal system monitor — CPU, memory, network, disk, and process management with a beautiful TUI. Essential for monitoring Docker workloads and pipeline jobs.
sources:
  - type: youtube
    title: "10 CLI tools I use with Claude Code"
    url: "https://youtu.be/3NzCBIcIqD0"
    date: "2026-02-23"
    confidence: high
  - type: web
    title: "Btop GitHub"
    url: "https://github.com/aristocratos/btop"
    date: "2026-02-23"
    confidence: high
sources_count: 2
last_updated: 2026-02-23
can_do_from_cli: true
---

# Btop — Terminal System Monitor

## Mental Model
Btop is htop on steroids. Full TUI with CPU graphs, memory bars, network throughput, disk I/O, and a process list — all in one screen. Use it to monitor resource usage while running Claude Code, Docker containers, video rendering, or pipeline jobs.

## Installation
```bash
# Already installed (v1.3.2)
btop
```

## Navigation
| Key | Action |
|-----|--------|
| `↑/↓` or `j/k` | Navigate process list |
| `enter` | Detailed view of selected process |
| `t` | Tree view (parent/child processes) |
| `k` | Kill selected process (sends SIGTERM) |
| `K` | Kill menu (choose signal) |
| `f` | Filter processes |
| `/` | Search processes |
| `s` | Sort menu |
| `r` | Reverse sort |
| `e` | Toggle tree view |
| `m` | Cycle memory display mode |
| `n` | Cycle network display mode |
| `z` | Toggle net auto-scaling |
| `p` | Toggle per-core CPU view |
| `1` | Toggle CPU graph mode |
| `esc` | Back / close menu |
| `q` | Quit |

## Config
Config at `~/.config/btop/btop.conf`. Key settings:
```
color_theme = "Default"
theme_background = False  # transparent background
truecolor = True
update_ms = 1000
proc_sorting = "cpu lazy"
proc_tree = False
show_disks = True
```

## Integration Points — Ninja Ecosystem
- **Docker Swarm monitoring:** Watch container CPU/memory for Rasengan, Dojo, Redis
- **Pipeline jobs:** Monitor fal.ai/Kling API calls eating bandwidth
- **Video rendering:** FFmpeg and Remotion renders are CPU-heavy — btop shows the load
- **PostgreSQL:** Spot runaway queries by watching postgres process CPU

## Tips
- Leave btop running in a dedicated tmux pane for always-on monitoring
- Press `p` to see per-core utilization — useful for spotting single-threaded bottlenecks
- Tree view (`t`) shows which process spawned what — great for debugging subprocess chains
