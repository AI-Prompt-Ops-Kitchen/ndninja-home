# CLI Agent Benchmark Arena - Milestone 2: Claude + Comparison Design

**Date:** 2026-02-09
**Status:** Approved for Implementation
**Prerequisites:** Milestone 1 Complete (Kimi adapter, quality analysis, HTML reports)

## Goal

Implement Claude Code adapter with output parser and multi-agent comparison reporting to enable head-to-head benchmarking between Kimi and Claude Code.

## Architecture

### 1. Claude Adapter Implementation

**Core Structure:**

The `ClaudeCodeAdapter` mirrors the `KimiAdapter` pattern:
- Spawn `claude` CLI as subprocess in task directory
- Wrap execution with asciinema for session recording
- Feed prompt via stdin or temp file
- Capture stdout/stderr for metrics extraction
- Use timeout for wall-time tracking

**Key Implementation Details:**

1. **Command Construction**: `claude --api-key <key> --model sonnet` (configurable model)
2. **Prompt Delivery**: Write prompt to `TASK.md` in task directory, then start Claude CLI
3. **Execution Tracking**:
   - Start timer before subprocess launch
   - Wrap in `asciinema rec -c "claude" recording.cast`
   - Monitor for completion or timeout
   - Calculate wall_time from start/end

4. **Output Capture**: Collect full stdout/stderr for parser

5. **Quality Analysis**: After execution, scan generated files with QualityAnalyzer (same as Kimi)

**Parser Integration**: Create `ClaudeParser` class extending `BaseOutputParser`

### 2. ClaudeParser Implementation

**Parsing Strategy:**

Use regex patterns to extract metrics from Claude Code's terminal output.

**Token Extraction:**
```python
# Look for patterns like:
# "Input tokens: 1,234"
# "Output tokens: 567"
# "Total: 1,801 tokens"
input_pattern = r'Input tokens?:\s*([0-9,]+)'
output_pattern = r'Output tokens?:\s*([0-9,]+)'
```

**Cost Calculation:**
```python
# Use Anthropic pricing (as of Feb 2026):
# Sonnet: $3/MTok input, $15/MTok output
cost = (input_tokens * 0.003 / 1000) + (output_tokens * 0.015 / 1000)
```

**Tool Calls:**
```python
# Count tool usage lines like:
# "Using tool: Read"
# "Using tool: Bash"
tool_pattern = r'Using tool:|Tool use:|<tool_use>'
tool_calls = len(re.findall(tool_pattern, output))
```

**Retries & Error Recovery:**
```python
# Detect retry patterns:
# "Retrying..." or "Attempting again"
retry_pattern = r'Retry|Attempting again|Re-attempting'
retries = len(re.findall(retry_pattern, output, re.IGNORECASE))

# Error recovery: errors present but final success
errors = bool(re.search(r'Error:|Failed:', output))
error_recovered = errors and exit_code == 0
```

**Fallback Handling:** If patterns don't match, return safe defaults (0 tokens, $0 cost, 0 retries) rather than failing.

### 3. Multi-Agent Comparison Reports

**Comparison Dashboard Enhancement:**

Extend the existing `HTMLGenerator` to support side-by-side agent comparison when multiple agents run the same task.

**Comparison Table Structure:**
```
| Metric          | Kimi      | Claude    | Winner |
|-----------------|-----------|-----------|--------|
| Speed           | 45.2s     | 38.7s ✓   | Claude |
| Correctness     | 100%      | 100%      | Tie    |
| Cost            | $0.038    | $0.042    | Kimi   |
| Tool Calls      | 12        | 8 ✓       | Claude |
| Code Quality    | 87.5      | 92.3 ✓    | Claude |
| Total Score     | 89.2      | 94.1 ✓    | Claude |
```

**Visual Enhancements:**
- Color-coded cells (green for winner, gray for tie)
- Score bars for visual comparison
- Aggregate statistics across all tasks
- Head-to-head win/loss/tie counts

**Database Query:**
```python
# Get results for same task from different agents
SELECT agent_name, total_score, wall_time_seconds, cost_usd, ...
FROM cli_agent_benchmark_results
WHERE task_name = ?
ORDER BY timestamp DESC
LIMIT 1 PER agent_name
```

**Report Sections:**
1. **Executive Summary**: Overall winner, key metrics
2. **Task-by-Task Comparison**: Detailed breakdown per benchmark
3. **Strengths & Weaknesses**: What each agent excels at
4. **Cost Analysis**: Total spend, efficiency metrics

**New Method:** `HTMLGenerator.generate_comparison(results_dict, task_name)` where `results_dict = {'kimi': result1, 'claude': result2}`

## Testing Strategy

**Test Coverage for Milestone 2:**

Following the TDD pattern from Milestone 1, we'll add approximately 20-25 new tests:

**ClaudeParser Tests (8-10 tests):**
- `test_extract_tokens_from_output` - Parse token counts from various formats
- `test_calculate_cost_correctly` - Verify pricing calculations
- `test_count_tool_calls` - Count tool usage patterns
- `test_detect_retries` - Identify retry attempts
- `test_detect_error_recovery` - Success after errors
- `test_fallback_on_missing_data` - Handle unparseable output
- `test_parse_real_claude_output` - Integration test with actual Claude output samples

**ClaudeAdapter Tests (5-7 tests):**
- `test_adapter_initialization` - Basic setup
- `test_check_available` - CLI detection
- `test_execute_task_success` - Happy path (mocked subprocess)
- `test_execute_task_timeout` - Timeout handling
- `test_quality_analysis_integration` - End-to-end with quality analyzer

**Comparison Report Tests (5-7 tests):**
- `test_generate_comparison_table` - Two-agent comparison
- `test_winner_detection` - Correct winner per metric
- `test_aggregate_statistics` - Multi-task summaries
- `test_html_rendering` - Valid HTML output
- `test_empty_comparison` - Handle missing data

**Integration Test:**
- `test_integration_milestone2` - Full pipeline: Claude execution → parsing → scoring → comparison report

**Test Execution:** All tests should pass before considering Milestone 2 complete. Target: 105+ tests passing total.

## Implementation Tasks

1. **ClaudeParser** (adapters/parsers/claude_parser.py + tests)
2. **ClaudeAdapter** (adapters/claude.py - replace stub + tests)
3. **Comparison Reports** (reporting/html_generator.py enhancements + tests)
4. **Integration Test** (test_integration_milestone2.py)
5. **Documentation** (README.md update)

## Success Criteria

- [ ] ClaudeAdapter spawns separate Claude process successfully
- [ ] ClaudeParser extracts metrics from terminal output accurately
- [ ] Comparison reports show side-by-side metrics for Kimi vs Claude
- [ ] 105+ tests passing (85 existing + 20 new)
- [ ] End-to-end benchmark run: `--agent kimi,claude --tasks algorithms/quicksort`
- [ ] HTML report shows comparison dashboard

## Technical Decisions

**Decision: Spawn separate Claude process**
Rationale: Only way to get true benchmark data comparable to Kimi. Self-benchmarking would compromise integrity.

**Decision: Parse terminal output vs structured logs**
Rationale: Consistent with Kimi approach, no modifications needed to Claude CLI, easier to maintain.

**Decision: Extend HTMLGenerator vs new reporter**
Rationale: Reuse existing infrastructure, maintain consistent report styling.

## Next Steps

After design approval:
1. Create feature branch in git worktree
2. Write detailed implementation plan (PLAN.md)
3. Execute TDD implementation
4. Verify all tests pass
5. Merge to master
