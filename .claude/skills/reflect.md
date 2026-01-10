---
name: reflect
description: Analyze conversations for corrections and update skills with learnings
version: 1.0.29
category: meta
args: ["[session_id]", "[--skill]", "[--dry-run]", "[--auto-approve]"]
when_to_use: "User wants to improve skills based on recent corrections, or automatically run after sessions with explicit corrections/preferences. Use when user says 'learn from this', 'remember this correction', or 'update the skill'."
tags: [reflection, meta-learning, self-improvement, skill-evolution, automation]
reflection_count: 29
last_reflection: 2026-01-10 14:07:49
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

### 2026-01-10 14:07 - Correction
**Signal:** "Fixed critical infinite loop bug in reflection engine where stop hook repeatedly detected same signals. Root cause: NEW_SKILL reflections (signals for already-implemented features) were filtered out but never recorded in database, causing re-detection on every run."
**What Changed:** Added _record_skipped_reflection() method to record filtered reflections with reviewed_by='auto-skipped' to prevent infinite loops
**Confidence:** High
**Source:** reflection-engine-deduplication-fix-2026-01-10
**Rationale:** This was a critical bug fix that prevented the reflection system from working properly - the learning about recording skipped reflections is essential for system stability

### 2026-01-10 14:07 - Correction
**Signal:** "Fixed critical infinite loop bug in reflection engine where stop hook repeatedly detected same signals. Root cause: NEW_SKILL reflections (signals for already-implemented features) were filtered out but never recorded in database, causing re-detection on every run."
**What Changed:** Added _record_skipped_reflection() method to record filtered reflections with reviewed_by='auto-skipped' to prevent infinite loops
**Confidence:** High
**Source:** reflection-engine-deduplication-fix-2026-01-10
**Rationale:** Critical bug fix that prevents infinite loops in reflection engine - this is a core operational requirement that must be documented

### 2026-01-10 14:07 - Correction
**Signal:** "Fixed critical infinite loop bug in reflection engine where stop hook repeatedly detected same signals. Root cause: NEW_SKILL reflections (signals for already-implemented features) were filtered out but never recorded in database, causing re-detection on every run."
**What Changed:** Implemented _record_skipped_reflection() method to record filtered reflections with reviewed_by='auto-skipped' to prevent infinite loops
**Confidence:** High
**Source:** reflection-engine-deduplication-fix-2026-01-10
**Rationale:** Critical bug fix that prevents infinite loops in reflection engine - this is a core architectural pattern that must be preserved

### 2026-01-10 14:02 - Correction
**Signal:** "Fixed critical infinite loop bug in reflection engine where stop hook repeatedly detected same signals. Root cause: NEW_SKILL reflections (signals for already-implemented features) were filtered out but never recorded in database, causing re-detection on every run."
**What Changed:** Added _record_skipped_reflection() method to record filtered reflections with reviewed_by='auto-skipped' to prevent infinite loops
**Confidence:** High
**Source:** reflection-engine-deduplication-fix-2026-01-10
**Rationale:** Critical bug fix that prevents infinite loops in the reflection system - essential for system stability

### 2026-01-10 13:59 - Correction
**Signal:** "Fixed critical infinite loop bug in reflection engine where stop hook repeatedly detected same signals. Root cause: NEW_SKILL reflections (signals for already-implemented features) were filtered out but never recorded in database, causing re-detection on every run."
**What Changed:** Fixed infinite loop by recording filtered reflections with reviewed_by='auto-skipped' and implementing _record_skipped_reflection() method
**Confidence:** High
**Source:** reflection-engine-deduplication-fix-2026-01-10
**Rationale:** This was a critical bug that caused infinite loops in the reflection engine - the fix represents important learning about proper signal deduplication that should be documented

### 2026-01-10 13:58 - Correction
**Signal:** "Fixed critical infinite loop bug in reflection engine where stop hook repeatedly detected same signals. Root cause: NEW_SKILL reflections (signals for already-implemented features) were filtered out but never recorded in database, causing re-detection on every run."
**What Changed:** Implemented _record_skipped_reflection() method to record filtered reflections with reviewed_by='auto-skipped' and added signal deduplication system
**Confidence:** High
**Source:** reflection-engine-deduplication-fix-2026-01-10
**Rationale:** Critical bug fix that prevents reflection engine from getting stuck in infinite loops - this is a core functionality issue that needs to be documented to prevent regression

### 2026-01-10 13:57 - Correction
**Signal:** "Fixed critical infinite loop bug in reflection engine where stop hook repeatedly detected same signals. Root cause: NEW_SKILL reflections (signals for already-implemented features) were filtered out but never recorded in database, causing re-detection on every run."
**What Changed:** Added _record_skipped_reflection() method to record filtered reflections with reviewed_by='auto-skipped' to prevent infinite loops
**Confidence:** High
**Source:** reflection-engine-deduplication-fix-2026-01-10
**Rationale:** This was a critical bug that caused infinite loops - the fix represents a fundamental pattern for how the reflection system should handle filtered signals

### 2026-01-10 13:57 - Correction
**Signal:** "Fixed critical infinite loop bug in reflection engine where stop hook repeatedly detected same signals. Root cause: NEW_SKILL reflections (signals for already-implemented features) were filtered out but never recorded in database, causing re-detection on every run."
**What Changed:** Added database recording for filtered reflections to prevent infinite loops
**Confidence:** High
**Source:** reflection-engine-deduplication-fix-2026-01-10
**Rationale:** Critical bug fix that prevents system from functioning - this pattern will occur whenever reflection engine filters signals without recording them

### 2026-01-10 13:51 - Correction
**Signal:** "Fixed critical infinite loop bug in reflection engine where stop hook repeatedly detected same signals. Root cause: NEW_SKILL reflections (signals for already-implemented features) were filtered out but never recorded in database, causing re-detection on every run."
**What Changed:** Added _record_skipped_reflection() method to record filtered reflections with reviewed_by='auto-skipped'
**Confidence:** High
**Source:** reflection-engine-deduplication-fix-2026-01-10
**Rationale:** This was a critical bug causing infinite loops - the reflection engine must record all processed signals, even filtered ones, to maintain proper deduplication

### 2026-01-10 13:50 - Correction
**Signal:** "Fixed critical infinite loop bug in reflection engine where stop hook repeatedly detected same signals. Root cause: NEW_SKILL reflections (signals for already-implemented features) were filtered out but never recorded in database, causing re-detection on every run."
**What Changed:** Added _record_skipped_reflection() method to record filtered reflections with reviewed_by='auto-skipped' to prevent infinite loops
**Confidence:** High
**Source:** reflection-engine-deduplication-fix-2026-01-10
**Rationale:** Critical bug fix that prevents infinite loops in the reflection system - this is a core architectural requirement that must be documented

### 2026-01-10 13:46 - Correction
**Signal:** "Fixed critical infinite loop bug in reflection engine where stop hook repeatedly detected same signals"
**What Changed:** Reflection engine was creating infinite loops by not recording filtered reflections, causing re-detection of same signals
**Confidence:** High
**Source:** reflection-engine-deduplication-fix-2026-01-10
**Rationale:** Critical bug fix that prevents infinite loops in reflection system - this is a core architectural issue that must be documented to prevent regression

### 2026-01-10 13:44 - Correction
**Signal:** "Fixed critical infinite loop bug in reflection engine where stop hook repeatedly detected same signals. Root cause: NEW_SKILL reflections (signals for already-implemented features) were filtered out but never recorded in database, causing re-detection on every run."
**What Changed:** Added _record_skipped_reflection() method to record filtered reflections with reviewed_by='auto-skipped' and prevent infinite loops
**Confidence:** High
**Source:** reflection-engine-deduplication-fix-2026-01-10
**Rationale:** This was a critical bug fix that reveals a fundamental requirement for the reflection system - all signals must be recorded even when filtered to prevent infinite loops

### 2026-01-10 13:41 - Correction
**Signal:** "Fixed critical infinite loop bug in reflection engine where stop hook repeatedly detected same signals. Root cause: NEW_SKILL reflections (signals for already-implemented features) were filtered out but never recorded in database, causing re-detection on every run."
**What Changed:** Added _record_skipped_reflection() method to record filtered reflections with reviewed_by='auto-skipped' to prevent infinite loops
**Confidence:** High
**Source:** reflection-engine-deduplication-fix-2026-01-10
**Rationale:** Critical bug fix that prevents infinite loops in the reflection system - this is a fundamental operational requirement that must be documented to prevent regression

### 2026-01-10 13:40 - Correction
**Signal:** "Fixed critical infinite loop bug in reflection engine where stop hook repeatedly detected same signals. Root cause: NEW_SKILL reflections (signals for already-implemented features) were filtered out but never recorded in database, causing re-detection on every run."
**What Changed:** Fixed infinite loop by recording filtered reflections with reviewed_by='auto-skipped' and implementing proper deduplication
**Confidence:** High
**Source:** reflection-engine-deduplication-fix-2026-01-10
**Rationale:** Critical bug fix that prevents infinite loops in reflection engine - this is a fundamental operational requirement that should be documented to prevent regression

### 2026-01-10 13:27 - Correction
**Signal:** "Fixed critical infinite loop bug in reflection engine where stop hook repeatedly detected same signals. Root cause: NEW_SKILL reflections (signals for already-implemented features) were filtered out but never recorded in database, causing re-detection on every run."
**What Changed:** Added _record_skipped_reflection() method to record filtered reflections with reviewed_by='auto-skipped' to prevent infinite loops
**Confidence:** High
**Source:** reflection-engine-deduplication-fix-2026-01-10
**Rationale:** Critical bug fix that prevents infinite loops in reflection engine - this is a core requirement for the skill to function properly

### 2026-01-10 13:25 - Correction
**Signal:** "Fixed critical infinite loop bug in reflection engine where stop hook repeatedly detected same signals. Root cause: NEW_SKILL reflections (signals for already-implemented features) were filtered out but never recorded in database, causing re-detection on every run."
**What Changed:** Added _record_skipped_reflection() method to record filtered reflections with reviewed_by='auto-skipped' to prevent infinite loops
**Confidence:** High
**Source:** reflection-engine-deduplication-fix-2026-01-10
**Rationale:** Critical bug fix that prevents infinite loops in reflection engine - this is a fundamental operational requirement that must be documented to prevent regression

### 2026-01-10 13:24 - Correction
**Signal:** "Fixed critical infinite loop bug in reflection engine where stop hook repeatedly detected same signals"
**What Changed:** Reflection engine was getting stuck in infinite loops due to filtered NEW_SKILL reflections not being recorded in database, causing re-detection on every run
**Confidence:** High
**Source:** reflection-engine-deduplication-fix-2026-01-10
**Rationale:** This is a critical bug fix that prevents infinite loops in the reflection system - essential for system stability

### 2026-01-10 13:16 - Correction
**Signal:** "Fixed critical infinite loop bug in reflection engine where stop hook repeatedly detected same signals. Root cause: NEW_SKILL reflections (signals for already-implemented features) were filtered out but never recorded in database, causing re-detection on every run."
**What Changed:** Filtered reflections must be recorded in database to prevent infinite loops
**Confidence:** High
**Source:** reflection-engine-deduplication-fix-2026-01-10
**Rationale:** Critical bug fix that prevents infinite loops in the reflection engine - this is a core technical requirement for the system to function properly

### 2026-01-10 13:03 - Correction
**Signal:** "Fixed critical infinite loop bug in reflection engine where stop hook repeatedly detected same signals. Root cause: NEW_SKILL reflections (signals for already-implemented features) were filtered out but never recorded in database, causing re-detection on every run."
**What Changed:** Added _record_skipped_reflection() method to record filtered reflections with reviewed_by='auto-skipped' and implemented signal deduplication system
**Confidence:** High
**Source:** reflection-engine-deduplication-fix-2026-01-10
**Rationale:** Critical bug fix that prevents infinite loops - essential knowledge for anyone maintaining or using the reflection system

### 2026-01-10 12:50 - Correction
**Signal:** "Fixed critical infinite loop bug in reflection engine where stop hook repeatedly detected same signals. Root cause: NEW_SKILL reflections (signals for already-implemented features) were filtered out but never recorded in database, causing re-detection on every run."
**What Changed:** Added _record_skipped_reflection() method to record filtered reflections with reviewed_by='auto-skipped' and implemented proper signal deduplication
**Confidence:** High
**Source:** reflection-engine-deduplication-fix-2026-01-10
**Rationale:** Critical bug fix that prevents infinite loops - this pattern will likely recur if not documented properly in the reflect skill

### 2026-01-10 12:47 - Correction
**Signal:** "Fixed critical infinite loop bug in reflection engine where stop hook repeatedly detected same signals. Root cause: NEW_SKILL reflections (signals for already-implemented features) were filtered out but never recorded in database, causing re-detection on every run."
**What Changed:** Added _record_skipped_reflection() method to record filtered reflections with reviewed_by='auto-skipped' and prevent infinite loops from unrecorded filtered signals
**Confidence:** High
**Source:** reflection-engine-deduplication-fix-2026-01-10
**Rationale:** Critical bug fix that prevents infinite loops in reflection engine - this is a core operational requirement that must be documented to prevent regression

### 2026-01-10 12:32 - Correction
**Signal:** "Fixed critical infinite loop bug in reflection engine where stop hook repeatedly detected same signals. Root cause: NEW_SKILL reflections (signals for already-implemented features) were filtered out but never recorded in database, causing re-detection on every run."
**What Changed:** Added _record_skipped_reflection() method to record filtered reflections with reviewed_by='auto-skipped' to prevent infinite loops
**Confidence:** High
**Source:** reflection-engine-deduplication-fix-2026-01-10
**Rationale:** Critical bug fix that prevents infinite loops in the reflection engine - this is a fundamental correctness issue that must be documented to prevent regression

### 2026-01-10 12:19 - Correction
**Signal:** "Fixed critical infinite loop bug in reflection engine where stop hook repeatedly detected same signals. Root cause: NEW_SKILL reflections (signals for already-implemented features) were filtered out but never recorded in database, causing re-detection on every run."
**What Changed:** Added _record_skipped_reflection() method to record filtered reflections with reviewed_by='auto-skipped' to prevent infinite loops
**Confidence:** High
**Source:** reflection-engine-deduplication-fix-2026-01-10
**Rationale:** Critical bug fix that prevents infinite loops in reflection engine - this is core functionality that must be documented to prevent regression

### 2026-01-10 12:10 - Correction
**Signal:** "Fixed critical infinite loop bug in reflection engine where stop hook repeatedly detected same signals. Root cause: NEW_SKILL reflections (signals for already-implemented features) were filtered out but never recorded in database, causing re-detection on every run."
**What Changed:** Implemented _record_skipped_reflection() method to record filtered reflections with reviewed_by='auto-skipped' to prevent infinite loops
**Confidence:** High
**Source:** reflection-engine-deduplication-fix-2026-01-10
**Rationale:** Critical bug fix that prevents infinite loops in the reflection system - this is a fundamental requirement for the reflect skill to function properly

### 2026-01-10 12:08 - Correction
**Signal:** "Fixed critical infinite loop bug in reflection engine where stop hook repeatedly detected same signals. Root cause: NEW_SKILL reflections (signals for already-implemented features) were filtered out but never recorded in database, causing re-detection on every run."
**What Changed:** Added _record_skipped_reflection() method to record filtered reflections with reviewed_by='auto-skipped' to prevent infinite loops
**Confidence:** High
**Source:** reflection-engine-deduplication-fix-2026-01-10
**Rationale:** This was a critical bug causing infinite loops - the reflection engine needs to properly handle and record skipped reflections to maintain state consistency

### 2026-01-10 11:59 - Correction
**Signal:** "Fixed critical infinite loop bug in reflection engine where stop hook repeatedly detected same signals. Root cause: NEW_SKILL reflections (signals for already-implemented features) were filtered out but never recorded in database, causing re-detection on every run."
**What Changed:** Added _record_skipped_reflection() method to record filtered reflections with reviewed_by='auto-skipped' to prevent infinite loops
**Confidence:** High
**Source:** reflection-engine-deduplication-fix-2026-01-10
**Rationale:** Critical bug fix that prevents infinite loops in the reflection system - this is a core architectural requirement that must be documented to prevent regression

### 2026-01-10 11:55 - Correction
**Signal:** "Fixed critical infinite loop bug in reflection engine where stop hook repeatedly detected same signals. Root cause: NEW_SKILL reflections (signals for already-implemented features) were filtered out but never recorded in database, causing re-detection on every run."
**What Changed:** Implemented _record_skipped_reflection() method to record filtered reflections with reviewed_by='auto-skipped' to prevent infinite loops
**Confidence:** High
**Source:** reflection-engine-deduplication-fix-2026-01-10
**Rationale:** This was a critical bug fix that addresses a fundamental flaw in the reflection system - filtered signals must still be recorded to prevent re-detection

### 2026-01-10 11:37 - Correction
**Signal:** "Fixed critical infinite loop bug in reflection engine where stop hook repeatedly detected same signals. Root cause: NEW_SKILL reflections (signals for already-implemented features) were filtered out but never recorded in database, causing re-detection on every run."
**What Changed:** Implemented _record_skipped_reflection() method to record filtered reflections with reviewed_by='auto-skipped' to prevent infinite loops
**Confidence:** High
**Source:** reflection-engine-deduplication-fix-2026-01-10
**Rationale:** This was a critical bug that caused infinite loops - the reflection system must handle skipped reflections properly to prevent re-processing the same signals

### 2026-01-10 11:27 - Correction
**Signal:** "Fixed critical infinite loop bug in reflection engine where stop hook repeatedly detected same signals. Root cause: NEW_SKILL reflections (signals for already-implemented features) were filtered out but never recorded in database, causing re-detection on every run."
**What Changed:** Added _record_skipped_reflection() method to record filtered reflections and prevent infinite loops
**Confidence:** High
**Source:** reflection-engine-deduplication-fix-2026-01-10
**Rationale:** Critical bug fix that prevents reflection engine from entering infinite loops - this is a core operational requirement for the reflect skill

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

## Database Schema

Reflections are tracked in `skill_reflections` table:

```sql
SELECT skill_name, confidence, what_changed, applied_at
FROM skill_reflections
ORDER BY applied_at DESC
LIMIT 5;
```

## Git Integration

Each reflection creates a separate git commit:

```bash
# View skill evolution
git log --oneline .claude/skills/verify-official.md

# Show specific reflection commit
git show abc123f4

# Rollback a reflection (if needed)
git revert abc123f4
```

## Your Task

Execute the reflection engine with user's parameters:

```bash
python3 /home/ndninja/scripts/reflection_engine/main.py \
  ${session_id:+--session "$session_id"} \
  ${skill:+--skill "$skill"} \
  ${dry_run:+--dry-run} \
  ${auto_approve:+--auto-approve}
```

The script will:
1. Query conversation_summaries database
2. Detect correction signals
3. Analyze with LLM Council
4. Show proposed skill updates
5. Ask for approval (unless --auto-approve with high confidence)
6. Apply updates and git commit
7. Record in skill_reflections table

Return summary of applied reflections to user.

## AuDHD-Friendly Features

**Reduces Repetition Anxiety:**
- Never repeat the same correction twice
- Clear confirmation that learning was saved
- Git history proves the correction stuck

**Executive Function Support:**
- Automatic detection (don't have to remember to reflect)
- Structured approval process (not overwhelming)
- Preview before applying (review before commit)

**Hyperfocus Accommodation:**
- Can batch process multiple corrections
- --dry-run lets you explore without commitment
- Git rollback if you change your mind

**Working Memory Relief:**
- Corrections are permanently stored
- Don't have to hold patterns in mind
- Skills improve automatically over time

## Integration with Other Systems

**Works with:**
- Conversation summaries database (source data)
- LLM Council (multi-model consensus)
- Git version control (change tracking)
- All existing skills (universal improvement)

**Future enhancements:**
- Automatic reflection via Stop hook (Phase 2)
- /evolution-report skill (Phase 3)
- Cross-skill learning patterns
- Community reflection sharing

## Troubleshooting

**No signals detected:**
- Check if conversation summaries exist in database
- Verify corrections were explicit enough
- Try --days flag to look back further
- Use --dry-run to see what would be detected

**LLM Council timeout:**
- Council analysis can take 30-60 seconds
- Check that council script is working: `/home/ndninja/projects/llm-council/run_council.sh`
- Reduce number of signals being analyzed

**Skill file not found:**
- Ensure skill exists in `/home/ndninja/.claude/skills/`
- Check spelling of --skill parameter
- Create skill first if it's a NEW_SKILL suggestion

**Git commit failed:**
- Check git status: `git status`
- Ensure no conflicts in skill file
- Verify git is configured properly

## Success Metrics

Track effectiveness over time:
- Reduction in repeated corrections (target: 70%)
- Skill update frequency (healthy: 2-3 per week)
- Confidence distribution (target: 80% high-confidence)
- User satisfaction with learnings

Query metrics:
```sql
SELECT
  skill_name,
  COUNT(*) as reflection_count,
  AVG(effectiveness_score) as avg_rating
FROM skill_reflections
WHERE applied_at >= NOW() - INTERVAL '30 days'
GROUP BY skill_name
ORDER BY reflection_count DESC;
```

## Version History

- v1.0.0 (2026-01-05): Initial release - Phase 1 MVP
  - Manual reflection with /reflect command
  - Signal detection from conversations
  - LLM Council analysis
  - Skill file updates with Learnings section
  - Git commit integration
  - Database tracking
