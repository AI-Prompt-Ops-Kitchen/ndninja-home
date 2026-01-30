# Doltgres Evaluation Report

**Date:** 2026-01-30  
**Evaluated by:** Clawd + Shadow Council (GPT-5.2, Claude Sonnet 4.5, Gemini 3 Pro, Perplexity Sonar)  
**Cost:** $0.16 (council synthesis)

---

## Executive Summary

| Use Case | Verdict | Reason |
|----------|---------|--------|
| **Kage Bunshin** (Secrets Manager) | ❌ **NOT RECOMMENDED** | pgcrypto incompatible (verified), security liability |
| **Sage Mode** (Dev Team Simulator) | ✅ **RECOMMENDED** | Natural fit for branching workflows, pursue PoC |

---

## What is Doltgres?

Doltgres is a PostgreSQL-compatible database with Git-like version control. It's built by DoltHub, the creators of Dolt (MySQL-compatible version).

**Key Features:**
- Branch, merge, fork, clone, push, pull databases like Git repos
- Version control via SQL: `dolt_commit()`, `dolt_checkout()`, `dolt.log`
- Connect with standard `psql` or any Postgres client
- Exports to standard PostgreSQL dumps (no vendor lock-in)

**Current Status:** Pre-alpha/Beta (as of Jan 2026)

---

## Use Case 1: Kage Bunshin (Secrets Manager)

### Current Architecture
```
PostgreSQL + pgcrypto
├── pgp_sym_encrypt() for storing secrets
├── pgp_sym_decrypt() for retrieving secrets
└── Full PostgreSQL extension support
```

### Doltgres Compatibility Test

**Test performed:** 2026-01-30

```bash
# Spin up Doltgres container
docker run -d --name doltgres-test -p 5433:5432 dolthub/doltgresql:latest

# Test extension creation
psql -p 5433 -c "CREATE EXTENSION pgcrypto;"
# ERROR: exec: "pg_config": executable file not found in $PATH

# Test function directly  
psql -p 5433 -c "SELECT pgp_sym_encrypt('test', 'key');"
# ERROR: function: 'pgp_sym_encrypt' not found
```

**Result: HARD BLOCKER** ❌

Doltgres cannot run PostgreSQL extensions because it's a Go-based emulator of the PostgreSQL wire protocol, not the actual PostgreSQL engine.

### Additional Security Concerns

Even if pgcrypto worked, version control creates security liabilities:

```sql
-- Nightmare scenario: Rotated secrets remain accessible
SELECT * FROM secrets AS OF '2025-01-01';  -- Old compromised keys still queryable
```

- GDPR/SOC2 require demonstrable deletion; version control retains history
- Increases blast radius of key compromise
- Audit complexity increases significantly

### Performance Impact

| Operation | PostgreSQL | Doltgres | Multiplier |
|-----------|------------|----------|------------|
| oltp_read_write | 4.25ms | 20.37ms | 4.8x |
| oltp_write_only | 1.73ms | 7.43ms | 4.3x |
| Point select | 0.14ms | 0.52ms | 3.7x |

For secrets retrieval (typically <10ms p99 SLA), this breaks performance requirements.

### Recommendation

**Keep PostgreSQL + pgcrypto.** If you need audit trails:
- Add `pgAudit` extension for change tracking
- Use Point-in-Time Recovery (PITR) for rollback
- Consider HashiCorp Vault for rotation workflows

---

## Use Case 2: Sage Mode (Dev Team Simulator)

### Why This is a Strong Fit

Simulation workflows naturally map to Git operations:

```sql
-- Create scenario branch
CALL DOLT_CHECKOUT('-b', 'team-a-high-velocity');
UPDATE team_config SET velocity_multiplier = 1.5 WHERE team_id = 'team-a';
CALL DOLT_COMMIT('-am', 'High velocity scenario');

-- Create alternative branch
CALL DOLT_CHECKOUT('-b', 'team-a-add-contractor');
INSERT INTO team_members (name, role) VALUES ('Contractor', 'senior-dev');
CALL DOLT_COMMIT('-am', 'Added contractor');

-- Compare outcomes
SELECT * FROM dolt_diff('team-a-high-velocity', 'team-a-add-contractor', 'sprint_outcomes');

-- Time travel: reproduce exact state from 3 months ago
CALL DOLT_CHECKOUT('a3f5b8c');
```

### Performance Tradeoffs

**Acceptable if:**
- Most time spent in simulation compute, DB is state checkpointing
- Simulations are batch processes, not real-time
- Writes can be batched (1 commit per run vs. per operation)

**Mitigation strategy:**
```python
# Bad: 365 commits
for day in range(365):
    db.execute("INSERT INTO daily_states ...")
    db.execute("CALL DOLT_COMMIT(...)")

# Good: 1 commit
with transaction():
    for day in range(365):
        db.execute("INSERT INTO daily_states ...")
    db.execute("CALL DOLT_COMMIT('-am', 'Year simulation')")
```

### Data Integrity Benefits

- **Cryptographic verification**: If commit hash matches, data is guaranteed identical
- **Full audit trail**: `SELECT * FROM dolt_log;`
- **Reproducibility**: Debug "Why did run #4 diverge?" by checking out exact state
- **Branching is cheap**: O(1) regardless of database size

### Recommended PoC Approach

**Phase 1: Proof of Concept (2-4 weeks)**

Test with actual Sage Mode schema:

```sql
-- Test branching performance (should be <100ms)
\timing on
CALL DOLT_CHECKOUT('-b', 'test-branch');

-- Test merge conflicts
CALL DOLT_CHECKOUT('main');
UPDATE teams SET capacity = 10 WHERE id = 1;
CALL DOLT_COMMIT('-am', 'Main: capacity 10');

CALL DOLT_CHECKOUT('test-branch');
UPDATE teams SET capacity = 15 WHERE id = 1;
CALL DOLT_COMMIT('-am', 'Branch: capacity 15');

CALL DOLT_MERGE('main');
SELECT * FROM dolt_conflicts;
```

**Go/No-Go Criteria:**
1. Branch/merge UX acceptable for users
2. Constraints (FK, unique) behave correctly after merges
3. End-to-end runtime impact ≤30%
4. Required SQL queries/indexes work as expected

**Phase 2: Parallel Validation (Month 2)**
- Run Doltgres alongside current system
- Validate merge conflict frequency <5%
- Confirm p95 latency within tolerance

### Schema Design Guidelines

```sql
-- ✅ GOOD: Simulation-friendly
CREATE TABLE simulation_runs (
    run_id UUID PRIMARY KEY,
    branch_name TEXT,
    started_at TIMESTAMP
);

CREATE TABLE team_states (
    run_id UUID,
    day INT,
    team_id TEXT,
    velocity DECIMAL,
    PRIMARY KEY (run_id, day, team_id)
);

-- ⚠️ AVOID: Heavy FK constraints across mutable entities
CREATE TABLE tasks (
    task_id UUID,
    assigned_to INT REFERENCES developers(id)  -- Merge complexity
);
```

### Alternative: Native Dolt (MySQL)

If Sage Mode doesn't require PostgreSQL-specific features, consider native Dolt (MySQL-compatible):
- Near 100% mature
- Same versioning architecture
- Better tested in production

---

## Decision Matrix

| Criteria | Kage Bunshin | Sage Mode |
|----------|--------------|-----------|
| Extension support needed | ❌ BLOCKER (pgcrypto) | ✅ None needed |
| Performance critical | ❌ Yes (<10ms) | ✅ Acceptable (batch) |
| Version control value | ❌ Security liability | ✅ Core workflow |
| Maturity risk tolerance | ❌ Zero (secrets) | ✅ Acceptable |
| Data integrity needs | ❌ Immutable required | ✅ Cryptographic VC helps |

---

## Shadow Council Consensus

**Unanimous agreement from all 4 models:**

1. **Kage Bunshin: Strong rejection**
   - pgcrypto incompatibility is a hard blocker
   - Version control creates security liabilities
   - Performance penalty unjustified

2. **Sage Mode: Conditional recommendation**
   - Natural fit for branching/merging workflows
   - Requires structured PoC with clear go/no-go criteria
   - Data integrity benefits valuable

---

## Next Steps

### Kage Bunshin
- [ ] No action needed — keep PostgreSQL + pgcrypto
- [ ] Consider HashiCorp Vault if rotation workflows become complex

### Sage Mode
- [ ] Spin up Doltgres dev instance
- [ ] Import subset of Sage Mode schema
- [ ] Run 2-week PoC with criteria above
- [ ] Decision point: commit or fall back to event sourcing

---

## References

- [Doltgres GitHub](https://github.com/dolthub/doltgresql)
- [Doltgres Docs](https://docs.doltgres.com)
- [Performance Benchmarks](https://docs.dolthub.com/sql-reference/benchmarks/latency)
- [Shadow Council Query #174](postgresql://workspace/council_queries?id=174)
