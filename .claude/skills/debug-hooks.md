---
name: debug-hooks
description: Debug Claude Code plugin hooks and event-driven behaviors
version: 1.0.0
category: debugging
args: ["[--hook-type]", "[--plugin-name]"]
when_to_use: "User reports hooks not triggering, block actions returning warnings instead of denials, or unexpected hook behavior in Claude Code plugins."
tags: [debugging, hooks, plugins, claude-code, event-driven]
---

# Debug Claude Code Plugin Hooks

Diagnose and fix Claude Code plugin hook issues, including hooks not triggering, incorrect event handling, and block/warn behaviors.

## Hook System Overview

**Claude Code Hooks** are event-driven callbacks that execute at specific points:

- **PreToolUse**: Before a tool is executed (can block/warn/modify)
- **PostToolUse**: After a tool completes (can analyze/log)
- **Stop**: When a conversation session ends
- **SubagentStop**: When a subagent finishes
- **SessionStart**: When a new session begins
- **SessionEnd**: When a session ends
- **UserPromptSubmit**: After user submits a prompt
- **PreCompact**: Before conversation history is compacted
- **Notification**: For user notifications

## Common Hook Issues

### Issue 1: Hook Not Triggering

**Symptoms:**
- Hook script exists but never runs
- No output/logs from hook
- Expected blocking doesn't happen

**Common Causes:**
1. `hook_event_name` not set in response
2. Hook not registered in plugin.json
3. Script not executable (`chmod +x`)
4. Script has syntax errors
5. Wrong hook type for desired behavior

### Issue 2: Block Action Returns Warning

**Symptoms:**
- Hook returns `"action": "block"` but tool still executes
- Gets warning instead of denial
- User sees "⚠️" instead of "❌"

**Root Cause:** `hook_event_name` field missing in response

**Fix:**
```json
{
  "action": "block",
  "hook_event_name": "PreToolUse",  // ← CRITICAL
  "message": "This operation is blocked",
  "details": "Reason for blocking"
}
```

### Issue 3: Hook Runs But Doesn't Block

**Symptoms:**
- Hook executes and logs show it ran
- Returns block action
- Tool still executes anyway

**Debugging Steps:**
1. Check if hook is PreToolUse (only PreToolUse can block)
2. Verify JSON is valid
3. Check `hook_event_name` matches actual event
4. Ensure exit code is 0 (non-zero = hook failure)

## Diagnostic Workflow

### Step 1: Verify Hook Registration

```bash
# Check plugin.json
cat ~/.claude/plugins/<plugin-name>/plugin.json | jq '.hooks'

# Should show:
{
  "PreToolUse": ["hooks/pre-tool-use.sh"],
  "Stop": ["hooks/on-stop.sh"]
}
```

**Common mistakes:**
- Path is relative to plugin root
- Missing executable permission
- Typo in hook event name

### Step 2: Test Hook Manually

```bash
# Make hook executable
chmod +x ~/.claude/plugins/<plugin-name>/hooks/pre-tool-use.sh

# Set required environment variables
export CLAUDE_PLUGIN_ROOT="$HOME/.claude/plugins/<plugin-name>"
export TOOL_NAME="Bash"
export TOOL_ARGS='{"command": "rm -rf /"}'

# Run hook manually
~/.claude/plugins/<plugin-name>/hooks/pre-tool-use.sh
```

**Check:**
- Exit code: `echo $?` (should be 0)
- Output: Should be valid JSON
- `hook_event_name`: Must match hook type

### Step 3: Enable Hook Debugging

```bash
# Add debugging to hook script
#!/bin/bash
set -x  # Enable bash debugging

# Log to file
exec 2>> /tmp/hook-debug.log

echo "Hook triggered: $(date)" >&2
echo "Tool: $TOOL_NAME" >&2
echo "Args: $TOOL_ARGS" >&2

# Your hook logic here
```

**Watch logs:**
```bash
tail -f /tmp/hook-debug.log
```

### Step 4: Validate JSON Response

**Hook response MUST be valid JSON:**

```json
{
  "action": "block",
  "hook_event_name": "PreToolUse",
  "message": "Operation blocked",
  "details": "Specific reason why"
}
```

**Test JSON validity:**
```bash
# In your hook script
response='{...}'
echo "$response" | jq . > /dev/null || echo "Invalid JSON" >&2
echo "$response"
```

**Common JSON mistakes:**
- Missing quotes around strings
- Trailing commas
- Unescaped quotes in message
- Missing `hook_event_name`

### Step 5: Check Hook Permissions

```bash
# Verify executable permission
ls -la ~/.claude/plugins/<plugin-name>/hooks/

# Should show: -rwxr-xr-x (executable)
# If not:
chmod +x ~/.claude/plugins/<plugin-name>/hooks/*.sh
```

### Step 6: Test with Simple Hook

Create minimal test hook:

```bash
#!/bin/bash
# test-hook.sh - Minimal blocking hook

cat <<'EOF'
{
  "action": "block",
  "hook_event_name": "PreToolUse",
  "message": "Test block",
  "details": "This is a test"
}
EOF
```

Register in plugin.json:
```json
{
  "hooks": {
    "PreToolUse": ["hooks/test-hook.sh"]
  }
}
```

Test:
```bash
# Try running any tool - should be blocked
/debug-hooks --plugin-name test-plugin
```

## Fix Patterns

### Pattern 1: Add hook_event_name

**Before (doesn't block):**
```bash
#!/bin/bash
cat <<EOF
{
  "action": "block",
  "message": "Blocked"
}
EOF
```

**After (blocks correctly):**
```bash
#!/bin/bash
cat <<EOF
{
  "action": "block",
  "hook_event_name": "PreToolUse",
  "message": "Blocked"
}
EOF
```

### Pattern 2: Proper Error Handling

**Before (fails silently):**
```bash
#!/bin/bash
# If analysis fails, returns nothing
result=$(some-complex-analysis)
echo "$result"
```

**After (graceful degradation):**
```bash
#!/bin/bash
set -euo pipefail

# If analysis fails, allow with warning
result=$(some-complex-analysis 2>/dev/null) || {
  cat <<EOF
{
  "action": "warn",
  "hook_event_name": "PreToolUse",
  "message": "Analysis failed - proceeding with caution"
}
EOF
  exit 0
}

echo "$result"
```

### Pattern 3: Conditional Blocking

**Example: Block only specific commands**
```bash
#!/bin/bash

# Parse tool args
COMMAND=$(echo "$TOOL_ARGS" | jq -r '.command')

# Check for dangerous patterns
if echo "$COMMAND" | grep -qE "(rm -rf|mkfs|dd|fdisk)"; then
  cat <<EOF
{
  "action": "block",
  "hook_event_name": "PreToolUse",
  "message": "Dangerous command blocked",
  "details": "Command matches dangerous pattern: $COMMAND"
}
EOF
else
  cat <<EOF
{
  "action": "allow",
  "hook_event_name": "PreToolUse"
}
EOF
fi
```

### Pattern 4: Multi-line Bash Command Issue

**Problem:** Claude Code rejects multi-line bash commands in plugins

**Symptoms:**
- Permission prompts even with whitelisted commands
- Commands work in terminal but not in skills/hooks
- Error: "Multi-line commands require user approval"

**Root Cause:** Claude Code security model blocks multi-line bash

**Fix:** Use semicolons or `&&` instead of newlines
```bash
# BAD (triggers permission prompt)
cat <<'EOF'
cd /some/path
ls -la
grep pattern
EOF

# GOOD (works without prompt)
cd /some/path && ls -la && grep pattern
```

### Pattern 5: Environment Variable Access

**Hook scripts have access to:**
```bash
$CLAUDE_PLUGIN_ROOT    # Plugin directory
$TOOL_NAME             # Tool being called (e.g., "Bash")
$TOOL_ARGS             # Tool arguments as JSON string
$USER                  # Current user
$HOME                  # Home directory
```

**Parse tool args:**
```bash
#!/bin/bash

# Extract command from Bash tool
if [ "$TOOL_NAME" = "Bash" ]; then
  COMMAND=$(echo "$TOOL_ARGS" | jq -r '.command')
  echo "Command: $COMMAND" >&2
fi
```

## Testing Checklist

Before deploying a hook:

- [ ] Hook script is executable (`chmod +x`)
- [ ] Registered in plugin.json under correct event
- [ ] Returns valid JSON (test with `jq`)
- [ ] Includes `hook_event_name` field
- [ ] Exit code is 0 on success
- [ ] Tested manually with real env vars
- [ ] Logs to file for debugging
- [ ] Graceful error handling
- [ ] No multi-line bash commands in output

## Debugging Tools

**1. Hook Test Harness**
```bash
#!/bin/bash
# test-hook-harness.sh

PLUGIN_NAME="$1"
HOOK_TYPE="$2"  # PreToolUse, PostToolUse, etc.
HOOK_SCRIPT="$HOME/.claude/plugins/$PLUGIN_NAME/hooks/$3"

export CLAUDE_PLUGIN_ROOT="$HOME/.claude/plugins/$PLUGIN_NAME"
export TOOL_NAME="Bash"
export TOOL_ARGS='{"command": "ls", "description": "test"}'

echo "Testing hook: $HOOK_SCRIPT"
echo "Event type: $HOOK_TYPE"
echo "---"

output=$("$HOOK_SCRIPT" 2>&1)
exit_code=$?

echo "Exit code: $exit_code"
echo "Output:"
echo "$output"
echo "---"

# Validate JSON
if echo "$output" | jq . > /dev/null 2>&1; then
  echo "✓ Valid JSON"

  # Check for hook_event_name
  if echo "$output" | jq -e '.hook_event_name' > /dev/null; then
    echo "✓ hook_event_name present"
  else
    echo "✗ hook_event_name MISSING"
  fi
else
  echo "✗ Invalid JSON"
fi
```

**2. Live Hook Monitoring**
```bash
# Monitor all hook activity
tail -f ~/.claude/logs/hooks.log

# Or add to each hook:
echo "$(date) - Hook triggered" >> ~/.claude/logs/hook-activity.log
```

## Common Scenarios

### Scenario 1: Hookify Plugin Not Blocking

**Issue:** Created hookify rule but commands still execute

**Debug:**
```bash
# Check if hook is registered
cat ~/.claude/plugins/hookify/plugin.json | jq '.hooks.PreToolUse'

# Test hook manually
export TOOL_NAME="Bash"
export TOOL_ARGS='{"command": "rm -rf test"}'
~/.claude/plugins/hookify/hooks/pre-tool-use.sh
```

**Fix:** Ensure hook response includes `hook_event_name`

### Scenario 2: Stop Hook Not Running

**Issue:** Stop hook doesn't execute when session ends

**Debug:**
```bash
# Verify registration
cat ~/.claude/plugins/<plugin>/plugin.json | jq '.hooks.Stop'

# Check if script exists and is executable
ls -la ~/.claude/plugins/<plugin>/hooks/on-stop.sh

# Test manually (no env vars needed for Stop)
~/.claude/plugins/<plugin>/hooks/on-stop.sh
```

**Fix:** Stop hooks run in background - check logs, don't expect immediate output

### Scenario 3: Hook Works Sometimes

**Issue:** Hook blocks correctly 50% of the time

**Root Cause:** Race condition or non-deterministic logic

**Debug:**
```bash
# Add timestamps to hook
echo "Hook start: $(date +%s.%N)" >&2
# ... hook logic ...
echo "Hook end: $(date +%s.%N)" >&2
```

**Fix:** Ensure hook logic is deterministic and doesn't depend on timing

## Output Format

```
🔍 Hook Debug Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Plugin: hookify
Hook Type: PreToolUse
Hook Script: hooks/pre-tool-use.sh

Status Checks:
  ✓ Hook registered in plugin.json
  ✓ Script exists
  ✓ Script is executable
  ✓ Returns valid JSON
  ✗ Missing 'hook_event_name' field  ← ISSUE FOUND

Test Execution:
  Command: rm -rf test
  Hook Response:
  {
    "action": "block",
    "message": "Dangerous command"
  }

Issue Identified:
  Response missing 'hook_event_name' field
  This causes block actions to be treated as warnings

Recommended Fix:
  Add to hook response:
  "hook_event_name": "PreToolUse"

Fixed Response:
  {
    "action": "block",
    "hook_event_name": "PreToolUse",
    "message": "Dangerous command"
  }
```

## Related Skills

- Plugin development skills - Creating hooks
- `/hookify` - Hook rule management
- `/plugin-dev:hook-development` - Hook development guide

---

## 🧠 Learnings (Auto-Updated)

### 2026-01-05 Initial - Correction
**Signal:** "hook_event_name wasn't being set, causing block actions to return warnings"
**What Changed:** Created skill documenting hook_event_name requirement
**Confidence:** High
**Source:** 2025-12-31-hookify-test
**Rationale:** Critical debugging pattern for Claude Code plugin development
