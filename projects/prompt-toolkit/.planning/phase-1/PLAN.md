# Phase 1: Database Schema & Data Foundation

**Timeline:** Week 1-2 (10-14 days)
**Goal:** Design and implement core data model that supports versioning, attribution, and future marketplace

---

## Success Criteria

- [ ] All database tables created with proper relationships
- [ ] Row-Level Security (RLS) policies pass security audit
- [ ] 50 high-quality seed prompts across 5 categories
- [ ] Full-text search returns results in <100ms
- [ ] Automated RLS tests prevent data leakage
- [ ] Database migrations are reversible and tested

---

## Tasks

### Task 1: Database Schema Design (Day 1-2)

**Deliverable:** Complete schema.sql with ERD diagram

#### Subtasks

1. **Design core entities:**
   - [ ] `users` table (id, email, name, avatar_url, created_at, updated_at)
   - [ ] `prompts` table (id, title, description, template, category, skill_level, ai_model, author_id, version, parent_id, status, created_at, updated_at)
   - [ ] `prompt_variables` table (id, prompt_id, name, label, helper_text, default_value, suggestions, required, order)
   - [ ] `prompt_dna` table (id, prompt_id, component_type, highlight_start, highlight_end, explanation, order)
   - [ ] `collections` table (id, user_id, name, description, is_public, created_at, updated_at)
   - [ ] `collection_prompts` table (id, collection_id, prompt_id, order, added_at)
   - [ ] `prompt_versions` table (id, prompt_id, version_number, template, variables_schema, change_summary, created_by, created_at)
   - [ ] `prompt_ratings` table (id, prompt_id, user_id, rating, notes, created_at)
   - [ ] `user_customizations` table (id, user_id, prompt_id, customized_template, variables_json, created_at)
   - [ ] `prompt_usage` table (id, user_id, prompt_id, used_at)

2. **Define indexes:**
   - [ ] Primary keys on all tables
   - [ ] Foreign keys with ON DELETE CASCADE where appropriate
   - [ ] Index on `prompts.category` for filtering
   - [ ] Index on `prompts.skill_level` for filtering
   - [ ] Index on `prompts.author_id` for creator queries
   - [ ] Index on `collections.user_id` for user collections
   - [ ] Index on `prompt_usage.user_id, used_at` for history
   - [ ] Composite index on `collection_prompts (collection_id, order)`

3. **Full-text search setup:**
   - [ ] Add `search_vector` tsvector column to `prompts` table
   - [ ] Create GIN index on `search_vector`
   - [ ] Create trigger to auto-update `search_vector` on INSERT/UPDATE
   - [ ] Test search performance with sample data

4. **Create ERD diagram:**
   - [ ] Document relationships (1:many, many:many)
   - [ ] Export as PNG/SVG for documentation
   - [ ] Save to `.planning/phase-1/erd.png`

**Verification:**
```sql
-- All tables exist
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- All indexes created
SELECT indexname, tablename FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- GIN index exists for search
SELECT indexname FROM pg_indexes
WHERE indexname = 'prompts_search_vector_idx';
```

**Acceptance Criteria:**
- Schema supports versioning (parent_id, version)
- Schema supports attribution (author_id, created_by)
- Schema supports marketplace (ratings, public collections)
- All foreign keys have proper constraints
- Full-text search infrastructure ready

---

### Task 2: Supabase Migration (Day 2-3)

**Deliverable:** Supabase migration file that creates all tables

#### Subtasks

1. **Create initial migration:**
   - [ ] Run: `npx supabase migration new initial_schema`
   - [ ] Copy schema.sql content to migration file
   - [ ] Add migration metadata (author, description)
   - [ ] Test migration locally

2. **Add seed data migration:**
   - [ ] Create separate migration for seed data
   - [ ] Include 50 starter prompts
   - [ ] Include 5 default categories
   - [ ] Include DNA annotations for featured prompts

3. **Test migration rollback:**
   - [ ] Create down migration (DROP tables)
   - [ ] Test: apply migration → rollback → re-apply
   - [ ] Verify data integrity after rollback

**Commands:**
```bash
# Create migration
cd app
npx supabase migration new initial_schema

# Test locally
npx supabase db reset

# Apply to remote (production)
npx supabase db push
```

**Verification:**
```bash
# Check migration status
npx supabase migration list

# Verify tables exist
npx supabase db diff
```

**Acceptance Criteria:**
- Migration applies cleanly on fresh database
- Migration is reversible (down migration works)
- No SQL errors in migration logs
- Seed data loads successfully

---

### Task 3: Row-Level Security (RLS) Policies (Day 3-4)

**Deliverable:** RLS policies for all user-owned tables

#### Subtasks

1. **Enable RLS on tables:**
   - [ ] `ALTER TABLE collections ENABLE ROW LEVEL SECURITY;`
   - [ ] `ALTER TABLE user_customizations ENABLE ROW LEVEL SECURITY;`
   - [ ] `ALTER TABLE prompt_usage ENABLE ROW LEVEL SECURITY;`
   - [ ] `ALTER TABLE prompt_ratings ENABLE ROW LEVEL SECURITY;`

2. **Create policies for `collections`:**
   - [ ] **SELECT policy:** Users can read their own collections + public collections
   - [ ] **INSERT policy:** Users can create collections (user_id = auth.uid())
   - [ ] **UPDATE policy:** Users can update their own collections
   - [ ] **DELETE policy:** Users can delete their own collections

3. **Create policies for `user_customizations`:**
   - [ ] **SELECT policy:** Users can read only their own customizations
   - [ ] **INSERT policy:** Users can create customizations (user_id = auth.uid())
   - [ ] **UPDATE policy:** Users can update their own customizations
   - [ ] **DELETE policy:** Users can delete their own customizations

4. **Create policies for `prompt_usage`:**
   - [ ] **SELECT policy:** Users can read only their own usage history
   - [ ] **INSERT policy:** Users can log their own usage
   - [ ] **No UPDATE/DELETE:** Usage logs are append-only

5. **Create policies for `prompt_ratings`:**
   - [ ] **SELECT policy:** All users can read all ratings (public)
   - [ ] **INSERT policy:** Authenticated users can rate prompts
   - [ ] **UPDATE policy:** Users can update their own ratings
   - [ ] **DELETE policy:** Users can delete their own ratings

6. **Public read policies:**
   - [ ] `prompts`: All users can SELECT published prompts
   - [ ] `prompt_variables`: All users can SELECT variables
   - [ ] `prompt_dna`: All users can SELECT DNA annotations

**Policy Template:**
```sql
-- Example: Collections SELECT policy
CREATE POLICY "Users can view own and public collections"
ON collections FOR SELECT
USING (
  user_id = auth.uid()
  OR is_public = true
);

-- Example: User customizations INSERT policy
CREATE POLICY "Users can create own customizations"
ON user_customizations FOR INSERT
WITH CHECK (user_id = auth.uid());
```

**Verification:**
```sql
-- Test as different users
SET LOCAL ROLE authenticated;
SET LOCAL "request.jwt.claims" TO '{"sub": "user-1-uuid"}';

-- Should return only user-1's collections
SELECT * FROM collections;

-- Should fail: trying to insert with different user_id
INSERT INTO collections (user_id, name)
VALUES ('user-2-uuid', 'Test');
```

**Acceptance Criteria:**
- Users cannot read other users' private data
- Users cannot modify other users' data
- Public data is accessible to all
- Authenticated users can create their own records
- Anonymous users can read public prompts

---

### Task 4: Automated RLS Tests (Day 4-5)

**Deliverable:** Test suite that verifies RLS policies

#### Subtasks

1. **Create test framework:**
   - [ ] Install testing dependencies: `npm install --save-dev vitest @supabase/supabase-js`
   - [ ] Create test file: `app/tests/rls.test.ts`
   - [ ] Set up test database connection
   - [ ] Create helper functions for user impersonation

2. **Write RLS tests:**

   **Collections Tests:**
   - [ ] Test: User A cannot read User B's private collections
   - [ ] Test: User A can read User B's public collections
   - [ ] Test: User A cannot update User B's collections
   - [ ] Test: User A cannot delete User B's collections

   **User Customizations Tests:**
   - [ ] Test: User A cannot read User B's customizations
   - [ ] Test: User A cannot insert customizations with User B's ID

   **Prompt Usage Tests:**
   - [ ] Test: User A cannot read User B's usage history
   - [ ] Test: Users cannot update usage logs (append-only)

   **Prompt Ratings Tests:**
   - [ ] Test: All users can read all ratings
   - [ ] Test: User A cannot update User B's ratings

3. **Test execution script:**
   - [ ] Create `npm run test:rls` command
   - [ ] Add to CI/CD pipeline (future)
   - [ ] Document test coverage

**Test Template:**
```typescript
import { describe, it, expect } from 'vitest';
import { createClient } from '@supabase/supabase-js';

describe('RLS: Collections', () => {
  it('User cannot read other user private collections', async () => {
    const supabase = createClient(URL, KEY, {
      auth: { persistSession: false }
    });

    // Sign in as User A
    await supabase.auth.signInWithPassword({
      email: 'userA@test.com',
      password: 'password'
    });

    // Try to read User B's private collection
    const { data, error } = await supabase
      .from('collections')
      .select('*')
      .eq('id', 'user-b-collection-id');

    expect(data).toHaveLength(0); // Should not return User B's data
  });
});
```

**Verification:**
```bash
npm run test:rls
# All tests should pass
```

**Acceptance Criteria:**
- 100% of RLS policies have corresponding tests
- All tests pass
- Tests cover both positive (allowed) and negative (denied) cases
- Tests run in <10 seconds

---

### Task 5: Seed Data Creation (Day 5-7)

**Deliverable:** 50 high-quality starter prompts across 5 categories

#### Subtasks

1. **Define categories:**
   - [ ] Marketing (10 prompts)
   - [ ] Code (10 prompts)
   - [ ] Writing (10 prompts)
   - [ ] Research (10 prompts)
   - [ ] Personal (10 prompts)

2. **Prompt structure requirements:**
   - [ ] Title (clear, action-oriented)
   - [ ] Description (what it does, when to use it)
   - [ ] Template with variables (e.g., `[brand_name]`, `[target_audience]`)
   - [ ] Skill level (beginner, intermediate, advanced)
   - [ ] AI model compatibility (ChatGPT, Claude, Gemini, All)
   - [ ] Variables with helper text and defaults

3. **Create Marketing prompts (10):**
   - [ ] Cold email outreach
   - [ ] LinkedIn post generator
   - [ ] Product description writer
   - [ ] Email subject line optimizer
   - [ ] Content calendar planner
   - [ ] Ad copy generator (Facebook/Google)
   - [ ] Customer persona builder
   - [ ] Competitor analysis
   - [ ] Blog post outline
   - [ ] Social media caption writer

4. **Create Code prompts (10):**
   - [ ] Code review assistant
   - [ ] Bug debugger
   - [ ] Function documentation generator
   - [ ] Unit test writer
   - [ ] Code refactoring suggestions
   - [ ] API endpoint design
   - [ ] Database schema designer
   - [ ] Error message explainer
   - [ ] Algorithm optimizer
   - [ ] Code comment generator

5. **Create Writing prompts (10):**
   - [ ] Blog post intro writer
   - [ ] Essay outline generator
   - [ ] Grammar and clarity improver
   - [ ] Storytelling assistant
   - [ ] Headline generator
   - [ ] Email reply drafter
   - [ ] Meeting notes summarizer
   - [ ] Report writer
   - [ ] Newsletter content
   - [ ] Press release generator

6. **Create Research prompts (10):**
   - [ ] Literature review assistant
   - [ ] Data analysis helper
   - [ ] Survey question generator
   - [ ] Market research analyst
   - [ ] Citation formatter
   - [ ] Research question refiner
   - [ ] Interview question builder
   - [ ] Trend analyzer
   - [ ] Competitive intelligence
   - [ ] Expert interviewer

7. **Create Personal prompts (10):**
   - [ ] Resume bullet point writer
   - [ ] Cover letter generator
   - [ ] Career advice assistant
   - [ ] Learning plan creator
   - [ ] Book recommendation finder
   - [ ] Meal planning assistant
   - [ ] Travel itinerary planner
   - [ ] Decision-making framework
   - [ ] Habit formation guide
   - [ ] Goal setting assistant

8. **Add Prompt DNA annotations:**
   - [ ] Annotate 10 "featured" prompts with DNA
   - [ ] DNA components: Role, Context, Instruction, Constraints, Tone
   - [ ] Keep explanations under 50 tokens each
   - [ ] Test DNA rendering in UI (Phase 6)

**Prompt Quality Checklist:**
- [ ] Clear, actionable title
- [ ] Descriptive summary (1-2 sentences)
- [ ] 3-5 variables per prompt
- [ ] Helper text for each variable
- [ ] Smart defaults where applicable
- [ ] Token count: 200-500 tokens per prompt
- [ ] Tested with at least 1 AI model

**Seed Data Format:**
```sql
INSERT INTO prompts (
  title,
  description,
  template,
  category,
  skill_level,
  ai_model,
  author_id,
  status
) VALUES (
  'Cold Email Outreach',
  'Generate personalized cold emails that get responses. Perfect for B2B sales and outreach.',
  'You are a senior sales copywriter...\n\nWrite a cold email to [target_role] at [industry] companies about [product/service]...',
  'marketing',
  'intermediate',
  'all',
  (SELECT id FROM users WHERE email = 'admin@prompttoolkit.com'),
  'published'
);
```

**Verification:**
```sql
-- Count prompts per category
SELECT category, COUNT(*) FROM prompts GROUP BY category;
-- Should show 10 per category

-- Check all have variables
SELECT id, title FROM prompts
WHERE template NOT LIKE '%[%]%';
-- Should return 0 rows

-- Check token counts (approximate)
SELECT id, title, LENGTH(template) FROM prompts
WHERE LENGTH(template) > 2000;
-- Should return 0 rows (prompts too long)
```

**Acceptance Criteria:**
- 50 prompts across 5 categories (balanced)
- All prompts have 3+ variables
- All prompts have helper text
- 10 prompts have Prompt DNA annotations
- No prompt exceeds 500 tokens
- All prompts tested with at least 1 AI model

---

### Task 6: Full-Text Search Implementation (Day 7-8)

**Deliverable:** Working PostgreSQL full-text search on prompts

#### Subtasks

1. **Create search function:**
   - [ ] Create `search_prompts()` SQL function
   - [ ] Support query syntax: `search_prompts('marketing email')`
   - [ ] Return ranked results (relevance score)
   - [ ] Support filters (category, skill_level, ai_model)

2. **Add search trigger:**
   - [ ] Create trigger function to update `search_vector` on INSERT/UPDATE
   - [ ] Trigger combines title + description + template
   - [ ] Weighted ranking: title (A), description (B), template (C)

3. **Test search performance:**
   - [ ] Benchmark with 50 prompts
   - [ ] Benchmark with 500 prompts (simulate growth)
   - [ ] Benchmark with 5,000 prompts (future scale)
   - [ ] Target: <100ms response time

4. **Create search API endpoint:**
   - [ ] Supabase RPC function: `rpc('search_prompts', { query: 'email' })`
   - [ ] Next.js API route: `app/api/search/route.ts`
   - [ ] Return: prompts + relevance score + total count

**SQL Implementation:**
```sql
-- Add search vector column
ALTER TABLE prompts
ADD COLUMN search_vector tsvector;

-- Create GIN index
CREATE INDEX prompts_search_vector_idx
ON prompts USING GIN (search_vector);

-- Create trigger function
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
  NEW.search_vector :=
    setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(NEW.template, '')), 'C');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach trigger
CREATE TRIGGER prompts_search_update
BEFORE INSERT OR UPDATE ON prompts
FOR EACH ROW EXECUTE FUNCTION update_search_vector();

-- Search function
CREATE OR REPLACE FUNCTION search_prompts(search_query TEXT)
RETURNS TABLE (
  id UUID,
  title TEXT,
  description TEXT,
  category TEXT,
  rank REAL
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    p.id,
    p.title,
    p.description,
    p.category,
    ts_rank(p.search_vector, plainto_tsquery('english', search_query)) AS rank
  FROM prompts p
  WHERE p.search_vector @@ plainto_tsquery('english', search_query)
    AND p.status = 'published'
  ORDER BY rank DESC;
END;
$$ LANGUAGE plpgsql;
```

**Performance Benchmark:**
```sql
-- Test search speed
EXPLAIN ANALYZE
SELECT * FROM search_prompts('marketing email');

-- Should use GIN index, <100ms execution time
```

**Verification:**
```bash
# Test search via Supabase
curl -X POST 'https://[project].supabase.co/rest/v1/rpc/search_prompts' \
  -H "apikey: [key]" \
  -H "Content-Type: application/json" \
  -d '{"search_query": "email marketing"}'

# Should return ranked results in <100ms
```

**Acceptance Criteria:**
- Full-text search returns relevant results
- Search is case-insensitive
- Search ranks title matches higher than description
- Search performance <100ms for 500 prompts
- GIN index is used (verified with EXPLAIN ANALYZE)

---

### Task 7: Database Performance Optimization (Day 8-9)

**Deliverable:** Optimized database with pagination and caching

#### Subtasks

1. **Add pagination support:**
   - [ ] Modify search function to support LIMIT and OFFSET
   - [ ] Create `get_prompts_paginated()` function
   - [ ] Return total count + page data
   - [ ] Default page size: 20

2. **Connection pooling:**
   - [ ] Configure Supabase connection pooler (transaction mode)
   - [ ] Set max connections: 15 (free tier limit)
   - [ ] Configure Next.js to use pooler URL

3. **Query optimization:**
   - [ ] Add `EXPLAIN ANALYZE` to all major queries
   - [ ] Ensure all queries use indexes
   - [ ] Remove N+1 queries (use JOINs or batch queries)

4. **Caching strategy:**
   - [ ] Cache popular prompts (Redis or Supabase cache)
   - [ ] Cache search results (5-minute TTL)
   - [ ] Implement stale-while-revalidate pattern

**Pagination Function:**
```sql
CREATE OR REPLACE FUNCTION get_prompts_paginated(
  page_size INT DEFAULT 20,
  page_offset INT DEFAULT 0,
  filter_category TEXT DEFAULT NULL
)
RETURNS TABLE (
  id UUID,
  title TEXT,
  description TEXT,
  category TEXT,
  total_count BIGINT
) AS $$
BEGIN
  RETURN QUERY
  WITH filtered AS (
    SELECT * FROM prompts
    WHERE status = 'published'
      AND (filter_category IS NULL OR category = filter_category)
  )
  SELECT
    f.id,
    f.title,
    f.description,
    f.category,
    (SELECT COUNT(*) FROM filtered) AS total_count
  FROM filtered f
  ORDER BY f.created_at DESC
  LIMIT page_size
  OFFSET page_offset;
END;
$$ LANGUAGE plpgsql;
```

**Verification:**
```sql
-- Test pagination
SELECT * FROM get_prompts_paginated(20, 0, 'marketing');
SELECT * FROM get_prompts_paginated(20, 20, 'marketing');

-- Verify total_count is consistent
```

**Acceptance Criteria:**
- Pagination works correctly (no duplicates, no gaps)
- Total count is accurate
- Query performance <50ms
- Connection pooling configured

---

### Task 8: Documentation (Day 9-10)

**Deliverable:** Complete database documentation

#### Subtasks

1. **Schema documentation:**
   - [ ] Create `DATABASE.md` in `.planning/phase-1/`
   - [ ] Document all tables with field descriptions
   - [ ] Document all indexes and their purpose
   - [ ] Document RLS policies

2. **ERD diagram:**
   - [ ] Export ERD as PNG
   - [ ] Add to `DATABASE.md`
   - [ ] Annotate relationships

3. **API documentation:**
   - [ ] Document Supabase RPC functions
   - [ ] Document query parameters
   - [ ] Provide example requests/responses

4. **Performance benchmarks:**
   - [ ] Document search performance
   - [ ] Document pagination performance
   - [ ] Document RLS overhead

**Documentation Template:**
```markdown
# Database Schema Documentation

## Tables

### `prompts`
Stores all prompt templates.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| title | TEXT | Prompt title (indexed for search) |
| template | TEXT | Prompt template with variables |
| category | TEXT | Category (marketing, code, writing, etc.) |
| skill_level | TEXT | beginner, intermediate, advanced |
| author_id | UUID | Foreign key to users |
| version | INT | Version number for versioning |
| parent_id | UUID | Parent prompt for forks/remixes |

## RLS Policies

### `collections`
- **SELECT:** Users can view own + public collections
- **INSERT:** Users can create collections (user_id = auth.uid())
- **UPDATE:** Users can update own collections
- **DELETE:** Users can delete own collections

## Performance Benchmarks

- **Search (50 prompts):** ~15ms
- **Search (500 prompts):** ~45ms
- **Pagination (20 results):** ~12ms
```

**Acceptance Criteria:**
- All tables documented
- All RLS policies explained
- ERD diagram included
- Performance benchmarks recorded

---

### Task 9: Integration Testing (Day 10)

**Deliverable:** End-to-end tests for database operations

#### Subtasks

1. **Create test suite:**
   - [ ] Test: Create user → Create collection → Add prompts
   - [ ] Test: Search prompts → Get paginated results
   - [ ] Test: User customization → Save → Retrieve
   - [ ] Test: Rate prompt → Calculate average rating

2. **Test RLS in real scenarios:**
   - [ ] User A creates collection
   - [ ] User B cannot access User A's private collection
   - [ ] User B can access User A's public collection
   - [ ] User B forks prompt from User A

3. **Performance tests:**
   - [ ] Load 500 prompts
   - [ ] Search 100 times (different queries)
   - [ ] Measure average response time
   - [ ] Verify <100ms for search

**Test Execution:**
```bash
npm run test:integration
# All tests should pass
```

**Acceptance Criteria:**
- All integration tests pass
- Performance tests meet <100ms target
- No RLS violations detected

---

### Task 10: Production Deployment (Day 10)

**Deliverable:** Database live on Supabase production

#### Subtasks

1. **Apply migrations to production:**
   - [ ] Backup existing data (if any)
   - [ ] Run: `npx supabase db push --linked`
   - [ ] Verify all tables created
   - [ ] Verify RLS policies enabled

2. **Load seed data:**
   - [ ] Run seed migration
   - [ ] Verify 50 prompts loaded
   - [ ] Test search in production

3. **Configure monitoring:**
   - [ ] Enable Supabase query performance monitoring
   - [ ] Set up alerts for slow queries (>500ms)
   - [ ] Monitor connection pool usage

4. **Security audit:**
   - [ ] Run RLS test suite against production
   - [ ] Verify no public access to private data
   - [ ] Test anonymous vs authenticated access

**Verification:**
```bash
# Production health check
curl -X POST 'https://[project].supabase.co/rest/v1/rpc/search_prompts' \
  -H "apikey: [anon-key]" \
  -d '{"search_query": "marketing"}'

# Should return results
```

**Acceptance Criteria:**
- Database live on Supabase
- 50 seed prompts accessible
- Search works in production
- RLS tests pass in production
- Monitoring enabled

---

## Phase Completion Checklist

- [ ] All 10 tasks completed
- [ ] Database schema supports versioning, attribution, marketplace
- [ ] RLS policies prevent data leakage (100% test pass rate)
- [ ] 50 seed prompts across 5 categories
- [ ] Full-text search <100ms
- [ ] Pagination working (20 per page)
- [ ] Documentation complete (DATABASE.md, ERD)
- [ ] Integration tests pass
- [ ] Production deployment successful
- [ ] Monitoring enabled

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| RLS policy gaps | Medium | High | Comprehensive test suite, security audit |
| Search performance degradation | Medium | Medium | Benchmarks at 500/5K prompts, GIN index |
| Migration rollback needed | Low | High | Test migrations locally, create down migrations |
| Seed data quality issues | Medium | Low | Manual review, test with real AI models |
| Connection pool exhaustion | Low | Medium | Configure pooler, monitor usage |

---

## Next Steps After Phase 1

1. **Phase 2:** Build `/browse` page to display prompts
2. **Phase 3:** Build prompt customizer with variable substitution
3. **Integration:** Connect Next.js frontend to database
4. **Testing:** E2E tests for prompt browsing and search

---

*Phase 1 establishes the data foundation. Everything else builds on this.*
