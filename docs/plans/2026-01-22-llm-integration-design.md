# LLM Integration Design for Sage Mode

**Date:** 2026-01-22
**Status:** Approved

## Overview

Replace mock agent implementations with real Claude API calls, enabling the 7 specialized agents to generate meaningful software development outputs.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Celery Task                              │
│                    execute_agent_task()                         │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Agent (e.g., BackendAgent)                 │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │ Role Config │  │ System Prompt│  │ Response Schema        │  │
│  │ (capabilities)│ │ (persona)    │  │ (BackendResponseSchema)│  │
│  └─────────────┘  └──────────────┘  └────────────────────────┘  │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     LLMClient (Abstract)                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  complete(prompt, schema) -> StructuredResponse          │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     ClaudeClient                                │
│  - API key from environment                                     │
│  - Uses claude-sonnet-4-20250514                                │
│  - JSON mode for structured output                              │
│  - Retry logic with exponential backoff                         │
└─────────────────────────────────────────────────────────────────┘
```

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| LLM Provider | Claude Sonnet 4 | Same cost as 3.5, better quality, abstraction layer for future Gemini |
| Response Format | Structured JSON | Predictable, type-safe, easy to store/display |
| Schema Design | Base + role-specific | Common fields (decisions) + specialized outputs per role |
| Prompts | Text files per role | Easy to edit, version controlled |
| Testing | Mock by default | Fast CI, integration tests opt-in |

## File Structure

```
sage_mode/
  llm/
    __init__.py
    client.py          # LLMClient abstract + ClaudeClient + MockLLMClient
    schemas.py         # Pydantic response schemas
    prompts/
      __init__.py      # Prompt loading utilities
      base.txt         # Common prompt template
      architect.txt
      backend.txt
      frontend.txt
      security.txt
      dba.txt
      uiux.txt
      itadmin.txt
```

## Response Schemas

### Base Schema (all agents)

```python
class BaseAgentResponse(BaseModel):
    analysis: str
    approach: str
    decisions: List[Decision]
    concerns: List[str]
    confidence: float  # 0.0-1.0
```

### Role-Specific Extensions

| Role | Additional Fields |
|------|-------------------|
| Architect | `architecture_patterns`, `component_diagram`, `tech_stack`, `integration_points` |
| Backend Dev | `endpoints`, `data_models`, `code_snippets`, `performance_notes` |
| Frontend Dev | `components`, `state_management`, `code_snippets`, `accessibility_notes` |
| Security | `vulnerabilities`, `risk_level`, `mitigations`, `compliance_notes` |
| DBA | `schema_changes`, `indexes`, `queries`, `migration_steps` |
| UI/UX | `user_flows`, `wireframe_description`, `design_tokens`, `accessibility_score` |
| IT Admin | `infrastructure`, `deployment_steps`, `monitoring_config`, `scaling_notes` |

## Cost Estimate

- **Model:** Claude Sonnet 4 ($3/MTok input, $15/MTok output)
- **Per agent:** ~2,000 input + ~1,500 output tokens = ~$0.03
- **Per session (7 agents):** ~$0.20
- **100 sessions/month:** ~$20

## Implementation Plan

### Phase 1: Foundation
1. Create `sage_mode/llm/` package structure
2. Implement response schemas (base + 7 roles)
3. Implement prompt templates (base + 7 roles)

### Phase 2: Client Implementation
4. Implement LLMClient abstract + MockLLMClient
5. Implement ClaudeClient
6. Add retry logic and error handling

### Phase 3: Agent Integration
7. Update BaseAgent with LLM support
8. Update all 7 agent subclasses

### Phase 4: Testing & Validation
9. Unit tests (mock client)
10. Integration tests (real Claude)
11. End-to-end session test

## Dependencies

```
# requirements.txt (add)
anthropic>=0.40.0
tenacity>=8.0.0
```

## Environment Variables

```bash
ANTHROPIC_API_KEY=sk-ant-...
USE_MOCK_LLM=false  # true for testing without API
```

## Testing Strategy

- **Unit tests:** MockLLMClient, always run, no API calls
- **Integration tests:** Real Claude, opt-in, marked with `@requires_api`
- **E2E tests:** Manual verification before release

## Future: Adding Gemini Fallback

The abstraction layer makes this straightforward:

```python
class GeminiClient(LLMClient):
    def complete(self, system_prompt, user_prompt, response_schema, ...):
        # Gemini implementation
        pass

class FallbackClient(LLMClient):
    def __init__(self, primary: LLMClient, fallback: LLMClient):
        self.primary = primary
        self.fallback = fallback

    def complete(self, ...):
        try:
            return self.primary.complete(...)
        except Exception:
            return self.fallback.complete(...)
```
