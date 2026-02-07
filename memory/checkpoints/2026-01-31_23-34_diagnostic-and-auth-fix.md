# Checkpoint: Diagnostic & Auth Fix
> Created: 2026-01-31 23:34 EST (before compaction at 68% context)

## Session Summary
Tonight's session focused on system diagnostics and fixing an auth issue.

## What We Did

### 1. Full System Diagnostic
Ran comprehensive checks on:
- Gateway status (running, pid 7484)
- Channel health (WhatsApp OK, Signal/iMessage not ready)
- Memory/disk (plenty of space)
- Claude CLI auth status

### 2. Fixed Claude CLI Auth Expiration
**Problem:** Claude CLI OAuth token was expiring in ~3 hours, `claude setup-token` link wasn't working on headless server.

**Solution:** Added Anthropic API key as fallback provider:
- Found key in `~/.bashrc` and project .env files
- Patched config: `models.providers.anthropic.apiKey`
- Gateway auto-restarted with new config

**Result:** When OAuth expires, API key kicks in automatically. No more manual token refresh needed.

### 3. Session State After Changes
- Gateway running, WhatsApp connected
- Context at 68% (137k/200k)
- API key fallback configured and tested
- OAuth still has ~2h left, then seamless failover

## Key Config Change
```json
{
  "models": {
    "providers": {
      "anthropic": {
        "baseUrl": "https://api.anthropic.com",
        "apiKey": "sk-ant-api03-...",
        "auth": "api-key",
        "api": "anthropic-messages",
        "models": []
      }
    }
  }
}
```

## Outstanding Minor Issues (unchanged)
- Signal daemon not running (HTTP 404)
- iMessage `imsg` CLI not found (expected on Linux)
- System Node 20.x, using nvm 22.22.0 (works fine)
- Gateway service uses nvm path (could break on nvm upgrade)

## Files Modified
- `~/.clawdbot/clawdbot.json` - Added Anthropic API key provider

## Next Session Notes
- Auth should "just work" now
- If you see OAuth warnings in `clawdbot doctor`, ignore them — API key fallback is active
- Context was at 68% when this checkpoint was created
