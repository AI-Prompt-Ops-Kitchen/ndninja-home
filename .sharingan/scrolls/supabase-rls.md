---
name: supabase-rls
domain: Backend/Security
level: 3-tomoe
description: Supabase Row Level Security — enabling, writing policies, and testing them for Next.js SaaS apps.
sources:
  - type: docs
    title: "Supabase RLS Documentation"
    url: "https://supabase.com/docs/guides/database/postgres/row-level-security"
    date: "2026-02-19"
    confidence: high
  - type: practice
    title: "Prompt Toolkit RLS migration (20260219000000)"
    url: "local:/home/ndninja/projects/prompt-toolkit/app/supabase/migrations/20260219000000_rls_policies.sql"
    date: "2026-02-19"
    confidence: high
  - type: practice
    title: "Verified via docker exec psql SET ROLE anon testing"
    url: "local:cli"
    date: "2026-02-19"
    confidence: high
last_updated: 2026-02-19
can_do_from_cli: true
---

# Supabase Row Level Security (RLS)

## Mental Model
RLS is PostgreSQL's built-in access control at the row level. Instead of filtering in app code, you write SQL `POLICY` statements that run on every query — the DB enforces them. Supabase's anon/authenticated roles go through PostgREST, which sets `SET LOCAL ROLE anon` or `SET LOCAL ROLE authenticated` per request, so your policies automatically apply to all API calls.

`auth.uid()` = the currently authenticated user's UUID from Supabase Auth JWT.

## Prerequisites
- Supabase project (local or hosted)
- Tables created in `public` schema
- Supabase CLI for migrations (`npx supabase migration up`)
- `SUPABASE_SERVICE_ROLE_KEY` env var for server-side admin bypasses

## Core Workflows

### Workflow 1: Enable RLS on a Table
```sql
ALTER TABLE my_table ENABLE ROW LEVEL SECURITY;
```
**After this, NO rows are accessible to anyone until you add policies.**
Gotcha: The `postgres` superuser and `service_role` always bypass RLS.

### Workflow 2: Public Read + Owner Write Pattern
The most common pattern for SaaS (public content library):
```sql
-- Anyone can read published records
CREATE POLICY "public read"
    ON my_table FOR SELECT
    USING (status = 'published' OR author_id = auth.uid());

-- Only authenticated users can insert their own records
CREATE POLICY "authenticated insert"
    ON my_table FOR INSERT
    WITH CHECK (author_id = auth.uid());

-- Only the author can update
CREATE POLICY "author update"
    ON my_table FOR UPDATE
    USING (author_id = auth.uid())
    WITH CHECK (author_id = auth.uid());
```
`USING` = filter rows for reads/updates/deletes. `WITH CHECK` = validate new/modified rows on INSERT/UPDATE.

### Workflow 3: Private User Data Pattern
For personal data that only the user should see:
```sql
ALTER TABLE user_data ENABLE ROW LEVEL SECURITY;

CREATE POLICY "owner only"
    ON user_data FOR ALL
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());
```
`FOR ALL` = covers SELECT, INSERT, UPDATE, DELETE in one policy.

### Workflow 4: Indirect / Helper Function Pattern
When visibility depends on a parent record (e.g., can see variables if prompt is visible):
```sql
CREATE OR REPLACE FUNCTION is_prompt_visible(p_prompt_id UUID)
RETURNS BOOLEAN LANGUAGE sql STABLE SECURITY DEFINER AS $$
    SELECT EXISTS (
        SELECT 1 FROM prompts
        WHERE id = p_prompt_id
          AND (status = 'published' OR author_id = auth.uid())
    );
$$;

CREATE POLICY "visible if parent visible"
    ON prompt_variables FOR SELECT
    USING (is_prompt_visible(prompt_id));
```
`SECURITY DEFINER` = the function runs as its owner (bypasses RLS inside it), but returns boolean — keeps the outer query constrained by the policy.

### Workflow 5: Testing RLS in CLI
```bash
# Simulate what anon users see
docker exec supabase_db_<project> psql -U postgres -c "
SET ROLE anon;
SELECT count(*) FROM my_table;
RESET ROLE;
"

# Check which policies exist
docker exec supabase_db_<project> psql -U postgres -c "
SELECT tablename, policyname, cmd FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename;"

# Check if RLS is enabled
docker exec supabase_db_<project> psql -U postgres -c "
SELECT tablename, rowsecurity FROM pg_tables
WHERE schemaname = 'public';"
```

### Workflow 6: Apply a Migration
```bash
# From the project's supabase/ directory
npx supabase migration up
# Or supabase db push for hosted
```

## Command Reference
| Action | Command | Notes |
|--------|---------|-------|
| Enable RLS | `ALTER TABLE t ENABLE ROW LEVEL SECURITY;` | Required before any policies matter |
| Create policy | `CREATE POLICY "name" ON t FOR SELECT USING (...)` | SELECT, INSERT, UPDATE, DELETE, or ALL |
| List policies | `SELECT * FROM pg_policies WHERE schemaname='public'` | |
| Test as anon | `SET ROLE anon; ... RESET ROLE;` in psql | Simulates PostgREST requests |
| Bypass RLS | Use `SUPABASE_SERVICE_ROLE_KEY` on server side | Never expose to client |

## Prompt Toolkit RLS Design (Validated Feb 2026)
From building the actual policy set for 10 tables, 46 policies:

| Table | SELECT | INSERT | UPDATE | DELETE |
|-------|--------|--------|--------|--------|
| prompts | published or author | author_id = uid | author | author |
| users | public | owner (uid match) | owner | owner |
| prompt_variables | if parent visible | author | author | author |
| prompt_ratings | public | no self-rating | rater | rater |
| user_customizations | owner only | owner | owner | owner |
| prompt_usage | owner only | owner | ❌ immutable | ❌ immutable |
| prompt_versions | if parent visible | author | ❌ immutable | ❌ immutable |
| collections | public or owner | owner | owner | owner |

**Key design choices:**
- Ratings: users can't rate their own prompts (`AND author_id != auth.uid()`)
- Version history: insert-only (no updates/deletes = append-only audit trail)
- Usage: insert-only (analytics integrity)
- Customizations: fully private (user's personal workspace)

## Views and RLS
**Critical gotcha:** PostgreSQL views are `SECURITY DEFINER` by default — they run as the view owner, bypassing RLS on underlying tables.

**Workaround options:**
1. Use `SECURITY INVOKER` (PostgreSQL 15+, Supabase supports it):
   ```sql
   CREATE VIEW my_view WITH (security_invoker = true) AS ...
   ```
2. PostgREST + Supabase anon role: In practice, PostgREST sets `SET LOCAL ROLE` per request, so queries to views via the Supabase client go through the role context correctly. **Verified: `SET ROLE anon; SELECT FROM prompts_with_author` correctly hides draft prompts.**
3. Use functions with `SECURITY DEFINER` that explicitly filter by `auth.uid()` if you need to bypass the view issue.

## Integration Points
- **Prompt Toolkit:** All 10 tables secured, 46 policies, tested via CLI
- **Next.js + Supabase SSR:** `@supabase/ssr` cookie-based client automatically sends auth token → PostgREST picks up `auth.uid()` from JWT
- **API routes:** Use `SUPABASE_SERVICE_ROLE_KEY` for admin ops (seed scripts, admin APIs) — bypasses RLS
- **Glitch backend:** If adding user data storage, follow same pattern

## Limitations & Gaps
- `auth.uid()` requires Supabase Auth. If using external auth, need a custom `auth.uid()` function or JWT claims
- RLS policies are checked on every query — can impact performance on large tables (use indexes!)
- Complex policies with subqueries can be slow; helper functions with `SECURITY DEFINER` + `STABLE` help
- Views are `SECURITY DEFINER` by default (see above) — test explicitly with `SET ROLE anon`

## Tips & Best Practices
1. **Enable RLS before adding policies.** Once enabled, zero rows are accessible — you build up from there.
2. **Test as anon explicitly.** Don't assume it works; run `SET ROLE anon; SELECT ...` in psql every time.
3. **Service role for admin operations.** Never expose `SUPABASE_SERVICE_ROLE_KEY` to the client. Use it only in server-side API routes.
4. **Immutable audit tables:** For version history and usage logs, create policies for SELECT + INSERT only (no UPDATE/DELETE). This is enforced at DB level.
5. **Self-reference gotcha for ratings:** Users should not rate their own content — add `AND author_id != auth.uid()` to the INSERT policy.
6. **DRY with helper functions:** When multiple tables need to check the same parent visibility, create a helper function (`is_prompt_visible()`) rather than duplicating the subquery in every policy.
