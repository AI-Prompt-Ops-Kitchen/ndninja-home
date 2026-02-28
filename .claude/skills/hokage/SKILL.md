---
name: hokage
description: Admin panel for managing Hokage judgment layer edicts — list, add, review, and track enforcement stats. For managing the rules, not consulting them (hooks handle that automatically).
---

# Hokage — Judgment Layer Admin

Manage the edicts that govern the ninja ecosystem. The hooks enforce rules automatically — this skill is for **administration only**.

## Invocation

```
/hokage              # Show summary stats
/hokage list         # List all edicts grouped by domain
/hokage list <domain> # List edicts for a specific domain
/hokage add          # Interactive: add a new edict
/hokage review       # Review recent enforcement events
/hokage stats        # Show block/warn/prefer counts and enforcement log
```

Natural language triggers:
- "hokage", "manage edicts", "edit rules", "add a rule", "enforcement stats"

---

## Edicts File

**Location:** `/home/ndninja/.claude/hokage/edicts.yaml`

Single source of truth for all 58 rules. YAML format with fields:
- `id` — Unique identifier (domain_NNN)
- `domain` — Category (14 domains)
- `severity` — BLOCK | WARN | PREFER
- `rule` — Human-readable rule text
- `rationale` — Why this rule exists
- `trigger_patterns` — Regex patterns for PreToolUse guard (Bash commands)
- `keywords` — Keywords for UserPromptSubmit scanner

## Domains (14)

| Domain | Description | Count |
|--------|-------------|-------|
| paid_api | Cost protection for rendering APIs | 5 |
| database | PostgreSQL enforcement | 3 |
| visual_style | Brand aesthetics | 6 |
| content_script | Script writing rules | 5 |
| avatar_tts | Voice and TTS rules | 7 |
| video_production | Rendering and assembly | 5 |
| qa_workflow | Quality assurance and preview | 5 |
| dual_anchor | Ninja + Glitch format | 5 |
| sharingan | Learning system rules | 4 |
| rasengan | Event hub rules | 2 |
| content_strategy | What content to make | 3 |
| glitch | AuDHD assistant project | 2 |
| user_context | Personal accommodations | 3 |
| session_memory | Memory management rules | 3 |

## Severity Levels

| Level | Hook Action | User Experience |
|-------|------------|-----------------|
| **BLOCK** | `decision: "block"` | Command refused with reason. Cannot proceed. |
| **WARN** | `decision: "ask"` | User prompted to confirm. Can override. |
| **PREFER** | `additionalContext` injection | Claude sees it silently. No interruption. |

## How Hooks Work (Auto — No Manual Invocation)

1. **SessionStart** (`hokage-session.sh`) — Loads ALL edicts into Claude's context on boot
2. **PreToolUse[Bash]** (`hokage-guard.sh`) — Pattern-matches commands against BLOCK/WARN patterns
3. **UserPromptSubmit** (`hokage-prompt.sh`) — Keyword-scans prompt, injects relevant domain edicts

## Adding a New Edict

When `/hokage add` is invoked, interactively collect:
1. **Domain** — pick from the 14 domains or create new
2. **Severity** — BLOCK, WARN, or PREFER
3. **Rule** — human-readable rule text
4. **Rationale** — why this rule exists
5. **Trigger patterns** — regex patterns (for BLOCK/WARN on Bash commands)
6. **Keywords** — for prompt keyword scanning

Then append to `edicts.yaml` and emit `hokage.edict_added` to Rasengan.

## Reviewing Enforcement

When `/hokage review` or `/hokage stats` is invoked:
1. Read `/home/ndninja/.logs/hokage.log` for recent enforcement events
2. Query Rasengan for `hokage.blocked` and `hokage.warned` events
3. Show summary: which edicts fire most, any false positives to tune

## Enforcement Log

All BLOCK/WARN events are logged to:
- **Local:** `/home/ndninja/.logs/hokage.log`
- **Rasengan:** `hokage.blocked`, `hokage.warned` event types

## Rasengan Integration

Events emitted:
- `hokage.session_loaded` — on every session start
- `hokage.blocked` — when a command is blocked (includes command preview + reason)
- `hokage.warned` — when a command triggers a warning
- `hokage.edict_added` — when a new edict is added via /hokage add
