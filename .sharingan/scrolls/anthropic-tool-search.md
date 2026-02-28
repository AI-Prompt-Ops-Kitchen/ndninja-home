# Anthropic Tool Calling 2.0 — Sharingan Scroll
**Mastery:** 1-Tomoe (documented, not yet needed in production)
**Last updated:** 2026-02-27
**Sources:** Anthropic docs, Anbu intel report (Feb 27, 2026)

---

## Overview
Anthropic's Tool Calling 2.0 introduces three features for managing large tool sets: **Tool Search** (deferred loading), **Programmatic Tool Calling**, and **Dynamic Filtering**. These matter when a Claude session has dozens of MCP tools and you want to reduce prompt bloat and improve routing accuracy.

## Feature 1: Tool Search (Deferred Loading)

### What It Does
Instead of injecting all tool schemas into every prompt, Tool Search lets Claude discover tools on demand. Tools are indexed server-side; Claude issues a `tool_search` call when it needs a capability, and only matching tool schemas get loaded into context.

### Configuration
```json
{
  "tool_choice": {
    "type": "auto",
    "disable_search_tool": false
  },
  "tools": [
    {
      "type": "server_tool",
      "name": "tool_search",
      "description": "Search for available tools by capability"
    }
  ]
}
```

### When It Helps
- **Many tools (20+):** Reduces prompt token usage significantly
- **Multi-MCP setups:** When tools from different servers overlap in naming
- **Dynamic environments:** Tools that come and go (e.g., per-user plugins)

### When to Skip
- **< 10 tools:** The overhead of search-then-call is worse than just loading all schemas
- **Latency-sensitive:** Adds one extra round-trip per new tool discovery
- **Our current setup:** We have ~1 MCP server (Remotion Media). Not worth it yet.

## Feature 2: Programmatic Tool Calling

### What It Does
Forces Claude to always respond with a tool call (never plain text). Useful for building structured pipelines where you want guaranteed structured output.

### Configuration
```json
{
  "tool_choice": {
    "type": "tool",
    "name": "specific_tool_name"
  }
}
```

Or force ANY tool (but must use one):
```json
{
  "tool_choice": {
    "type": "any"
  }
}
```

### Use Cases
- **Pipeline automation:** Ensure every response triggers an action
- **Structured extraction:** Force output through a schema-validated tool
- **Agent loops:** Guarantee the agent always takes a step (no "I'll just explain...")

## Feature 3: Dynamic Filtering

### What It Does
Per-request tool filtering — send the full tool set once, then include/exclude tools per message based on conversation state.

### Configuration
```json
{
  "tool_choice": {
    "type": "auto",
    "allowed_tools": ["tool_a", "tool_b"]
  }
}
```

### Use Cases
- **Workflow stages:** Only expose "draft" tools during drafting, "publish" tools during review
- **Permission scoping:** Restrict tools based on user role
- **Cost control:** Disable expensive tools until user explicitly enables them

## When This Becomes Relevant for Us

| Trigger | Action |
|---------|--------|
| Add Rasengan MCP server | Consider Tool Search to manage tool overlap |
| Add Dojo MCP server | Dynamic filtering to scope pipeline vs review tools |
| Build Glitch agent (AuDHD assistant) | Programmatic tool calling for structured responses |
| Tool count exceeds 20 | Tool Search saves meaningful token budget |

## Current Status: DEFER

Our setup has 1 MCP server (Remotion Media) with ~12 tools. Tool Search overhead > benefit. Revisit when we add Rasengan MCP or Dojo MCP servers, or when total tool count crosses 20.

## API Reference

- Docs: `https://docs.anthropic.com/en/docs/build-with-claude/tool-use`
- Tool search: Part of Messages API `tool_choice` parameter
- Minimum model: Claude 3.5 Sonnet or newer
