---
name: merge-strategies
description: Pattern for implementing multiple merge strategies for data conflict resolution
version: 1.0.0
category: architecture
args: ["[--context]", "[--data-type]"]
when_to_use: "User needs to handle data merging, conflict resolution, or synchronization. Use when building multi-worker systems, distributed data, git-like workflows, or any scenario with potentially conflicting updates."
tags: [architecture, merging, conflict-resolution, data-sync, patterns, distributed-systems]
examples:
  - /merge-strategies --context "git worktrees"
  - /merge-strategies --context "database sync"
  - /merge-strategies --data-type "JSON configuration"
reflection_count: 0
---

# Multiple Merge Strategies Pattern

**Purpose:** Guide implementation of flexible merge/conflict resolution systems. Prevents building single-strategy solutions that don't handle edge cases. Promotes user control over merge behavior.

## Core Principle

> **Don't build one merge strategy. Build a system that supports multiple strategies and lets users choose.**

Different scenarios need different merge approaches. A production-grade system should support:
1. **Automatic merging** when safe (no conflicts)
2. **Conservative strategies** when data integrity is critical
3. **Manual intervention** when context matters
4. **Custom strategies** for domain-specific logic

## The Three Essential Strategies

### Strategy 1: THEIRS (Conservative)

**Concept:** When in doubt, prefer the source data completely. Discard local changes.

**When to use:**
- Source is authoritative (official data, upstream repo)
- Local changes are experimental/throwaway
- Data integrity is critical (financial, medical)
- First-time sync (no local state to preserve)

**Implementation pattern:**
```python
async def merge_theirs(local_data, remote_data, context):
    """
    Conservative merge: Always prefer remote/source data.

    Returns:
        remote_data unchanged

    Discards:
        All local_data
    """
    return remote_data
```

**Example from Kage Bunshin:**
```python
# Git worktree merge - always accept AI changes
if merge_strategy == "THEIRS":
    result = await git.merge(
        worktree_branch,
        strategy_option="theirs"
    )
    # All conflicts resolved in favor of AI branch
```

**Real-world use cases:**
- Pulling upstream changes from main branch
- Syncing from official API to local cache
- Resetting sandbox environment to production state
- Accepting external contributor's work wholesale

### Strategy 2: AUTO (Smart Automatic)

**Concept:** Attempt automatic merge. Succeed if no conflicts, fail otherwise.

**When to use:**
- Most common case (changes don't overlap)
- Time-sensitive operations (can't wait for manual review)
- High confidence in non-conflicting changes
- Continuous integration / deployment pipelines

**Implementation pattern:**
```python
async def merge_auto(local_data, remote_data, context):
    """
    Automatic merge: Succeed if no conflicts, fail if conflicts detected.

    Returns:
        merged_data if successful

    Raises:
        MergeConflictError if conflicts detected
    """
    conflicts = detect_conflicts(local_data, remote_data)

    if conflicts:
        raise MergeConflictError(
            "Cannot auto-merge: conflicts detected",
            conflicts=conflicts
        )

    return smart_merge(local_data, remote_data)
```

**Example from Kage Bunshin:**
```python
if merge_strategy == "AUTO":
    try:
        result = await git.merge(worktree_branch)
        if result.conflicts:
            return {
                "status": "conflict",
                "conflicts": result.conflicts,
                "suggestion": "Use MANUAL strategy to resolve"
            }
    except GitMergeError as e:
        return {"status": "failed", "error": str(e)}
```

**Conflict detection examples:**

**File-based:**
```python
def detect_file_conflicts(local_files, remote_files):
    """Detect which files changed in both versions"""
    conflicts = []

    for path in local_files:
        if path in remote_files:
            if local_files[path] != remote_files[path]:
                conflicts.append({
                    "file": path,
                    "local": local_files[path],
                    "remote": remote_files[path]
                })

    return conflicts
```

**JSON-based:**
```python
def detect_json_conflicts(local_json, remote_json, path=""):
    """Recursively detect conflicting JSON keys"""
    conflicts = []

    all_keys = set(local_json.keys()) | set(remote_json.keys())

    for key in all_keys:
        current_path = f"{path}.{key}" if path else key

        local_val = local_json.get(key)
        remote_val = remote_json.get(key)

        if local_val != remote_val:
            if isinstance(local_val, dict) and isinstance(remote_val, dict):
                # Recurse into nested objects
                conflicts.extend(
                    detect_json_conflicts(local_val, remote_val, current_path)
                )
            else:
                conflicts.append({
                    "path": current_path,
                    "local": local_val,
                    "remote": remote_val
                })

    return conflicts
```

### Strategy 3: MANUAL (Full Control)

**Concept:** Present conflicts to user and let them resolve explicitly.

**When to use:**
- Conflicts detected that can't auto-merge
- Critical data where mistakes are expensive
- Complex business logic requiring human judgment
- Learning/training scenarios (user needs to understand changes)

**Implementation pattern:**
```python
async def merge_manual(local_data, remote_data, context):
    """
    Manual merge: Provide conflict resolution interface.

    Returns:
        Partial result with conflict markers

    Requires:
        User intervention to complete
    """
    conflicts = detect_conflicts(local_data, remote_data)

    return {
        "status": "needs_resolution",
        "conflicts": conflicts,
        "local_preview": local_data,
        "remote_preview": remote_data,
        "resolution_options": [
            "accept_local",
            "accept_remote",
            "merge_custom"
        ]
    }
```

**Example conflict presentation:**
```markdown
## Merge Conflict in config.json

### Path: database.host

**Local version (OURS):**
```json
"database": {
  "host": "localhost",
  "port": 5432
}
```

**Remote version (THEIRS):**
```json
"database": {
  "host": "production-db.example.com",
  "port": 5432
}
```

**Resolution options:**
1. Keep local (localhost)
2. Accept remote (production-db.example.com)
3. Use custom value: ___________

Choose [1/2/3]:
```

**Git-style conflict markers:**
```python
def create_conflict_markers(local_data, remote_data, path):
    """Create git-style conflict markers for manual resolution"""
    return f"""
<<<<<<< LOCAL (current changes)
{format_data(local_data)}
=======
{format_data(remote_data)}
>>>>>>> REMOTE (incoming changes)
    """.strip()
```

## Advanced Strategy: OURS

**Concept:** Opposite of THEIRS - always prefer local data.

**When to use:**
- Local version is authoritative
- Merging feature branch into main (keep main's critical files)
- Preserving local configuration overrides
- Rolling back bad changes from remote

**Implementation:**
```python
async def merge_ours(local_data, remote_data, context):
    """Keep local data, discard remote changes"""
    return local_data
```

## Strategy Selection Interface

**User-friendly API:**
```python
class MergeEngine:
    STRATEGIES = {
        "THEIRS": merge_theirs,
        "AUTO": merge_auto,
        "MANUAL": merge_manual,
        "OURS": merge_ours
    }

    async def merge(
        self,
        local_data,
        remote_data,
        strategy: str = "AUTO",
        context: dict = None
    ):
        """
        Merge data using specified strategy.

        Args:
            local_data: Current local state
            remote_data: Incoming remote state
            strategy: One of THEIRS, AUTO, MANUAL, OURS
            context: Additional context for merge decisions

        Returns:
            Merged data or conflict information
        """
        if strategy not in self.STRATEGIES:
            raise ValueError(f"Unknown strategy: {strategy}")

        merge_fn = self.STRATEGIES[strategy]
        return await merge_fn(local_data, remote_data, context)
```

## Real-World Examples

### Example 1: Kage Bunshin Git Worktrees

**Context:** Multiple AI agents working in parallel git worktrees need to merge back to base branch.

**Three strategies implemented:**

1. **THEIRS** - Accept AI changes completely
   ```bash
   # Use case: AI generated new feature from scratch
   git merge feature/ai-implementation --strategy-option theirs
   ```

2. **AUTO** - Merge if no conflicts
   ```bash
   # Use case: AI changed different files than human
   git merge feature/ai-refactor
   # Fails if conflicts detected
   ```

3. **MANUAL** - Show conflicts for human resolution
   ```bash
   # Use case: AI and human both modified same functions
   git merge feature/ai-optimization
   # Creates conflict markers in files
   ```

**Why three strategies matter:**
- Different tasks have different risk profiles
- Some AI outputs can be trusted more than others
- Humans need final say on critical changes

### Example 2: Configuration Sync

**Context:** Syncing application config between environments (dev/staging/prod).

**Strategy selection:**

```python
async def sync_config(source_env, target_env, strategy="AUTO"):
    """
    Sync configuration between environments.

    Examples:
        # Safe: dev → staging (accept all changes)
        sync_config("dev", "staging", strategy="THEIRS")

        # Careful: staging → prod (only if no conflicts)
        sync_config("staging", "prod", strategy="AUTO")

        # Critical: prod → staging (manual review)
        sync_config("prod", "staging", strategy="MANUAL")
    """
    local_config = load_config(target_env)
    remote_config = load_config(source_env)

    result = await merge_engine.merge(
        local_config,
        remote_config,
        strategy=strategy,
        context={"source": source_env, "target": target_env}
    )

    if result.get("status") == "needs_resolution":
        # Present conflicts to user
        show_conflicts(result["conflicts"])
    else:
        # Apply merged config
        save_config(target_env, result)
```

### Example 3: Database Record Merging

**Context:** Distributed database with eventual consistency.

**Conflict-free merge strategies:**

```python
class RecordMerger:
    """Merge database records from different sources"""

    async def merge_records(
        self,
        local_record: dict,
        remote_record: dict,
        strategy: str = "LAST_WRITE_WINS"
    ):
        """
        Strategies for database records:
        - LAST_WRITE_WINS: Use most recent timestamp (THEIRS variant)
        - MERGE_FIELDS: Combine non-conflicting fields (AUTO variant)
        - VERSIONED: Keep both versions (MANUAL variant)
        """

        if strategy == "LAST_WRITE_WINS":
            if remote_record["updated_at"] > local_record["updated_at"]:
                return remote_record  # THEIRS
            return local_record  # OURS

        elif strategy == "MERGE_FIELDS":
            merged = local_record.copy()

            for key, remote_val in remote_record.items():
                local_val = local_record.get(key)

                if local_val == remote_val:
                    continue  # No conflict
                elif key == "updated_at":
                    merged[key] = max(local_val, remote_val)
                elif local_val is None:
                    merged[key] = remote_val  # New field
                elif remote_val is None:
                    continue  # Keep local
                else:
                    # Conflict detected
                    raise MergeConflictError(
                        f"Conflict on field {key}",
                        local=local_val,
                        remote=remote_val
                    )

            return merged

        elif strategy == "VERSIONED":
            return {
                "local_version": local_record,
                "remote_version": remote_record,
                "status": "needs_resolution"
            }
```

## Strategy Selection Guide

| Scenario | Recommended Strategy | Rationale |
|----------|---------------------|-----------|
| First-time setup | THEIRS | No local state to preserve |
| Routine updates | AUTO | Most changes are non-conflicting |
| Production deployment | MANUAL | Human review required |
| Rollback operation | OURS | Keep current state |
| Experimental branch | THEIRS | Upstream is authoritative |
| Configuration override | OURS | Local config intentionally different |
| CI/CD pipeline | AUTO | Fail fast on conflicts |
| Data migration | MANUAL | Review every change |

## Implementation Checklist

When building a merge system:

- [ ] Support at least 3 strategies (THEIRS, AUTO, MANUAL)
- [ ] Make strategy selection explicit (not hidden default)
- [ ] Detect conflicts before attempting merge
- [ ] Provide clear error messages for conflicts
- [ ] Allow fallback (AUTO → MANUAL if conflicts)
- [ ] Log merge decisions for audit trail
- [ ] Test all strategies with real data
- [ ] Document when to use each strategy

## Anti-Patterns to Avoid

### ❌ Anti-Pattern 1: Single Strategy Only

```python
# BAD: Only one way to merge
def merge(local, remote):
    """Always overwrites local with remote"""
    return remote
    # What if user wants to keep local changes?
    # What if changes conflict?
```

**Fix:** Support multiple strategies
```python
def merge(local, remote, strategy="AUTO"):
    strategies = {
        "THEIRS": lambda: remote,
        "OURS": lambda: local,
        "AUTO": lambda: smart_merge(local, remote)
    }
    return strategies[strategy]()
```

### ❌ Anti-Pattern 2: Silent Conflict Resolution

```python
# BAD: Silently picks one version
def merge(local, remote):
    if local != remote:
        return remote  # User doesn't know local was discarded!
```

**Fix:** Explicit conflict handling
```python
def merge(local, remote, strategy="AUTO"):
    if local != remote and strategy == "AUTO":
        raise MergeConflictError(
            "Conflict detected. Use THEIRS/OURS/MANUAL strategy."
        )
    # ... handle based on strategy
```

### ❌ Anti-Pattern 3: No Fallback Option

```python
# BAD: AUTO fails with no alternative
async def merge_auto(local, remote):
    if has_conflicts(local, remote):
        raise Exception("Cannot merge!")  # Now what?
```

**Fix:** Suggest fallback strategy
```python
async def merge_auto(local, remote):
    if has_conflicts(local, remote):
        raise MergeConflictError(
            "Cannot auto-merge due to conflicts. "
            "Use MANUAL strategy to resolve.",
            fallback_strategy="MANUAL",
            conflicts=get_conflicts(local, remote)
        )
```

## AuDHD-Friendly Features

**Reduces Decision Anxiety:**
- Clear strategy names (THEIRS/OURS/AUTO/MANUAL)
- Explicit choice points (not implicit heuristics)
- Predictable outcomes for each strategy

**Executive Function Support:**
- Pre-defined strategies (don't need to design merge logic)
- Checklist for implementation
- Decision table shows which strategy for which scenario

**Hyperfocus Accommodation:**
- Can deep-dive into conflict resolution
- Structured approach prevents getting lost in edge cases
- MANUAL strategy allows perfectionism when needed

## Testing Strategies

**Test matrix:**
```python
test_cases = [
    # (local, remote, strategy, expected_result)
    ("A", "B", "THEIRS", "B"),
    ("A", "B", "OURS", "A"),
    ("A", "A", "AUTO", "A"),
    ("A", "B", "AUTO", MergeConflictError),
    ("A", "B", "MANUAL", {"status": "needs_resolution"}),
]

for local, remote, strategy, expected in test_cases:
    result = merge(local, remote, strategy)
    assert result == expected
```

## Integration with Other Skills

**Works well with:**
- `/realtime-transport` - Sync strategies for distributed systems
- `/db-health-check` - Monitor merge performance
- `/debug-zombies` - Debug hanging merge operations

## Success Criteria

A good merge strategy system should:
1. ✅ Support multiple strategies (minimum 3)
2. ✅ Make strategy selection explicit
3. ✅ Detect conflicts before merging
4. ✅ Provide clear error messages
5. ✅ Allow fallback strategies
6. ✅ Log all merge decisions

## Version History

- v1.0.0 (2026-01-05): Initial release from Kage Bunshin reflection
  - Captured multi-strategy pattern from Week 3 implementation
  - Three core strategies: THEIRS, AUTO, MANUAL
  - Real-world examples from git worktree merging

---

## 🧠 Learnings (Auto-Updated)

### 2026-01-05 - Pattern
**Signal:** "Implemented 3 merge strategies for different use cases"
**What Changed:** Pattern of implementing multiple merge strategies rather than single approach
**Confidence:** Medium
**Source:** kage-bunshin-week3-implementation-2026-01-04
**Rationale:** This shows a preference for flexible, multi-strategy approaches to data merging that could apply to various data synchronization scenarios beyond just git workflows
