-- Prompt Toolkit — Waitlist table
-- Captures email signups before beta launch

CREATE TABLE waitlist (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    email       TEXT        NOT NULL,
    source      TEXT        NOT NULL DEFAULT 'landing',   -- 'landing', 'hero', 'cta', 'blog'
    referrer    TEXT,                                     -- HTTP Referer header
    metadata    JSONB       NOT NULL DEFAULT '{}',        -- utm_source, utm_campaign, etc.
    confirmed   BOOLEAN     NOT NULL DEFAULT false,
    position    SERIAL      NOT NULL,                     -- signup order (for "you're #N")
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT waitlist_email_key UNIQUE (email)
);

-- Index for fast email lookups and ordered position queries
CREATE INDEX idx_waitlist_email     ON waitlist(email);
CREATE INDEX idx_waitlist_position  ON waitlist(position);
CREATE INDEX idx_waitlist_created   ON waitlist(created_at DESC);

-- Enable RLS (public insert for signups, admin-only read)
ALTER TABLE waitlist ENABLE ROW LEVEL SECURITY;

-- Anyone can sign up (insert their own email)
CREATE POLICY "waitlist: anyone can insert"
    ON waitlist FOR INSERT
    WITH CHECK (true);

-- No reads for anon/authenticated — only service role (admin) can read
-- This prevents scrapers from reading the full email list

COMMENT ON TABLE waitlist IS 'Pre-beta email waitlist. Position column tracks signup order for "you are #N" messaging.';
