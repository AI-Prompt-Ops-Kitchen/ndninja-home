---
name: tdd
description: "Multi-agent Test-Driven Development — isolated subagents enforce Red-Green-Refactor discipline. Each phase runs in a fresh context to prevent implementation bias and context pollution."
---

# /tdd — Multi-Agent Test-Driven Development

Enforce Red-Green-Refactor discipline through isolated subagents. Each TDD phase spawns a fresh agent so the test writer can't see the implementation and the implementer can't cheat by reading test reasoning.

## Invocation

```
/tdd <feature-description>          # Full RGR cycle
/tdd red <feature-description>      # RED only — write a failing test
/tdd green <test-file-path>         # GREEN only — implement to pass
/tdd refactor <impl-file-path>      # REFACTOR only — clean up
```

Natural triggers: "tdd", "test first", "red green refactor", "write a failing test"

## Workflow

### Parse the Command

Extract the subcommand and argument:
- No subcommand → full RGR cycle with feature description
- `red` → RED phase only
- `green` → GREEN phase only (argument is path to failing test)
- `refactor` → REFACTOR phase only (argument is path to implementation)

### Detect Project Context

Before spawning agents, gather context to pass along:

1. **Test framework:** Check for pytest.ini, pyproject.toml, vitest.config.*, jest.config.*, package.json
2. **Test conventions:** Find existing test files, note naming patterns and directory structure
3. **Project root:** The working directory where the feature lives

Store this as `project_context` to pass to agents.

### Emit Start Event

```bash
python3 /home/ndninja/rasengan/cli.py emit tdd.cycle_started tdd --data '{"feature": "<description>", "mode": "<full|red|green|refactor>"}'
```

If Rasengan is unavailable, continue without events — TDD works standalone.

---

## Phase 1: RED — Write a Failing Test

Spawn the test-writer agent with **Agent tool** (subagent_type: `general-purpose`):

**Prompt template:**
```
You are a TDD test writer. Follow the instructions in /home/ndninja/.claude/agents/tdd-test-writer.md exactly.

PROJECT ROOT: <working directory>
TEST FRAMEWORK: <detected framework>
TEST CONVENTIONS: <detected patterns, e.g. "tests/test_*.py with pytest, conftest.py exists">
EXISTING TEST FILES: <list of relevant test files>

FEATURE TO TEST:
<feature description>

Write ONE failing test. Run it. Confirm it fails. Report the test file path and failure output.
```

**Phase gate:** The agent MUST confirm the test FAILS. If it reports PASS, something is wrong — investigate before proceeding.

After RED completes, emit:
```bash
python3 /home/ndninja/rasengan/cli.py emit tdd.red_complete tdd --data '{"test_file": "<path>", "status": "fail_confirmed"}'
```

**Show the user:** Test file path and failure output. Ask for confirmation to proceed to GREEN.

---

## Phase 2: GREEN — Minimal Implementation

Spawn the implementer agent with **Agent tool** (subagent_type: `general-purpose`):

**Prompt template:**
```
You are a TDD implementer. Follow the instructions in /home/ndninja/.claude/agents/tdd-implementer.md exactly.

PROJECT ROOT: <working directory>
TEST FILE: <path from RED phase>

Read the failing test. Write the MINIMUM code to make it pass. Run the test. Confirm it passes.
Do NOT read any feature descriptions — work from the test only.
Report the implementation file path(s) and pass output.
```

**Key isolation rule:** Do NOT pass the feature description to this agent. It works from the test spec only.

**Phase gate:** The agent MUST confirm the test PASSES. If it reports FAIL, let it debug. If still failing after reasonable attempts, stop and report to user.

After GREEN completes, emit:
```bash
python3 /home/ndninja/rasengan/cli.py emit tdd.green_complete tdd --data '{"test_file": "<path>", "impl_files": ["<paths>"], "status": "pass_confirmed"}'
```

**Show the user:** Implementation file path(s) and pass output. Ask for confirmation to proceed to REFACTOR.

---

## Phase 3: REFACTOR — Clean Up

Spawn the refactorer agent with **Agent tool** (subagent_type: `general-purpose`):

**Prompt template:**
```
You are a TDD refactorer. Follow the instructions in /home/ndninja/.claude/agents/tdd-refactorer.md exactly.

PROJECT ROOT: <working directory>
TEST FILE: <path from RED phase>
IMPLEMENTATION FILE(S): <path(s) from GREEN phase>

Evaluate the code against the refactoring checklist. If improvements are warranted, make them incrementally — run tests after EACH change. If the code is clean, report "no changes needed".
Report your evaluation, changes made, and final test output.
```

After REFACTOR completes, emit:
```bash
python3 /home/ndninja/rasengan/cli.py emit tdd.refactor_complete tdd --data '{"test_file": "<path>", "impl_files": ["<paths>"], "changes": "<summary or none>"}'
```

---

## Cycle Complete

After all three phases (or single phase if using subcommands), emit:
```bash
python3 /home/ndninja/rasengan/cli.py emit tdd.cycle_complete tdd --data '{"feature": "<description>", "test_file": "<path>", "impl_files": ["<paths>"], "phases_completed": ["red", "green", "refactor"]}'
```

**Present the summary:**
```
TDD Cycle Complete ✓

RED:      <test file> — FAIL confirmed
GREEN:    <impl file(s)> — PASS confirmed
REFACTOR: <changes made or "no changes needed">

Files created/modified:
  - <test file>
  - <impl file(s)>
```

**Then ask:** "Ready for the next cycle, or is this feature complete?"

---

## Core Rules

1. **One feature per cycle** — never batch multiple features into one TDD run
2. **Vertical slicing** — each cycle informs the next. Don't plan all tests upfront
3. **Phase gates are mandatory** — RED must fail, GREEN must pass, REFACTOR must stay green
4. **Subagent isolation** — each phase gets a FRESH agent via the Agent tool. No shared context
5. **Tests are specs** — the test writer defines behavior, the implementer reads it cold
6. **User confirms between phases** — show output and get go-ahead before advancing
7. **Rasengan events are fire-and-forget** — if the event bus is down, TDD still works

## Error Handling

- **Test has syntax error in RED:** Fix the test (syntax errors aren't valid RED)
- **Implementation can't pass in GREEN:** Let agent debug for 2-3 attempts, then stop and report
- **Refactor breaks tests:** Agent reverts the change automatically
- **Rasengan unavailable:** Skip events, continue with TDD
- **No test framework detected:** Ask the user which to use
