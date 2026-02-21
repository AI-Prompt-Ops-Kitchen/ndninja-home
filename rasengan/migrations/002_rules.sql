-- Rasengan Phase 2: Rules Engine
-- Declarative IFTTT-style rules that evaluate incoming events and fire actions.

CREATE TABLE rules (
    id               BIGSERIAL PRIMARY KEY,
    name             TEXT NOT NULL UNIQUE,
    event_type       TEXT NOT NULL,
    source           TEXT,
    condition        JSONB NOT NULL DEFAULT '{}',
    action           JSONB NOT NULL,
    enabled          BOOLEAN NOT NULL DEFAULT true,
    cooldown_seconds INT NOT NULL DEFAULT 0,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_rules_enabled ON rules (enabled) WHERE enabled = true;

CREATE TABLE rule_executions (
    id            BIGSERIAL PRIMARY KEY,
    rule_id       BIGINT NOT NULL REFERENCES rules(id) ON DELETE CASCADE,
    event_type    TEXT NOT NULL,
    event_payload JSONB NOT NULL DEFAULT '{}',
    action_result JSONB NOT NULL DEFAULT '{}',
    success       BOOLEAN NOT NULL DEFAULT true,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_rule_exec_rule ON rule_executions (rule_id);
CREATE INDEX idx_rule_exec_created ON rule_executions (created_at DESC);
