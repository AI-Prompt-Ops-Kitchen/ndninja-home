-- ============================================================
-- Prompt Toolkit SaaS — Database Schema
-- PostgreSQL 15+ / Supabase compatible
-- ============================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";    -- Fuzzy text search

-- ============================================================
-- ENUMS
-- ============================================================

CREATE TYPE user_role AS ENUM ('free', 'pro', 'admin');
CREATE TYPE difficulty_level AS ENUM ('beginner', 'intermediate', 'advanced', 'expert');
CREATE TYPE prompt_status AS ENUM ('draft', 'published', 'archived', 'pending_review');

-- ============================================================
-- USERS
-- ============================================================

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           TEXT UNIQUE NOT NULL,
    display_name    TEXT,
    avatar_url      TEXT,
    bio             TEXT,
    role            user_role DEFAULT 'free',
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    subscription_status TEXT DEFAULT 'inactive',
    daily_copies    INT DEFAULT 0,
    daily_copies_reset_at TIMESTAMPTZ DEFAULT NOW(),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_stripe ON users(stripe_customer_id);

-- ============================================================
-- CATEGORIES
-- ============================================================

CREATE TABLE categories (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        TEXT NOT NULL,
    slug        TEXT UNIQUE NOT NULL,
    description TEXT,
    icon        TEXT,                         -- emoji or icon name
    color       TEXT,                         -- hex color for UI
    parent_id   UUID REFERENCES categories(id) ON DELETE SET NULL,
    sort_order  INT DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_categories_slug ON categories(slug);
CREATE INDEX idx_categories_parent ON categories(parent_id);

-- ============================================================
-- TAGS
-- ============================================================

CREATE TABLE tags (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        TEXT UNIQUE NOT NULL,
    slug        TEXT UNIQUE NOT NULL,
    color       TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_tags_slug ON tags(slug);

-- ============================================================
-- PROMPTS
-- ============================================================

CREATE TABLE prompts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title           TEXT NOT NULL,
    slug            TEXT UNIQUE NOT NULL,
    description     TEXT,
    content         TEXT NOT NULL,               -- The actual prompt text
    system_prompt   TEXT,                        -- Optional system prompt
    example_output  TEXT,                        -- Example of what the prompt produces
    use_case        TEXT,                        -- When to use this prompt
    variables       JSONB DEFAULT '[]'::jsonb,   -- Template variables [{name, description, default}]
    difficulty      difficulty_level DEFAULT 'intermediate',
    ai_model_tags   TEXT[] DEFAULT '{}',         -- ['gpt-4', 'claude', 'gemini']
    category_id     UUID REFERENCES categories(id) ON DELETE SET NULL,
    author_id       UUID REFERENCES users(id) ON DELETE SET NULL,
    status          prompt_status DEFAULT 'published',
    is_public       BOOLEAN DEFAULT true,
    is_featured     BOOLEAN DEFAULT false,
    is_pro_only     BOOLEAN DEFAULT false,
    version         INT DEFAULT 1,
    fork_of         UUID REFERENCES prompts(id) ON DELETE SET NULL,
    
    -- Denormalized counters (updated via triggers)
    copy_count      INT DEFAULT 0,
    favorite_count  INT DEFAULT 0,
    rating_avg      DECIMAL(3,2) DEFAULT 0.00,
    rating_count    INT DEFAULT 0,
    view_count      INT DEFAULT 0,
    
    -- Full-text search
    search_vector   TSVECTOR,
    
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_prompts_slug ON prompts(slug);
CREATE INDEX idx_prompts_category ON prompts(category_id);
CREATE INDEX idx_prompts_author ON prompts(author_id);
CREATE INDEX idx_prompts_status ON prompts(status) WHERE status = 'published';
CREATE INDEX idx_prompts_featured ON prompts(is_featured) WHERE is_featured = true;
CREATE INDEX idx_prompts_search ON prompts USING GIN(search_vector);
CREATE INDEX idx_prompts_model_tags ON prompts USING GIN(ai_model_tags);
CREATE INDEX idx_prompts_created ON prompts(created_at DESC);
CREATE INDEX idx_prompts_popular ON prompts(copy_count DESC, favorite_count DESC);

-- Auto-update search vector
CREATE OR REPLACE FUNCTION prompts_search_vector_update() RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.content, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(NEW.use_case, '')), 'D');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_prompts_search_vector
    BEFORE INSERT OR UPDATE OF title, description, content, use_case
    ON prompts
    FOR EACH ROW
    EXECUTE FUNCTION prompts_search_vector_update();

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_prompts_updated_at
    BEFORE UPDATE ON prompts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- PROMPT ↔ TAG (many-to-many)
-- ============================================================

CREATE TABLE prompt_tags (
    prompt_id   UUID REFERENCES prompts(id) ON DELETE CASCADE,
    tag_id      UUID REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (prompt_id, tag_id)
);

CREATE INDEX idx_prompt_tags_tag ON prompt_tags(tag_id);

-- ============================================================
-- FAVORITES
-- ============================================================

CREATE TABLE favorites (
    user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
    prompt_id   UUID REFERENCES prompts(id) ON DELETE CASCADE,
    folder      TEXT DEFAULT 'default',       -- User-defined collections
    note        TEXT,                         -- Personal note
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, prompt_id)
);

CREATE INDEX idx_favorites_user ON favorites(user_id);
CREATE INDEX idx_favorites_prompt ON favorites(prompt_id);

-- Trigger to update denormalized count
CREATE OR REPLACE FUNCTION update_favorite_count() RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE prompts SET favorite_count = favorite_count + 1 WHERE id = NEW.prompt_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE prompts SET favorite_count = favorite_count - 1 WHERE id = OLD.prompt_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_favorites_count
    AFTER INSERT OR DELETE ON favorites
    FOR EACH ROW
    EXECUTE FUNCTION update_favorite_count();

-- ============================================================
-- RATINGS
-- ============================================================

CREATE TABLE ratings (
    user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
    prompt_id   UUID REFERENCES prompts(id) ON DELETE CASCADE,
    score       INT NOT NULL CHECK (score >= 1 AND score <= 5),
    review      TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, prompt_id)
);

CREATE INDEX idx_ratings_prompt ON ratings(prompt_id);

-- Trigger to update denormalized rating
CREATE OR REPLACE FUNCTION update_rating_stats() RETURNS TRIGGER AS $$
BEGIN
    UPDATE prompts SET 
        rating_avg = (SELECT AVG(score) FROM ratings WHERE prompt_id = COALESCE(NEW.prompt_id, OLD.prompt_id)),
        rating_count = (SELECT COUNT(*) FROM ratings WHERE prompt_id = COALESCE(NEW.prompt_id, OLD.prompt_id))
    WHERE id = COALESCE(NEW.prompt_id, OLD.prompt_id);
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_ratings_stats
    AFTER INSERT OR UPDATE OR DELETE ON ratings
    FOR EACH ROW
    EXECUTE FUNCTION update_rating_stats();

-- ============================================================
-- USAGE LOGS (analytics)
-- ============================================================

CREATE TABLE usage_logs (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID REFERENCES users(id) ON DELETE SET NULL,
    prompt_id   UUID REFERENCES prompts(id) ON DELETE SET NULL,
    action      TEXT NOT NULL,                -- 'view', 'copy', 'fork', 'share', 'search'
    metadata    JSONB DEFAULT '{}'::jsonb,    -- Extra context (search query, referrer, etc.)
    ip_address  INET,
    user_agent  TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_usage_user ON usage_logs(user_id);
CREATE INDEX idx_usage_prompt ON usage_logs(prompt_id);
CREATE INDEX idx_usage_action ON usage_logs(action);
CREATE INDEX idx_usage_created ON usage_logs(created_at DESC);

-- Partition by month for performance at scale (optional)
-- CREATE TABLE usage_logs_2025_01 PARTITION OF usage_logs
--     FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

-- ============================================================
-- ROW LEVEL SECURITY (Supabase)
-- ============================================================

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE prompts ENABLE ROW LEVEL SECURITY;
ALTER TABLE favorites ENABLE ROW LEVEL SECURITY;
ALTER TABLE ratings ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE tags ENABLE ROW LEVEL SECURITY;

-- Public read for published prompts
CREATE POLICY "Public prompts are viewable by everyone"
    ON prompts FOR SELECT
    USING (status = 'published' AND is_public = true);

-- Authors can see their own drafts
CREATE POLICY "Users can view own prompts"
    ON prompts FOR SELECT
    USING (author_id = auth.uid());

-- Authors can insert their own prompts
CREATE POLICY "Users can create prompts"
    ON prompts FOR INSERT
    WITH CHECK (author_id = auth.uid());

-- Authors can update their own prompts
CREATE POLICY "Users can update own prompts"
    ON prompts FOR UPDATE
    USING (author_id = auth.uid());

-- Users manage their own favorites
CREATE POLICY "Users manage own favorites"
    ON favorites FOR ALL
    USING (user_id = auth.uid());

-- Users manage their own ratings
CREATE POLICY "Users manage own ratings"
    ON ratings FOR ALL
    USING (user_id = auth.uid());

-- Public read for ratings (to show reviews)
CREATE POLICY "Ratings are viewable by everyone"
    ON ratings FOR SELECT
    USING (true);

-- Categories and tags are public read
CREATE POLICY "Categories are public"
    ON categories FOR SELECT
    USING (true);

CREATE POLICY "Tags are public"
    ON tags FOR SELECT
    USING (true);

-- Users can see their own profile
CREATE POLICY "Users can view own profile"
    ON users FOR SELECT
    USING (id = auth.uid());

-- Users can update their own profile
CREATE POLICY "Users can update own profile"
    ON users FOR UPDATE
    USING (id = auth.uid());

-- Usage logs: users can insert, only see their own
CREATE POLICY "Users can log usage"
    ON usage_logs FOR INSERT
    WITH CHECK (user_id = auth.uid() OR user_id IS NULL);

CREATE POLICY "Users can view own usage"
    ON usage_logs FOR SELECT
    USING (user_id = auth.uid());

-- ============================================================
-- SEED DATA: Default Categories
-- ============================================================

INSERT INTO categories (name, slug, description, icon, sort_order) VALUES
    ('Writing & Content',    'writing',      'Blog posts, articles, copywriting',         '✍️', 1),
    ('Code & Development',   'code',         'Programming, debugging, code review',       '💻', 2),
    ('Business & Strategy',  'business',     'Planning, analysis, decision-making',       '📊', 3),
    ('Creative & Design',    'creative',     'Art direction, brainstorming, ideation',     '🎨', 4),
    ('Education & Learning', 'education',    'Teaching, studying, explanations',           '📚', 5),
    ('Data & Analysis',      'data',         'Data processing, insights, reporting',       '📈', 6),
    ('Marketing & Sales',    'marketing',    'Campaigns, funnels, persuasion',            '📣', 7),
    ('Productivity',         'productivity', 'Workflows, automation, organization',        '⚡', 8),
    ('Communication',        'communication','Emails, messages, presentations',            '💬', 9),
    ('AI & Meta-Prompting',  'meta',         'Prompts about prompting, system design',     '🧠', 10);

INSERT INTO tags (name, slug, color) VALUES
    ('ChatGPT',     'chatgpt',     '#10a37f'),
    ('Claude',      'claude',      '#d4a574'),
    ('Gemini',      'gemini',      '#4285f4'),
    ('Midjourney',  'midjourney',  '#000000'),
    ('Chain-of-Thought', 'cot',   '#ff6b6b'),
    ('Few-Shot',    'few-shot',    '#4ecdc4'),
    ('Zero-Shot',   'zero-shot',   '#45b7d1'),
    ('System Prompt','system',     '#96ceb4'),
    ('Template',    'template',    '#ffeaa7'),
    ('Framework',   'framework',   '#dfe6e9');
