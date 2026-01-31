# Ninja Assist - Requirements

## Functional Requirements

### REQ-001: Plain Language Input
- System MUST accept natural language requests
- System MUST NOT require specific command syntax
- Examples: "help me code X", "research Y", "update Z"

### REQ-002: Intent Classification
- System MUST classify intents into: code, research, install/update, design/brainstorm
- Classification MUST work without LLM calls for common patterns
- Fallback to LLM for ambiguous requests

### REQ-003: Tool Routing
- System MUST route classified intents to appropriate tools
- Routing MUST be configurable/extensible
- User MUST NOT need to know tool names

### REQ-004: Context Awareness
- System MUST track current project context
- System MUST remember recent actions
- Context MUST persist across sessions

### REQ-005: Proactive Assistance
- System SHOULD surface pending tasks during heartbeats
- System SHOULD remind about incomplete work
- Notifications MUST be respectful (not spammy)

## Non-Functional Requirements

### REQ-010: Token Efficiency
- Pattern matching layer MUST use zero tokens
- State files MUST be small and fast to read
- Full LLM ONLY for complex/ambiguous requests

### REQ-011: Neurodivergent-Friendly
- NO multi-step manual processes
- NO requirement to remember commands
- MUST reduce cognitive load, not add to it
- MUST NOT make user feel stupid

### REQ-012: Automation First
- If it CAN be automated, it MUST be automated
- Manual steps = failure points for ADHD
- End-to-end automation is the goal

## Success Metrics
- User never needs to type a tool/command name
- 80%+ of requests handled by pattern matching (no LLM)
- Positive emotional response (no frustration)
