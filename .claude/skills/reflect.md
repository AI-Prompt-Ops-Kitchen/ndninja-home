---
name: reflect
description: Analyze conversations for corrections and update skills with learnings
version: 2.0.0
category: meta
args: ["[session_id]", "[--skill]", "[--dry-run]", "[--auto-approve]"]
when_to_use: "User wants to improve skills based on recent corrections, or automatically run after sessions with explicit corrections/preferences. Use when user says 'learn from this', 'remember this correction', or 'update the skill'."
tags: [reflection, meta-learning, self-improvement, skill-evolution, automation]
reflection_count: 4
last_reflection: 2026-01-10
---
# Reflect: Self-Improving Skills

Analyze conversation corrections and automatically update skill files with learnings. Implements "correct once, never again" workflow.

## Purpose

When you correct Claude's behavior during a session (e.g., "Actually, use WebFetch not just WebSearch"), this skill captures that correction and permanently updates the relevant skill file so the mistake never happens again.

## Usage

```bash
# Reflect on current session (most common)
/reflect

# Reflect on specific past session
/reflect kage-bunshin-week3-implementation-2026-01-04

# Reflect only on specific skill
/reflect --skill verify-official

# Preview without applying changes
/reflect --dry-run

# Auto-approve high confidence updates (no prompts)
/reflect --auto-approve

# Combine options
/reflect --skill daily-review --dry-run
```

## How It Works

1. **Signal Detection**: Scans conversation summaries for correction patterns:
   - "Actually, [correction]"
   - "No, the correct way is..."
   - "Instead of X, use Y"
   - "Always do X when Y"
   - Repeated topics (pattern detection)
   - Key decisions (preference detection)

2. **LLM Council Analysis**: Uses multi-model consensus to:
   - Determine which skill(s) need updating
   - Extract the specific learning
   - Assess confidence (high/medium/low)
   - Propose concrete changes

3. **Skill Update**: Updates markdown skill files by:
   - Adding entry to "Learnings" section
   - Updating version number
   - Recording metadata (timestamp, confidence, source)

4. **Git Commit**: Creates structured commit:
   - Clear commit message with reflection details
   - Separate commit per reflection (easy rollback)
   - Tracked in git history

5. **Database Tracking**: Records in `skill_reflections` table:
   - Full reflection history
   - Confidence levels
   - Effectiveness tracking
   - Source sessions

## Examples

### Example 1: Explicit Correction

**Session:**
```
User: "Actually, always use WebFetch to verify content, not just WebSearch"
Claude: [fixes the verify-official skill]
```

**Command:**
```bash
/reflect
```

**Output:**
```
🧠 Reflection Engine v1.0.0
============================================================

📡 Detecting signals...
   ✓ Detected 1 signal(s)

🔍 Analyzing with LLM Council...
   ✓ Generated 1 reflection(s)

============================================================
Reflection 1/1
============================================================

🎯 Skill: verify-official
📝 Signal: Always use WebFetch to verify content, not just WebSearch
🔒 Confidence: HIGH
📋 What Changed: Added mandatory WebFetch verification step
💡 Rationale: Explicit user correction indicating WebSearch alone is insufficient
🔗 Source: hallu-guardrails-2026-01-03

📄 File: /home/ndninja/.claude/skills/verify-official.md
📦 Version: 1.2.0 → 1.2.1

✏️  Learning Entry:
---
### 2026-01-05 14:30 - Correction
**Signal:** "Always use WebFetch to verify content, not just WebSearch"
**What Changed:** Added mandatory WebFetch verification step
**Confidence:** High
**Source:** hallu-guardrails-2026-01-03
**Rationale:** Explicit user correction indicating WebSearch alone is insufficient
---

❓ Apply this update? [y/N]: y

⚙️  Applying update...
   ✓ Skill file updated
   ✓ Committed: abc123f4
   ✓ Recorded in database

✅ Update applied successfully!

============================================================
📊 Summary
============================================================
Signals detected: 1
Reflections proposed: 1
Updates applied: 1
```

### Example 2: Pattern Detection

**Multiple Sessions:**
```
Session 1: User asks to export docs to Craft
Session 2: User asks to export docs to Craft again
Session 3: User asks to export docs to Craft (3rd time!)
```

**Command:**
```bash
/reflect --days 7
```

**Output:**
```
🎯 Skill: NEW_SKILL
📝 Signal: Repeated topic: documentation export
🔒 Confidence: HIGH
📋 What Changed: Suggest creating /export-docs skill
💡 Rationale: User requested 3 times in past week
```

### Example 3: Preference Update

**Session with decision:**
```
Key decision: "Changed default output to Craft instead of file"
```

**Command:**
```bash
/reflect --skill generate-doc
```

**Output:**
```
🎯 Skill: generate-doc
📝 Signal: Changed default output to Craft instead of file
🔒 Confidence: MEDIUM
📋 What Changed: Updated default --output flag from 'file' to 'craft'
```

## Confidence Levels

**HIGH** (Auto-approved in --auto-approve mode):
- Explicit corrections repeated 2+ times
- Very clear, specific corrections
- Pattern detected across multiple sessions
- User says "always", "never", "must"

**MEDIUM** (Requires manual approval):
- Single clear correction
- Specific preference stated once
- Implied from key decision

**LOW** (Always requires manual approval):
- Vague or ambiguous
- Inferred from context
- Unclear generalizability

## Skill File Format

After reflection, skills get a "Learnings" section:

```markdown
---
name: skill-name
version: 1.2.1
last_reflection: 2026-01-05 14:30:00
reflection_count: 3
---

[Original skill content...]

---

## 🧠 Learnings (Auto-Updated)

### 2026-01-10 - Bug Fix (Consolidated)
**Signal:** "Fixed critical infinite loop bug in reflection engine"
**What Changed:**
- Deduplication now uses session ID matching (not just signal text)
- Added `_record_skipped_reflection()` method for NEW_SKILL signals
- Consolidated 36+ duplicate entries into this single learning
**Confidence:** High
**Source:** reflection-engine-deduplication-fix-2026-01-10
**Rationale:** Root cause was signal detector extracting different text lengths, creating unique fingerprints that bypassed deduplication. Fix: use session-based deduplication.

### 2026-01-05 14:30 - Correction
**Signal:** "Always use HTTPS for API calls, not HTTP"
**What Changed:** Updated all example URLs from http:// to https://
**Confidence:** High
**Source:** kage-bunshin-week3-implementation-2026-01-04

### 2026-01-04 09:15 - Pattern
**Signal:** User corrected port from 8000 to 8080 (3rd time)
**What Changed:** Default port changed to 8080 in examples
**Confidence:** High
**Source:** prompting-techniques-import-2026-01-03

### 2026-01-03 16:45 - Preference
**Signal:** "Please always save to Craft, not local files"
**What Changed:** Changed default --output flag from 'file' to 'craft'
**Confidence:** Medium
**Source:** hallu-guardrails-2026-01-03
```
