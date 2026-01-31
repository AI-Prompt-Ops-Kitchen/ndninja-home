# Ninja Assist — Project State

## Overview
Neurodivergent-friendly AI interface that routes plain-language requests to the right tools automatically.

## Status: 🟡 PLANNING
Last updated: 2026-01-31

## Location
`/home/ndninja/clawd/projects/ninja-assist/`

## The Problem
- Too many tools/commands to remember
- Cognitive overhead causes friction
- User has ADHD + Autism — manual steps = failure points

## The Solution
Hybrid A+C architecture:
1. **Layer 1:** Pattern matching (zero tokens)
2. **Layer 2:** Context state files (persistent)
3. **Layer 3:** Auto-triggers on heartbeats
4. **Layer 4:** Full LLM only when needed

## Core Use Cases
| Intent | Routes To |
|--------|-----------|
| Code | Claude Code / GSD |
| Research | web_search / Shadow Council |
| Install/Update | exec / package managers |
| Design/Brainstorm | Shadow Council |

## Phases
1. ✅ Intent Router (Foundation) - `src/intent_router.py` (33/33 tests)
2. ✅ Context State System - `src/state_manager.py` (8/8 tests)
3. ⏳ Auto-Triggers (Heartbeat)
4. ⏳ Clawdbot Integration
5. ⏳ Learning & Refinement

## Key Files
- `.planning/PROJECT.md` — Vision
- `.planning/REQUIREMENTS.md` — Specs
- `.planning/ROADMAP.md` — Phases

## Design Principles
- AUTOMATION IS NON-NEGOTIABLE
- Token efficient
- Plain language in, right tool out
- Never make user feel stupid
