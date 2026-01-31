---
name: ninja-assist
description: Neurodivergent-friendly AI routing layer. Routes plain language to the right tools automatically. Use when user says things like "help me code", "research X", "install Y", or asks about project status. Reduces cognitive load by eliminating the need to remember commands.
homepage: https://github.com/AI-Prompt-Ops-Kitchen/clawd
metadata: {"clawdbot":{"emoji":"🥷","category":"productivity"}}
---

# Ninja Assist

Plain language → right tool. Zero commands to remember.

## Quick Start

Route a request:
```bash
python3 /home/ndninja/clawd/skills/ninja-assist/scripts/route.py "help me code a parser"
# → {"category": "code", "tool": "claude_code", "confidence": 0.85}
```

Check project context:
```bash
python3 /home/ndninja/clawd/skills/ninja-assist/scripts/context.py
# → Shows current project, phase, pending tasks
```

Check heartbeat triggers:
```bash
python3 /home/ndninja/clawd/skills/ninja-assist/scripts/heartbeat.py
# → Returns alerts or "Nothing to report"
```

## Intent Categories

| Category | Triggers | Routes To |
|----------|----------|-----------|
| **code** | "help me code", "fix bug", "write function" | Claude Code / GSD |
| **research** | "research X", "what is", "compare" | web_search |
| **install** | "install", "update", "npm/pip" | exec |
| **design** | "brainstorm", "architect", "help me think" | Shadow Council |
| **unknown** | Ambiguous requests | Full LLM |

## Routing Logic

1. **Pattern match** (0 tokens) — Check 50+ regex patterns
2. **Confidence threshold** — If ≥0.5, route to tool
3. **Fallback** — If <0.5 or unknown, use full LLM

## Project Context

Auto-detects projects by walking up from cwd looking for:
- `.state.json` (Ninja Assist)
- `.planning/` (GSD)
- `.beads/` (Beads)
- `.git/` (Git root)

State persists to `.state.json` in project root.

## Heartbeat Integration

Add to HEARTBEAT.md:
```markdown
## Ninja Assist (every 4h)
python3 /home/ndninja/clawd/skills/ninja-assist/scripts/heartbeat.py
```

Trigger types:
- `pending_tasks` — ≥3 tasks waiting
- `stale_project` — No activity in 48h
- `phase_complete` — All tasks done, suggest next phase

## Learning System

Ninja Assist learns from corrections and tracks token savings.

Correct a misclassification:
```bash
python3 /home/ndninja/clawd/skills/ninja-assist/scripts/route.py --correct research
# Learns a new pattern from the last route
```

View stats:
```bash
python3 /home/ndninja/clawd/skills/ninja-assist/scripts/stats.py
# Shows tokens saved, accuracy, learned patterns
```

Data stored in `~/.ninja-assist/`:
- `route_logs.jsonl` — All routing decisions
- `learned_patterns.json` — Patterns from corrections
- `stats.json` — Token savings, route counts

## Usage in Conversation

When user says something like:
- "help me code X" → Route to Claude Code
- "research Y" → Use web_search
- "what's the status of project Z" → Show context
- "install numpy" → Run `pip install numpy`

Don't ask "which tool?" — just route based on intent.

If user says "that was wrong, I meant research" → Run correction to learn.
