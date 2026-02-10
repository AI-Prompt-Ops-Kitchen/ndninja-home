# Supabase Migrations

This directory contains database migrations for the Prompt Toolkit SaaS project.

## Migrations

### 1. `20260210175024_initial_schema.sql`
- Creates all database tables, indexes, and constraints
- Sets up full-text search infrastructure (GIN indexes)
- Defines triggers for auto-updating timestamps, search vectors, and ratings
- Creates helper functions (`search_prompts`, `get_prompt_details`)
- Creates views (`prompts_with_author`, `popular_prompts`)

**Tables created:**
- `users` - User accounts
- `prompts` - Core prompt templates
- `prompt_variables` - Dynamic form fields
- `prompt_dna` - Educational annotations
- `collections` - User-curated lists
- `collection_prompts` - Many-to-many junction
- `prompt_versions` - Version history
- `prompt_ratings` - User ratings (1-5 stars)
- `user_customizations` - Saved/forked prompts
- `prompt_usage` - Analytics tracking

### 2. `20260210175135_seed_data.sql`
- Seeds 50 high-quality starter prompts
- Covers 5 categories (10 prompts each):
  - **Marketing**: Cold emails, social media, SEO, ads, landing pages
  - **Code**: Code review, API generation, SQL optimization, testing, documentation
  - **Writing**: Blog posts, emails, stories, LinkedIn, technical docs
  - **Research**: Summaries, competitive analysis, market research, surveys
  - **Personal**: Career planning, goals, learning, routines, budgeting
- Includes prompt variables for customization
- Includes Prompt DNA annotations for featured prompts

## Usage

### Local Development

```bash
# Start local Supabase (requires Docker)
npx supabase start

# Reset database (apply all migrations)
npx supabase db reset

# Check migration status
npx supabase migration list

# Create new migration
npx supabase migration new <name>
```

### Production Deployment

```bash
# Link to Supabase project
npx supabase link --project-ref <project-id>

# Push migrations to production
npx supabase db push

# Verify schema
npx supabase db diff
```

## Testing Migrations

### Test Rollback

Migrations should be idempotent and reversible:

```bash
# Apply migrations
npx supabase db reset

# Check database state
npx supabase db diff

# Rollback (manual - Supabase doesn't support down migrations)
# Drop all tables in reverse dependency order
```

### Verify Schema

After applying migrations:

```sql
-- Check tables exist
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- Check indexes
SELECT indexname, tablename FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- Test full-text search
SELECT * FROM search_prompts('marketing email', NULL, NULL, 10, 0);

-- Verify seed data
SELECT category, COUNT(*) FROM prompts GROUP BY category;
```

## Migration Best Practices

1. **Never modify existing migrations** - Create new ones for changes
2. **Test locally first** - Always use `supabase db reset` before pushing
3. **Idempotent migrations** - Use `IF NOT EXISTS` and `OR REPLACE`
4. **Reversible operations** - Document rollback steps
5. **Seed data separately** - Keep schema and data migrations separate
6. **Version control** - Commit migrations before pushing to remote

## Troubleshooting

### Migration fails to apply

```bash
# Check migration status
npx supabase migration list

# View error details
npx supabase db reset --debug

# Verify SQL syntax
psql -f supabase/migrations/<migration>.sql
```

### Database out of sync

```bash
# Generate diff from remote
npx supabase db diff -f <name>

# Review generated migration
# Apply if correct
npx supabase db push
```

## Row-Level Security (RLS)

RLS policies are applied in a separate migration (Task 3). User-owned tables:
- `collections`
- `user_customizations`
- `prompt_usage`
- `prompt_ratings`

## Performance Targets

- Full-text search: <100ms
- Prompt detail page: <150ms
- Browse/filter: <200ms

Achieved through:
- GIN indexes on `search_vector` and `tags`
- B-tree indexes on foreign keys and filters
- Partial indexes on boolean columns
- Materialized views for complex aggregations (future)

## Next Steps

After migrations are applied:

1. **Task 3**: Implement RLS policies
2. **Task 4**: Build automated RLS test suite
3. **Task 6**: Test full-text search performance
4. **Task 7**: Optimize with pagination and connection pooling
5. **Task 10**: Deploy to Supabase production
