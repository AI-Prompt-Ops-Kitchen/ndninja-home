# Prompt Toolkit - Database Documentation

> **Schema Version:** 1.0
> **Last Updated:** 2026-02-10
> **Database:** PostgreSQL 14+
> **Extensions:** uuid-ossp, pg_trgm

---

## Overview

The Prompt Toolkit database is designed to support a SaaS platform for discovering, customizing, and sharing AI prompts. The schema prioritizes:

- **Versioning**: Track prompt evolution through `parent_id` and `version` fields
- **Attribution**: Full author tracking with `author_id` and `created_by` fields
- **Marketplace**: Support for ratings, public collections, and user customizations
- **Performance**: Full-text search with GIN indexes, optimized for <100ms queries
- **Security**: Row-Level Security (RLS) ready for all user-owned tables

---

## Core Entities

### 1. Users

Stores user accounts and profiles.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    avatar_url TEXT,
    bio TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**Relationships:**
- Creates → prompts (author)
- Owns → collections
- Rates → prompt_ratings
- Customizes → user_customizations
- Uses → prompt_usage

---

### 2. Prompts

Core entity storing prompt templates.

```sql
CREATE TABLE prompts (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT NOT NULL,
    template TEXT NOT NULL,

    -- Categorization
    category category_type NOT NULL,
    skill_level skill_level_type NOT NULL DEFAULT 'beginner',
    ai_model ai_model_type NOT NULL DEFAULT 'universal',
    tags TEXT[] DEFAULT '{}',

    -- Attribution & Versioning
    author_id UUID NOT NULL REFERENCES users(id),
    version INTEGER NOT NULL DEFAULT 1,
    parent_id UUID REFERENCES prompts(id),

    -- Status & Features
    status prompt_status_type NOT NULL DEFAULT 'published',
    is_featured BOOLEAN NOT NULL DEFAULT false,

    -- Metrics
    usage_count INTEGER NOT NULL DEFAULT 0,
    fork_count INTEGER NOT NULL DEFAULT 0,
    avg_rating DECIMAL(3,2),

    -- Full-text search
    search_vector TSVECTOR,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**Key Features:**

1. **Versioning**: `parent_id` creates a version tree
   - Original prompt: `parent_id = NULL`
   - Fork/version: `parent_id = <original_prompt_id>`
   - `version` auto-increments for each fork

2. **Full-text Search**: `search_vector` auto-updated by trigger
   - Weighted: Title (A) > Tags/Description (B) > Template (C)
   - Searchable via `search_prompts()` function

3. **Enums**:
   - `category_type`: marketing, code, writing, research, personal, business, education, creative
   - `skill_level_type`: beginner, intermediate, advanced, expert
   - `ai_model_type`: gpt4, claude, gemini, llama, universal
   - `prompt_status_type`: draft, published, archived, flagged

**Relationships:**
- Belongs to → users (author)
- Has many → prompt_variables
- Has many → prompt_dna
- Has many → prompt_versions
- Receives → prompt_ratings
- Used in → prompt_usage
- Included in → collection_prompts

---

### 3. Prompt Variables

Dynamic form fields for prompt customization.

```sql
CREATE TABLE prompt_variables (
    id UUID PRIMARY KEY,
    prompt_id UUID NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,

    name TEXT NOT NULL,
    label TEXT NOT NULL,
    helper_text TEXT,
    placeholder TEXT,
    default_value TEXT,
    suggestions TEXT[],

    -- Validation
    required BOOLEAN NOT NULL DEFAULT true,
    variable_type TEXT NOT NULL DEFAULT 'text',
    max_length INTEGER,

    "order" INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(prompt_id, name)
);
```

**Variable Types:**
- `text`: Single-line text input
- `textarea`: Multi-line text input
- `select`: Dropdown (uses `suggestions` array)
- `number`: Numeric input

**Example:**
```sql
INSERT INTO prompt_variables (prompt_id, name, label, helper_text, suggestions)
VALUES (
    'uuid-prompt',
    'target_audience',
    'Target Audience',
    'Who are you writing for?',
    ARRAY['developers', 'marketers', 'students', 'executives']
);
```

---

### 4. Prompt DNA

Educational annotations explaining prompt components.

```sql
CREATE TABLE prompt_dna (
    id UUID PRIMARY KEY,
    prompt_id UUID NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,

    component_type TEXT NOT NULL,
    highlight_start INTEGER NOT NULL,
    highlight_end INTEGER NOT NULL,

    explanation TEXT NOT NULL,
    why_it_works TEXT,

    "order" INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**Component Types:**
- `persona`: Who the AI should act as
- `constraints`: Boundaries and rules
- `format`: Output structure
- `examples`: Sample inputs/outputs
- `context`: Background information

**Example:**
```sql
INSERT INTO prompt_dna (prompt_id, component_type, highlight_start, highlight_end, explanation)
VALUES (
    'uuid-prompt',
    'persona',
    0,
    42,
    'Sets the AI to act as an expert copywriter, which primes it for persuasive language.'
);
```

---

### 5. Collections

User-curated lists of prompts.

```sql
CREATE TABLE collections (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    name TEXT NOT NULL,
    description TEXT,
    slug TEXT NOT NULL,

    is_public BOOLEAN NOT NULL DEFAULT false,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(user_id, slug)
);
```

**Junction Table:**
```sql
CREATE TABLE collection_prompts (
    id UUID PRIMARY KEY,
    collection_id UUID NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    prompt_id UUID NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,

    "order" INTEGER NOT NULL DEFAULT 0,
    added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(collection_id, prompt_id)
);
```

---

### 6. Supporting Tables

#### Prompt Versions (Audit Trail)
```sql
CREATE TABLE prompt_versions (
    id UUID PRIMARY KEY,
    prompt_id UUID NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,

    version_number INTEGER NOT NULL,
    template TEXT NOT NULL,
    variables_schema JSONB,
    change_summary TEXT NOT NULL,

    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(prompt_id, version_number)
);
```

#### Prompt Ratings
```sql
CREATE TABLE prompt_ratings (
    id UUID PRIMARY KEY,
    prompt_id UUID NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(prompt_id, user_id)
);
```

#### User Customizations
```sql
CREATE TABLE user_customizations (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    prompt_id UUID NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,

    customized_template TEXT NOT NULL,
    variables_json JSONB,
    custom_notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### Prompt Usage (Analytics)
```sql
CREATE TABLE prompt_usage (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    prompt_id UUID NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,

    used_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    platform TEXT,
    was_helpful BOOLEAN
);
```

---

## Indexes

### Performance Indexes

```sql
-- Full-text search (GIN)
CREATE INDEX idx_prompts_search_vector ON prompts USING GIN(search_vector);

-- Tag search (GIN for arrays)
CREATE INDEX idx_prompts_tags ON prompts USING GIN(tags);

-- Foreign key indexes
CREATE INDEX idx_prompts_author_id ON prompts(author_id);
CREATE INDEX idx_collections_user_id ON collections(user_id);
CREATE INDEX idx_prompt_variables_prompt_id ON prompt_variables(prompt_id);

-- Filtering indexes
CREATE INDEX idx_prompts_category ON prompts(category);
CREATE INDEX idx_prompts_skill_level ON prompts(skill_level);
CREATE INDEX idx_prompts_status ON prompts(status);

-- Sorting indexes
CREATE INDEX idx_prompts_created_at ON prompts(created_at DESC);
CREATE INDEX idx_prompt_usage_user_id ON prompt_usage(user_id, used_at DESC);

-- Partial indexes (filtered)
CREATE INDEX idx_prompts_featured ON prompts(is_featured) WHERE is_featured = true;
CREATE INDEX idx_collections_is_public ON collections(is_public) WHERE is_public = true;
```

**Index Strategy:**
- GIN indexes for full-text search and array columns
- B-tree indexes for foreign keys, enums, and timestamps
- Partial indexes for commonly filtered boolean columns
- Composite indexes for common query patterns (user_id + timestamp)

---

## Triggers

### 1. Auto-update Timestamps

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Applied to: users, prompts, collections, prompt_ratings, user_customizations
```

### 2. Auto-update Search Vector

```sql
CREATE OR REPLACE FUNCTION update_prompts_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.template, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(array_to_string(NEW.tags, ' '), '')), 'B');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

**Weighting:**
- A (highest): title
- B (medium): description, tags
- C (lowest): template

### 3. Auto-calculate Average Rating

```sql
CREATE OR REPLACE FUNCTION update_prompt_avg_rating()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE prompts
    SET avg_rating = (
        SELECT ROUND(AVG(rating)::numeric, 2)
        FROM prompt_ratings
        WHERE prompt_id = COALESCE(NEW.prompt_id, OLD.prompt_id)
    )
    WHERE id = COALESCE(NEW.prompt_id, OLD.prompt_id);
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Triggered on INSERT, UPDATE, DELETE of prompt_ratings
```

---

## Functions

### search_prompts()

Full-text search with filters, pagination, and relevance ranking.

```sql
SELECT * FROM search_prompts(
    'marketing email',              -- search query
    'marketing'::category_type,     -- category filter (optional)
    'beginner'::skill_level_type,   -- skill level filter (optional)
    20,                              -- limit
    0                                -- offset
);
```

**Returns:**
- id, title, slug, description, category, skill_level, avg_rating, usage_count, rank

**Features:**
- Uses PostgreSQL full-text search (tsquery)
- Ranks results by relevance (ts_rank)
- Secondary sort by avg_rating
- Filters by status = 'published'
- Supports NULL filters (shows all)

### get_prompt_details()

Fetch prompt with all related data in a single query.

```sql
SELECT get_prompt_details('my-prompt-slug');
```

**Returns JSON:**
```json
{
  "prompt": { /* prompt fields */ },
  "variables": [ /* array of variables */ ],
  "dna": [ /* array of DNA annotations */ ],
  "author": { /* user fields */ }
}
```

---

## Views

### prompts_with_author

Prompts joined with author name and avatar.

```sql
SELECT * FROM prompts_with_author
WHERE category = 'marketing'
ORDER BY created_at DESC;
```

### popular_prompts

Top prompts by usage in the last 30 days.

```sql
SELECT * FROM popular_prompts
LIMIT 10;
```

---

## Common Queries

### 1. Get all prompts by category

```sql
SELECT id, title, slug, description, avg_rating
FROM prompts
WHERE category = 'code'
  AND status = 'published'
ORDER BY created_at DESC
LIMIT 20;
```

### 2. Search prompts with full-text search

```sql
SELECT * FROM search_prompts(
    'write email campaign',
    NULL,  -- any category
    NULL,  -- any skill level
    20,
    0
);
```

### 3. Get prompt with variables and DNA

```sql
SELECT get_prompt_details('cold-email-template');
```

### 4. Get user's collections

```sql
SELECT c.*, COUNT(cp.id) AS prompt_count
FROM collections c
LEFT JOIN collection_prompts cp ON c.id = cp.collection_id
WHERE c.user_id = 'user-uuid'
GROUP BY c.id
ORDER BY c.updated_at DESC;
```

### 5. Get prompt version history

```sql
SELECT version_number, change_summary, created_by, created_at
FROM prompt_versions
WHERE prompt_id = 'prompt-uuid'
ORDER BY version_number DESC;
```

### 6. Track prompt usage

```sql
INSERT INTO prompt_usage (user_id, prompt_id, platform)
VALUES ('user-uuid', 'prompt-uuid', 'chatgpt');
```

### 7. Rate a prompt

```sql
INSERT INTO prompt_ratings (prompt_id, user_id, rating, notes)
VALUES ('prompt-uuid', 'user-uuid', 5, 'Excellent template!')
ON CONFLICT (prompt_id, user_id)
DO UPDATE SET rating = EXCLUDED.rating, notes = EXCLUDED.notes;

-- avg_rating is auto-calculated by trigger
```

---

## Performance Considerations

### Query Performance Targets
- **Full-text search**: <100ms
- **Browse/filter**: <200ms
- **Prompt detail page**: <150ms

### Optimization Strategies

1. **Use prepared statements** to avoid query planning overhead
2. **Paginate results** (LIMIT/OFFSET or cursor-based)
3. **Use partial indexes** for boolean filters (is_featured, is_public)
4. **Connection pooling** (pgBouncer or Supabase built-in)
5. **Cache frequently accessed data** (Redis for popular prompts)

### Index Maintenance

```sql
-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;

-- Rebuild indexes (if fragmented)
REINDEX INDEX idx_prompts_search_vector;

-- Update statistics
ANALYZE prompts;
```

---

## Row-Level Security (RLS)

### Tables Requiring RLS
- `collections` (users can only see their own or public collections)
- `user_customizations` (users can only see their own)
- `prompt_usage` (users can only see their own)
- `prompt_ratings` (users can see their own, read others on published prompts)

### Example RLS Policies

```sql
-- Collections: Users see their own + public collections
ALTER TABLE collections ENABLE ROW LEVEL SECURITY;

CREATE POLICY collections_select_policy ON collections
FOR SELECT
USING (
    user_id = auth.uid()
    OR is_public = true
);

CREATE POLICY collections_insert_policy ON collections
FOR INSERT
WITH CHECK (user_id = auth.uid());

CREATE POLICY collections_update_policy ON collections
FOR UPDATE
USING (user_id = auth.uid())
WITH CHECK (user_id = auth.uid());

CREATE POLICY collections_delete_policy ON collections
FOR DELETE
USING (user_id = auth.uid());
```

**Note:** Replace `auth.uid()` with your auth provider's user ID function (Supabase uses `auth.uid()`).

---

## Versioning Strategy

### Creating a Fork

```sql
-- 1. Create new prompt as fork
INSERT INTO prompts (
    title, slug, description, template,
    category, skill_level, ai_model,
    author_id, version, parent_id,
    status
)
SELECT
    title || ' (Fork)',
    slug || '-fork-' || gen_random_uuid(),
    description,
    template,
    category, skill_level, ai_model,
    'new-user-uuid',  -- new author
    (SELECT COALESCE(MAX(version), 0) + 1 FROM prompts WHERE parent_id = id OR id = parent_id),
    id,  -- original prompt
    'draft'
FROM prompts
WHERE id = 'original-prompt-uuid';

-- 2. Copy variables
INSERT INTO prompt_variables (prompt_id, name, label, helper_text, default_value, suggestions, required, variable_type, max_length, "order")
SELECT 'new-prompt-uuid', name, label, helper_text, default_value, suggestions, required, variable_type, max_length, "order"
FROM prompt_variables
WHERE prompt_id = 'original-prompt-uuid';

-- 3. (Optional) Copy DNA annotations
INSERT INTO prompt_dna (prompt_id, component_type, highlight_start, highlight_end, explanation, why_it_works, "order")
SELECT 'new-prompt-uuid', component_type, highlight_start, highlight_end, explanation, why_it_works, "order"
FROM prompt_dna
WHERE prompt_id = 'original-prompt-uuid';
```

### Version Tree Navigation

```sql
-- Get original prompt
SELECT * FROM prompts WHERE id = (
    SELECT COALESCE(parent_id, id) FROM prompts WHERE id = 'current-prompt-uuid'
);

-- Get all versions/forks
SELECT * FROM prompts
WHERE parent_id = 'original-prompt-uuid'
   OR id = 'original-prompt-uuid'
ORDER BY version ASC;
```

---

## Migration Strategy

### Phase 1: Initial Schema
1. Create all tables, indexes, enums
2. Create triggers and functions
3. Create views
4. Seed data (50 prompts)

### Phase 2: RLS Policies
1. Enable RLS on user-owned tables
2. Create SELECT/INSERT/UPDATE/DELETE policies
3. Test with automated suite

### Phase 3: Production Deployment
1. Apply migrations to Supabase production
2. Enable RLS
3. Configure connection pooling
4. Set up monitoring

---

## Monitoring & Maintenance

### Key Metrics
- Query response time (p50, p95, p99)
- Index hit rate (should be >95%)
- Connection pool usage
- Table sizes and growth rate
- Full-text search performance

### Queries for Monitoring

```sql
-- Table sizes
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Index hit rate (should be >95%)
SELECT
    sum(idx_blks_hit) / NULLIF(sum(idx_blks_hit + idx_blks_read), 0) * 100 AS index_hit_rate
FROM pg_statio_user_indexes;

-- Slow queries (enable pg_stat_statements extension)
SELECT
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    max_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

---

## ERD

See [erd.md](./.planning/phase-1/erd.md) for the full Entity Relationship Diagram.

---

## Next Steps

1. **Task 2**: Create Supabase migrations from this schema
2. **Task 3**: Implement Row-Level Security policies
3. **Task 4**: Build automated RLS test suite
4. **Task 5**: Create 50 seed prompts
5. **Task 6**: Test full-text search performance
6. **Task 7**: Optimize with pagination and connection pooling
7. **Task 8**: Deploy to production
