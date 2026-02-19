-- Prompt Toolkit SaaS - Row Level Security Policies
-- Phase 1: Security Foundation
-- auth.uid() = the currently authenticated user's UUID (from Supabase Auth)
-- users.id is expected to mirror auth.users.id (set up via trigger or auth hook)

-- ============================================================================
-- ENABLE RLS ON ALL TABLES
-- ============================================================================

ALTER TABLE users               ENABLE ROW LEVEL SECURITY;
ALTER TABLE prompts             ENABLE ROW LEVEL SECURITY;
ALTER TABLE prompt_variables    ENABLE ROW LEVEL SECURITY;
ALTER TABLE prompt_dna          ENABLE ROW LEVEL SECURITY;
ALTER TABLE collections         ENABLE ROW LEVEL SECURITY;
ALTER TABLE collection_prompts  ENABLE ROW LEVEL SECURITY;
ALTER TABLE prompt_versions     ENABLE ROW LEVEL SECURITY;
ALTER TABLE prompt_ratings      ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_customizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE prompt_usage        ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- HELPER: is_prompt_visible(prompt_id)
-- Returns true if the prompt is published OR the caller is the author.
-- Used across multiple tables to avoid repeating the join.
-- ============================================================================

CREATE OR REPLACE FUNCTION is_prompt_visible(p_prompt_id UUID)
RETURNS BOOLEAN
LANGUAGE sql STABLE SECURITY DEFINER AS $$
    SELECT EXISTS (
        SELECT 1 FROM prompts
        WHERE id = p_prompt_id
          AND (status = 'published' OR author_id = auth.uid())
    );
$$;

-- ============================================================================
-- USERS
-- ============================================================================

-- Anyone can read public user profiles (needed for author attribution).
CREATE POLICY "users: anyone can read"
    ON users FOR SELECT
    USING (true);

-- Only the user themselves can update their own profile.
CREATE POLICY "users: owner can update"
    ON users FOR UPDATE
    USING (id = auth.uid())
    WITH CHECK (id = auth.uid());

-- New users are inserted via Supabase Auth trigger (service role bypasses RLS).
-- Authenticated users can insert their own row (for signup flows that do it manually).
CREATE POLICY "users: owner can insert"
    ON users FOR INSERT
    WITH CHECK (id = auth.uid());

-- Users can delete their own account.
CREATE POLICY "users: owner can delete"
    ON users FOR DELETE
    USING (id = auth.uid());

-- ============================================================================
-- PROMPTS
-- ============================================================================

-- Published prompts are readable by everyone.
-- Authors can always read their own prompts (any status).
CREATE POLICY "prompts: published are public"
    ON prompts FOR SELECT
    USING (status = 'published' OR author_id = auth.uid());

-- Authenticated users can create prompts (author_id must be their own).
CREATE POLICY "prompts: authenticated can insert"
    ON prompts FOR INSERT
    WITH CHECK (author_id = auth.uid());

-- Only the author can update their own prompts.
CREATE POLICY "prompts: author can update"
    ON prompts FOR UPDATE
    USING (author_id = auth.uid())
    WITH CHECK (author_id = auth.uid());

-- Only the author can delete their own prompts.
CREATE POLICY "prompts: author can delete"
    ON prompts FOR DELETE
    USING (author_id = auth.uid());

-- ============================================================================
-- PROMPT VARIABLES
-- (visibility follows the parent prompt)
-- ============================================================================

CREATE POLICY "prompt_variables: visible if prompt visible"
    ON prompt_variables FOR SELECT
    USING (is_prompt_visible(prompt_id));

-- Only the prompt author can manage variables.
CREATE POLICY "prompt_variables: author can insert"
    ON prompt_variables FOR INSERT
    WITH CHECK (
        EXISTS (SELECT 1 FROM prompts WHERE id = prompt_id AND author_id = auth.uid())
    );

CREATE POLICY "prompt_variables: author can update"
    ON prompt_variables FOR UPDATE
    USING (
        EXISTS (SELECT 1 FROM prompts WHERE id = prompt_id AND author_id = auth.uid())
    );

CREATE POLICY "prompt_variables: author can delete"
    ON prompt_variables FOR DELETE
    USING (
        EXISTS (SELECT 1 FROM prompts WHERE id = prompt_id AND author_id = auth.uid())
    );

-- ============================================================================
-- PROMPT DNA
-- (educational annotations — same rules as prompt_variables)
-- ============================================================================

CREATE POLICY "prompt_dna: visible if prompt visible"
    ON prompt_dna FOR SELECT
    USING (is_prompt_visible(prompt_id));

CREATE POLICY "prompt_dna: author can insert"
    ON prompt_dna FOR INSERT
    WITH CHECK (
        EXISTS (SELECT 1 FROM prompts WHERE id = prompt_id AND author_id = auth.uid())
    );

CREATE POLICY "prompt_dna: author can update"
    ON prompt_dna FOR UPDATE
    USING (
        EXISTS (SELECT 1 FROM prompts WHERE id = prompt_id AND author_id = auth.uid())
    );

CREATE POLICY "prompt_dna: author can delete"
    ON prompt_dna FOR DELETE
    USING (
        EXISTS (SELECT 1 FROM prompts WHERE id = prompt_id AND author_id = auth.uid())
    );

-- ============================================================================
-- COLLECTIONS
-- ============================================================================

-- Public collections are readable by everyone; private only by owner.
CREATE POLICY "collections: public or owner can read"
    ON collections FOR SELECT
    USING (is_public = true OR user_id = auth.uid());

-- Authenticated users can create their own collections.
CREATE POLICY "collections: owner can insert"
    ON collections FOR INSERT
    WITH CHECK (user_id = auth.uid());

-- Only the owner can update.
CREATE POLICY "collections: owner can update"
    ON collections FOR UPDATE
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- Only the owner can delete.
CREATE POLICY "collections: owner can delete"
    ON collections FOR DELETE
    USING (user_id = auth.uid());

-- ============================================================================
-- COLLECTION PROMPTS
-- ============================================================================

-- Readable if the parent collection is readable.
CREATE POLICY "collection_prompts: visible if collection visible"
    ON collection_prompts FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM collections
            WHERE id = collection_id
              AND (is_public = true OR user_id = auth.uid())
        )
    );

-- Only the collection owner can add prompts.
CREATE POLICY "collection_prompts: collection owner can insert"
    ON collection_prompts FOR INSERT
    WITH CHECK (
        EXISTS (SELECT 1 FROM collections WHERE id = collection_id AND user_id = auth.uid())
    );

-- Only the collection owner can reorder.
CREATE POLICY "collection_prompts: collection owner can update"
    ON collection_prompts FOR UPDATE
    USING (
        EXISTS (SELECT 1 FROM collections WHERE id = collection_id AND user_id = auth.uid())
    );

-- Only the collection owner can remove prompts.
CREATE POLICY "collection_prompts: collection owner can delete"
    ON collection_prompts FOR DELETE
    USING (
        EXISTS (SELECT 1 FROM collections WHERE id = collection_id AND user_id = auth.uid())
    );

-- ============================================================================
-- PROMPT VERSIONS
-- ============================================================================

-- Readable if the parent prompt is visible.
CREATE POLICY "prompt_versions: visible if prompt visible"
    ON prompt_versions FOR SELECT
    USING (is_prompt_visible(prompt_id));

-- Only the prompt author can create versions.
CREATE POLICY "prompt_versions: author can insert"
    ON prompt_versions FOR INSERT
    WITH CHECK (
        EXISTS (SELECT 1 FROM prompts WHERE id = prompt_id AND author_id = auth.uid())
        AND created_by = auth.uid()
    );

-- Version history is immutable — no updates or deletes.

-- ============================================================================
-- PROMPT RATINGS
-- ============================================================================

-- Anyone can read ratings (public signal of quality).
CREATE POLICY "prompt_ratings: anyone can read"
    ON prompt_ratings FOR SELECT
    USING (true);

-- Authenticated users can rate published prompts (but not their own).
CREATE POLICY "prompt_ratings: authenticated can insert"
    ON prompt_ratings FOR INSERT
    WITH CHECK (
        user_id = auth.uid()
        AND EXISTS (
            SELECT 1 FROM prompts
            WHERE id = prompt_id
              AND status = 'published'
              AND author_id != auth.uid()
        )
    );

-- Users can update their own rating.
CREATE POLICY "prompt_ratings: owner can update"
    ON prompt_ratings FOR UPDATE
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- Users can retract their own rating.
CREATE POLICY "prompt_ratings: owner can delete"
    ON prompt_ratings FOR DELETE
    USING (user_id = auth.uid());

-- ============================================================================
-- USER CUSTOMIZATIONS
-- (private — only the user can see/edit their own saved work)
-- ============================================================================

CREATE POLICY "user_customizations: owner only"
    ON user_customizations FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "user_customizations: owner can insert"
    ON user_customizations FOR INSERT
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "user_customizations: owner can update"
    ON user_customizations FOR UPDATE
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "user_customizations: owner can delete"
    ON user_customizations FOR DELETE
    USING (user_id = auth.uid());

-- ============================================================================
-- PROMPT USAGE
-- (private — only the user can see their own history; inserts are self-only)
-- ============================================================================

CREATE POLICY "prompt_usage: owner can read"
    ON prompt_usage FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "prompt_usage: owner can insert"
    ON prompt_usage FOR INSERT
    WITH CHECK (user_id = auth.uid());

-- Usage records are append-only (no update or delete to preserve analytics integrity).

-- ============================================================================
-- VIEWS — RE-GRANT after RLS
-- Supabase views run as the query user by default, so RLS applies automatically.
-- No additional grants needed for `prompts_with_author` or `popular_prompts`.
-- ============================================================================

-- ============================================================================
-- SERVICE ROLE NOTE
-- The Supabase service_role key bypasses RLS entirely.
-- Use it only in server-side admin operations (e.g. seed scripts, admin API).
-- The anon and authenticated keys respect all policies above.
-- ============================================================================
