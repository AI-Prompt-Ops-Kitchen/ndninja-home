-- Migration: Create skill_reflections table
-- Purpose: Track reflection history for self-improving skills
-- Created: 2026-01-05

CREATE TABLE IF NOT EXISTS skill_reflections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_name TEXT NOT NULL,
    source_session TEXT NOT NULL,
    signal_type TEXT NOT NULL CHECK (signal_type IN ('correction', 'pattern', 'preference')),
    signal_text TEXT NOT NULL,
    confidence TEXT NOT NULL CHECK (confidence IN ('high', 'medium', 'low')),
    what_changed TEXT NOT NULL,
    file_diff TEXT,
    git_commit TEXT,
    applied_at TIMESTAMP DEFAULT NOW(),
    reviewed_by TEXT,
    effectiveness_score INTEGER CHECK (effectiveness_score >= 1 AND effectiveness_score <= 5)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_skill_reflections_skill
    ON skill_reflections(skill_name);

CREATE INDEX IF NOT EXISTS idx_skill_reflections_session
    ON skill_reflections(source_session);

CREATE INDEX IF NOT EXISTS idx_skill_reflections_applied
    ON skill_reflections(applied_at DESC);

CREATE INDEX IF NOT EXISTS idx_skill_reflections_confidence
    ON skill_reflections(confidence);

-- Comments for documentation
COMMENT ON TABLE skill_reflections IS
    'Tracks reflection updates to skills based on conversation corrections';

COMMENT ON COLUMN skill_reflections.signal_type IS
    'Type of signal: correction (explicit fix), pattern (repeated behavior), preference (user choice)';

COMMENT ON COLUMN skill_reflections.confidence IS
    'Confidence level: high (explicit/repeated 2+), medium (single mention), low (implied)';

COMMENT ON COLUMN skill_reflections.reviewed_by IS
    'NULL for auto-applied, ''user'' for manual approval';

COMMENT ON COLUMN skill_reflections.effectiveness_score IS
    'User feedback rating 1-5, NULL if not rated';
