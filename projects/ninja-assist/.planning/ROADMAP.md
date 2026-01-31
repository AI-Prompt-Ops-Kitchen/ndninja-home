# Ninja Assist - Roadmap

## Phase 1: Intent Router (Foundation) ✅ COMPLETE
**Goal:** Plain language → categorized intent

- [x] Define intent categories (code, research, install, design)
- [x] Build pattern matching layer (regex/keywords)
- [x] Create intent → tool mapping
- [x] Test with common phrases (33/33 tests passing)

**Deliverable:** `src/intent_router.py` - classifies user input with 0 LLM tokens

---

## Phase 2: Context State System ✅ COMPLETE
**Goal:** Persistent project awareness

- [x] Define `.state.json` schema
- [x] Auto-detect current project from cwd/context
- [x] Track: current phase, pending tasks, last action
- [x] Integrate with GSD `.planning/` folders

**Deliverable:** `src/state_manager.py` - persists context across sessions (8/8 tests passing)

---

## Phase 3: Auto-Triggers (Heartbeat Integration) ✅ COMPLETE
**Goal:** Proactive assistance without being asked

- [x] Define trigger conditions (pending tasks, stale project, phase complete)
- [x] Integrate with Clawdbot heartbeat system
- [x] Surface relevant actions during heartbeats
- [x] Smart notification (spam prevention via TriggerHistory)

**Deliverable:** `src/auto_triggers.py` - heartbeat hooks with 8/8 tests passing

**Trigger Types:**
- `pending_tasks` - Surface when ≥3 tasks waiting
- `stale_project` - Nudge after 48h inactivity
- `phase_complete` - Celebrate + suggest next phase
- `custom` - Register your own checks

---

## Phase 4: Clawdbot Integration ✅ COMPLETE
**Goal:** Seamless integration with existing system

- [x] Create Ninja Assist skill for Clawdbot
- [x] Route intents to existing tools (ninja_content, exec, etc.)
- [x] Fallback to full LLM for ambiguous requests
- [ ] Token usage tracking/optimization (deferred to Phase 5)

**Deliverable:** `skills/ninja-assist/` - Clawdbot skill with 3 scripts

**Scripts:**
- `route.py` — Classify intent, suggest tool
- `context.py` — Show project state
- `heartbeat.py` — Check for triggers

---

## Phase 5: Learning & Refinement ✅ COMPLETE
**Goal:** Get smarter over time

- [x] Log successful routes for pattern learning
- [x] Add user corrections mechanism
- [x] Expand pattern library based on usage
- [x] Measure token savings

**Deliverable:** `src/learning.py` - self-improving system (8/8 tests passing)

**Features:**
- Route logging to `~/.ninja-assist/route_logs.jsonl`
- Correction with `--correct <category>` learns new patterns
- Stats tracking: tokens saved, cost, accuracy
- Learned patterns auto-applied before built-in patterns
