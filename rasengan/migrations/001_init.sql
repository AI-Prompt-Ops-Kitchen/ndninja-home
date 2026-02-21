-- Rasengan — Event Hub schema
-- Run against: rasengan database

CREATE TABLE IF NOT EXISTS events (
    id          BIGSERIAL PRIMARY KEY,
    event_type  TEXT NOT NULL,
    source      TEXT NOT NULL,
    payload     JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_events_type ON events (event_type);
CREATE INDEX IF NOT EXISTS idx_events_source ON events (source);
CREATE INDEX IF NOT EXISTS idx_events_created ON events (created_at DESC);

CREATE TABLE IF NOT EXISTS context_snapshots (
    id          BIGSERIAL PRIMARY KEY,
    snapshot    JSONB NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
