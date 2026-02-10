# Prompt Toolkit Database ERD

```mermaid
erDiagram
    users ||--o{ prompts : "creates"
    users ||--o{ collections : "owns"
    users ||--o{ prompt_ratings : "rates"
    users ||--o{ user_customizations : "customizes"
    users ||--o{ prompt_usage : "uses"
    users ||--o{ prompt_versions : "creates_version"

    prompts ||--o{ prompt_variables : "has"
    prompts ||--o{ prompt_dna : "explains"
    prompts ||--o{ prompt_versions : "versioned_as"
    prompts ||--o{ prompt_ratings : "receives"
    prompts ||--o{ user_customizations : "customized_in"
    prompts ||--o{ prompt_usage : "tracked_in"
    prompts ||--o{ collection_prompts : "included_in"
    prompts ||--o{ prompts : "forks (parent_id)"

    collections ||--o{ collection_prompts : "contains"
    prompts ||--o{ collection_prompts : "belongs_to"

    users {
        UUID id PK
        TEXT email UK
        TEXT name
        TEXT avatar_url
        TEXT bio
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    prompts {
        UUID id PK
        TEXT title
        TEXT slug UK
        TEXT description
        TEXT template
        category_type category
        skill_level_type skill_level
        ai_model_type ai_model
        TEXT[] tags
        UUID author_id FK
        INTEGER version
        UUID parent_id FK
        prompt_status_type status
        BOOLEAN is_featured
        INTEGER usage_count
        INTEGER fork_count
        DECIMAL avg_rating
        TSVECTOR search_vector
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    prompt_variables {
        UUID id PK
        UUID prompt_id FK
        TEXT name
        TEXT label
        TEXT helper_text
        TEXT placeholder
        TEXT default_value
        TEXT[] suggestions
        BOOLEAN required
        TEXT variable_type
        INTEGER max_length
        INTEGER order
        TIMESTAMPTZ created_at
    }

    prompt_dna {
        UUID id PK
        UUID prompt_id FK
        TEXT component_type
        INTEGER highlight_start
        INTEGER highlight_end
        TEXT explanation
        TEXT why_it_works
        INTEGER order
        TIMESTAMPTZ created_at
    }

    collections {
        UUID id PK
        UUID user_id FK
        TEXT name
        TEXT description
        TEXT slug
        BOOLEAN is_public
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    collection_prompts {
        UUID id PK
        UUID collection_id FK
        UUID prompt_id FK
        INTEGER order
        TIMESTAMPTZ added_at
    }

    prompt_versions {
        UUID id PK
        UUID prompt_id FK
        INTEGER version_number
        TEXT template
        JSONB variables_schema
        TEXT change_summary
        UUID created_by FK
        TIMESTAMPTZ created_at
    }

    prompt_ratings {
        UUID id PK
        UUID prompt_id FK
        UUID user_id FK
        INTEGER rating
        TEXT notes
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    user_customizations {
        UUID id PK
        UUID user_id FK
        UUID prompt_id FK
        TEXT customized_template
        JSONB variables_json
        TEXT custom_notes
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    prompt_usage {
        UUID id PK
        UUID user_id FK
        UUID prompt_id FK
        TIMESTAMPTZ used_at
        TEXT platform
        BOOLEAN was_helpful
    }
```

## Key Relationships

### One-to-Many
- **users → prompts**: A user can create many prompts (author)
- **users → collections**: A user can create many collections
- **users → prompt_ratings**: A user can rate many prompts
- **users → user_customizations**: A user can customize many prompts
- **users → prompt_usage**: A user can use many prompts
- **prompts → prompt_variables**: A prompt has many variables
- **prompts → prompt_dna**: A prompt has many DNA annotations
- **prompts → prompt_versions**: A prompt has version history
- **prompts → prompt_ratings**: A prompt receives many ratings
- **collections → collection_prompts**: A collection contains many prompts

### Many-to-Many
- **prompts ↔ collections**: Through `collection_prompts` junction table
  - Allows same prompt to be in multiple collections
  - Allows collection to have multiple prompts
  - Includes order for custom sorting

### Self-Referential
- **prompts → prompts**: Parent-child relationship for versioning/forking
  - `parent_id` references original prompt
  - Enables version tree navigation
  - `NULL` parent_id = original prompt

## Indexes Summary

### Primary Indexes
- All tables have UUID primary keys
- Composite unique constraints on junction tables

### Performance Indexes
- **Full-text search**: GIN index on `prompts.search_vector`
- **Tag search**: GIN index on `prompts.tags` (array)
- **Foreign keys**: All FK columns indexed for JOIN performance
- **Filtering**: Indexes on category, skill_level, status
- **Sorting**: Indexes on created_at, order columns
- **User queries**: Composite indexes on (user_id, timestamp)

### Partial Indexes
- `is_featured` index (WHERE is_featured = true)
- `is_public` index (WHERE is_public = true)

## Triggers & Automation

1. **Auto-update timestamps**: `updated_at` on users, prompts, collections, ratings
2. **Full-text search**: Auto-update `search_vector` when title/description/template/tags change
3. **Average rating**: Auto-calculate `prompts.avg_rating` when ratings added/updated/deleted

## Enums

- **category_type**: marketing, code, writing, research, personal, business, education, creative
- **skill_level_type**: beginner, intermediate, advanced, expert
- **ai_model_type**: gpt4, claude, gemini, llama, universal
- **prompt_status_type**: draft, published, archived, flagged

## Views

1. **prompts_with_author**: Prompts joined with author name/avatar
2. **popular_prompts**: Top prompts by usage in last 30 days

## Functions

1. **search_prompts()**: Full-text search with filters, pagination, ranking
2. **get_prompt_details()**: Fetch prompt + variables + DNA + author in one call
