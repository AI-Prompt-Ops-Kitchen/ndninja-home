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

## Phase 3: Auto-Triggers (Heartbeat Integration)
**Goal:** Proactive assistance without being asked

- [ ] Define trigger conditions (pending tasks, time-based, etc.)
- [ ] Integrate with Clawdbot heartbeat system
- [ ] Surface relevant actions during heartbeats
- [ ] Smart notification (don't spam)

**Deliverable:** Heartbeat hooks that check project states

---

## Phase 4: Clawdbot Integration
**Goal:** Seamless integration with existing system

- [ ] Create Ninja Assist skill for Clawdbot
- [ ] Route intents to existing tools (ninja_content, exec, etc.)
- [ ] Fallback to full LLM for ambiguous requests
- [ ] Token usage tracking/optimization

**Deliverable:** Working skill that makes commands invisible

---

## Phase 5: Learning & Refinement
**Goal:** Get smarter over time

- [ ] Log successful routes for pattern learning
- [ ] Add user corrections mechanism
- [ ] Expand pattern library based on usage
- [ ] Measure token savings

**Deliverable:** Self-improving routing system
