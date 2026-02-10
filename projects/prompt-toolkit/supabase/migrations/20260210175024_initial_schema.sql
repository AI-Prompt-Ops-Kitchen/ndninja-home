-- Prompt Toolkit SaaS - Database Schema
-- Phase 1: Database Schema & Data Foundation
-- Supports: Versioning, Attribution, Marketplace, Full-text Search

-- ============================================================================
-- EXTENSIONS
-- ============================================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable full-text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    avatar_url TEXT,
    bio TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Categories enum for prompts
CREATE TYPE category_type AS ENUM (
    'marketing',
    'code',
    'writing',
    'research',
    'personal',
    'business',
    'education',
    'creative'
);

-- Skill level enum
CREATE TYPE skill_level_type AS ENUM (
    'beginner',
    'intermediate',
    'advanced',
    'expert'
);

-- AI model compatibility enum
CREATE TYPE ai_model_type AS ENUM (
    'gpt4',
    'claude',
    'gemini',
    'llama',
    'universal'
);

-- Prompt status enum
CREATE TYPE prompt_status_type AS ENUM (
    'draft',
    'published',
    'archived',
    'flagged'
);

-- Prompts table (core entity)
CREATE TABLE prompts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Basic info
    title TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT NOT NULL,
    template TEXT NOT NULL,

    -- Categorization
    category category_type NOT NULL,
    skill_level skill_level_type NOT NULL DEFAULT 'beginner',
    ai_model ai_model_type NOT NULL DEFAULT 'universal',
    tags TEXT[] DEFAULT '{}',

    -- Attribution
    author_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Versioning
    version INTEGER NOT NULL DEFAULT 1,
    parent_id UUID REFERENCES prompts(id) ON DELETE SET NULL,

    -- Status
    status prompt_status_type NOT NULL DEFAULT 'published',
    is_featured BOOLEAN NOT NULL DEFAULT false,

    -- Metrics
    usage_count INTEGER NOT NULL DEFAULT 0,
    fork_count INTEGER NOT NULL DEFAULT 0,
    avg_rating DECIMAL(3,2),

    -- Full-text search
    search_vector TSVECTOR,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Prompt variables (dynamic form fields)
CREATE TABLE prompt_variables (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prompt_id UUID NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,

    -- Variable definition
    name TEXT NOT NULL,
    label TEXT NOT NULL,
    helper_text TEXT,
    placeholder TEXT,
    default_value TEXT,
    suggestions TEXT[], -- Array of suggested values

    -- Validation
    required BOOLEAN NOT NULL DEFAULT true,
    variable_type TEXT NOT NULL DEFAULT 'text', -- text, textarea, select, number
    max_length INTEGER,

    -- Display order
    "order" INTEGER NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Ensure unique variable names per prompt
    UNIQUE(prompt_id, name)
);

-- Prompt DNA (educational annotations)
CREATE TABLE prompt_dna (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prompt_id UUID NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,

    -- Component info
    component_type TEXT NOT NULL, -- e.g., 'persona', 'constraints', 'examples'
    highlight_start INTEGER NOT NULL,
    highlight_end INTEGER NOT NULL,

    -- Educational content
    explanation TEXT NOT NULL,
    why_it_works TEXT,

    -- Display order
    "order" INTEGER NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Collections (user-curated prompt lists)
CREATE TABLE collections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Collection info
    name TEXT NOT NULL,
    description TEXT,
    slug TEXT NOT NULL,

    -- Visibility
    is_public BOOLEAN NOT NULL DEFAULT false,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Ensure unique slugs per user
    UNIQUE(user_id, slug)
);

-- Collection-Prompt junction table
CREATE TABLE collection_prompts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    collection_id UUID NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    prompt_id UUID NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,

    -- Display order in collection
    "order" INTEGER NOT NULL DEFAULT 0,

    -- Added timestamp
    added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Prevent duplicate prompts in same collection
    UNIQUE(collection_id, prompt_id)
);

-- Prompt versions (version history)
CREATE TABLE prompt_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prompt_id UUID NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,

    -- Version details
    version_number INTEGER NOT NULL,
    template TEXT NOT NULL,
    variables_schema JSONB, -- Snapshot of variables at this version
    change_summary TEXT NOT NULL,

    -- Attribution
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Ensure unique version numbers per prompt
    UNIQUE(prompt_id, version_number)
);

-- Prompt ratings
CREATE TABLE prompt_ratings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prompt_id UUID NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Rating data
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- One rating per user per prompt
    UNIQUE(prompt_id, user_id)
);

-- User customizations (saved/forked prompts)
CREATE TABLE user_customizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    prompt_id UUID NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,

    -- Customized content
    customized_template TEXT NOT NULL,
    variables_json JSONB, -- User's filled variable values
    custom_notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Prompt usage tracking
CREATE TABLE prompt_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    prompt_id UUID NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,

    -- Usage metadata
    used_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Optional: track which platform
    platform TEXT, -- 'chatgpt', 'claude', 'gemini', etc.

    -- Optional: track success
    was_helpful BOOLEAN
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Users indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at DESC);

-- Prompts indexes
CREATE INDEX idx_prompts_author_id ON prompts(author_id);
CREATE INDEX idx_prompts_category ON prompts(category);
CREATE INDEX idx_prompts_skill_level ON prompts(skill_level);
CREATE INDEX idx_prompts_status ON prompts(status);
CREATE INDEX idx_prompts_parent_id ON prompts(parent_id);
CREATE INDEX idx_prompts_slug ON prompts(slug);
CREATE INDEX idx_prompts_created_at ON prompts(created_at DESC);
CREATE INDEX idx_prompts_featured ON prompts(is_featured) WHERE is_featured = true;
CREATE INDEX idx_prompts_tags ON prompts USING GIN(tags);

-- Full-text search index
CREATE INDEX idx_prompts_search_vector ON prompts USING GIN(search_vector);

-- Prompt variables indexes
CREATE INDEX idx_prompt_variables_prompt_id ON prompt_variables(prompt_id);
CREATE INDEX idx_prompt_variables_order ON prompt_variables(prompt_id, "order");

-- Prompt DNA indexes
CREATE INDEX idx_prompt_dna_prompt_id ON prompt_dna(prompt_id);
CREATE INDEX idx_prompt_dna_order ON prompt_dna(prompt_id, "order");

-- Collections indexes
CREATE INDEX idx_collections_user_id ON collections(user_id);
CREATE INDEX idx_collections_is_public ON collections(is_public) WHERE is_public = true;
CREATE INDEX idx_collections_slug ON collections(user_id, slug);

-- Collection prompts indexes
CREATE INDEX idx_collection_prompts_collection_id ON collection_prompts(collection_id);
CREATE INDEX idx_collection_prompts_prompt_id ON collection_prompts(prompt_id);
CREATE INDEX idx_collection_prompts_order ON collection_prompts(collection_id, "order");

-- Prompt versions indexes
CREATE INDEX idx_prompt_versions_prompt_id ON prompt_versions(prompt_id);
CREATE INDEX idx_prompt_versions_created_at ON prompt_versions(prompt_id, created_at DESC);

-- Prompt ratings indexes
CREATE INDEX idx_prompt_ratings_prompt_id ON prompt_ratings(prompt_id);
CREATE INDEX idx_prompt_ratings_user_id ON prompt_ratings(user_id);
CREATE INDEX idx_prompt_ratings_rating ON prompt_ratings(prompt_id, rating);

-- User customizations indexes
CREATE INDEX idx_user_customizations_user_id ON user_customizations(user_id);
CREATE INDEX idx_user_customizations_prompt_id ON user_customizations(prompt_id);

-- Prompt usage indexes
CREATE INDEX idx_prompt_usage_user_id ON prompt_usage(user_id, used_at DESC);
CREATE INDEX idx_prompt_usage_prompt_id ON prompt_usage(prompt_id, used_at DESC);
CREATE INDEX idx_prompt_usage_platform ON prompt_usage(platform);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_prompts_updated_at
    BEFORE UPDATE ON prompts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_collections_updated_at
    BEFORE UPDATE ON collections
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_prompt_ratings_updated_at
    BEFORE UPDATE ON prompt_ratings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_customizations_updated_at
    BEFORE UPDATE ON user_customizations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Auto-update search_vector on prompts
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

CREATE TRIGGER update_prompts_search_vector_trigger
    BEFORE INSERT OR UPDATE OF title, description, template, tags
    ON prompts
    FOR EACH ROW
    EXECUTE FUNCTION update_prompts_search_vector();

-- Auto-update prompt avg_rating when rating added/updated/deleted
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

CREATE TRIGGER update_prompt_avg_rating_on_insert
    AFTER INSERT ON prompt_ratings
    FOR EACH ROW
    EXECUTE FUNCTION update_prompt_avg_rating();

CREATE TRIGGER update_prompt_avg_rating_on_update
    AFTER UPDATE OF rating ON prompt_ratings
    FOR EACH ROW
    EXECUTE FUNCTION update_prompt_avg_rating();

CREATE TRIGGER update_prompt_avg_rating_on_delete
    AFTER DELETE ON prompt_ratings
    FOR EACH ROW
    EXECUTE FUNCTION update_prompt_avg_rating();

-- ============================================================================
-- VIEWS (Helpful for common queries)
-- ============================================================================

-- View: Prompts with author info
CREATE OR REPLACE VIEW prompts_with_author AS
SELECT
    p.*,
    u.name AS author_name,
    u.avatar_url AS author_avatar
FROM prompts p
JOIN users u ON p.author_id = u.id;

-- View: Popular prompts (most used in last 30 days)
CREATE OR REPLACE VIEW popular_prompts AS
SELECT
    p.id,
    p.title,
    p.slug,
    p.category,
    p.avg_rating,
    COUNT(pu.id) AS recent_usage_count
FROM prompts p
LEFT JOIN prompt_usage pu ON p.id = pu.prompt_id
    AND pu.used_at >= NOW() - INTERVAL '30 days'
WHERE p.status = 'published'
GROUP BY p.id
ORDER BY recent_usage_count DESC;

-- ============================================================================
-- FUNCTIONS (Helpful utilities)
-- ============================================================================

-- Function: Search prompts with full-text search
CREATE OR REPLACE FUNCTION search_prompts(
    search_query TEXT,
    category_filter category_type DEFAULT NULL,
    skill_filter skill_level_type DEFAULT NULL,
    limit_count INTEGER DEFAULT 20,
    offset_count INTEGER DEFAULT 0
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    slug TEXT,
    description TEXT,
    category category_type,
    skill_level skill_level_type,
    avg_rating DECIMAL(3,2),
    usage_count INTEGER,
    rank REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id,
        p.title,
        p.slug,
        p.description,
        p.category,
        p.skill_level,
        p.avg_rating,
        p.usage_count,
        ts_rank(p.search_vector, plainto_tsquery('english', search_query)) AS rank
    FROM prompts p
    WHERE
        p.status = 'published'
        AND p.search_vector @@ plainto_tsquery('english', search_query)
        AND (category_filter IS NULL OR p.category = category_filter)
        AND (skill_filter IS NULL OR p.skill_level = skill_filter)
    ORDER BY rank DESC, p.avg_rating DESC NULLS LAST
    LIMIT limit_count
    OFFSET offset_count;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function: Get prompt with all related data
CREATE OR REPLACE FUNCTION get_prompt_details(prompt_slug TEXT)
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'prompt', (
            SELECT row_to_json(p.*)
            FROM prompts p
            WHERE p.slug = prompt_slug
        ),
        'variables', (
            SELECT COALESCE(json_agg(row_to_json(pv.*) ORDER BY pv."order"), '[]'::json)
            FROM prompt_variables pv
            JOIN prompts p ON pv.prompt_id = p.id
            WHERE p.slug = prompt_slug
        ),
        'dna', (
            SELECT COALESCE(json_agg(row_to_json(pd.*) ORDER BY pd."order"), '[]'::json)
            FROM prompt_dna pd
            JOIN prompts p ON pd.prompt_id = p.id
            WHERE p.slug = prompt_slug
        ),
        'author', (
            SELECT row_to_json(u.*)
            FROM prompts p
            JOIN users u ON p.author_id = u.id
            WHERE p.slug = prompt_slug
        )
    ) INTO result;

    RETURN result;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- COMMENTS (Documentation)
-- ============================================================================

COMMENT ON TABLE prompts IS 'Core prompt templates with versioning and attribution support';
COMMENT ON COLUMN prompts.parent_id IS 'References original prompt if this is a fork/version';
COMMENT ON COLUMN prompts.version IS 'Version number for this prompt (auto-incremented for forks)';
COMMENT ON COLUMN prompts.search_vector IS 'Full-text search vector (auto-updated by trigger)';

COMMENT ON TABLE prompt_variables IS 'Dynamic form fields for prompt customization';
COMMENT ON TABLE prompt_dna IS 'Educational annotations explaining prompt components';
COMMENT ON TABLE collections IS 'User-curated lists of prompts';
COMMENT ON TABLE prompt_versions IS 'Version history for prompts (audit trail)';
COMMENT ON TABLE prompt_ratings IS 'User ratings for prompts (1-5 stars)';
COMMENT ON TABLE user_customizations IS 'User-specific modifications to prompts';
COMMENT ON TABLE prompt_usage IS 'Usage tracking for analytics and recommendations';
