-- Migration: Standardize Action Item Schema
-- Version: 004
-- Date: 2026-01-11
-- Description: Add metadata fields to action_items for better tracking

-- Create a function to migrate action items to the enhanced schema
CREATE OR REPLACE FUNCTION migrate_action_item(item JSONB) RETURNS JSONB AS $$
BEGIN
    -- Add standard metadata fields if not present
    RETURN item ||
        jsonb_build_object(
            'started_at', COALESCE(item->>'started_at', NULL),
            'completed_at', COALESCE(item->>'completed_at', NULL),
            'last_mentioned', COALESCE(item->>'last_mentioned', NULL),
            'context_keywords', COALESCE(item->'context_keywords', '[]'::jsonb),
            'estimated_effort', COALESCE(item->>'estimated_effort', NULL),
            'source', COALESCE(item->>'source', 'conversation'),
            'version', 2
        );
END;
$$ LANGUAGE plpgsql;

-- Create a view that normalizes action items with metadata
CREATE OR REPLACE VIEW action_items_normalized AS
SELECT
    cs.id AS summary_id,
    cs.session_id,
    cs.app_source,
    cs.created_at AS session_date,
    ai.ordinal,
    COALESCE(ai.item->>'item', ai.item::text) AS item_text,
    COALESCE(ai.item->>'priority', 'medium') AS priority,
    COALESCE((ai.item->>'completed')::boolean, false) AS completed,
    (ai.item->>'started_at')::timestamptz AS started_at,
    (ai.item->>'completed_at')::timestamptz AS completed_at,
    (ai.item->>'last_mentioned')::timestamptz AS last_mentioned,
    COALESCE(ai.item->'context_keywords', '[]'::jsonb) AS context_keywords,
    ai.item->>'estimated_effort' AS estimated_effort,
    COALESCE(ai.item->>'source', 'conversation') AS source,
    COALESCE((ai.item->>'version')::int, 1) AS schema_version
FROM conversation_summaries cs
CROSS JOIN LATERAL jsonb_array_elements(COALESCE(cs.action_items, '[]'::jsonb))
    WITH ORDINALITY AS ai(item, ordinal)
WHERE jsonb_array_length(COALESCE(cs.action_items, '[]'::jsonb)) > 0;

-- Create a table to track action item events/progress
CREATE TABLE IF NOT EXISTS action_item_events (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    item_index INTEGER NOT NULL,
    event_type VARCHAR(32) NOT NULL,  -- 'created', 'started', 'mentioned', 'completed', 'blocked'
    detected_from VARCHAR(32),  -- 'manual', 'tool_use', 'conversation', 'auto'
    confidence VARCHAR(16),  -- 'high', 'medium', 'low'
    context_snippet TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_action_events_session ON action_item_events(session_id);
CREATE INDEX IF NOT EXISTS idx_action_events_type ON action_item_events(event_type);

-- Function to get pending action items (not completed, from recent sessions)
CREATE OR REPLACE FUNCTION get_pending_action_items(days_back INTEGER DEFAULT 7)
RETURNS TABLE (
    session_id VARCHAR(100),
    item_text TEXT,
    priority TEXT,
    session_date TIMESTAMPTZ,
    age_days INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ain.session_id,
        ain.item_text,
        ain.priority,
        ain.session_date,
        EXTRACT(DAY FROM NOW() - ain.session_date)::INTEGER AS age_days
    FROM action_items_normalized ain
    WHERE ain.completed = false
      AND ain.session_date >= NOW() - (days_back || ' days')::INTERVAL
    ORDER BY
        CASE ain.priority
            WHEN 'high' THEN 1
            WHEN 'medium' THEN 2
            WHEN 'low' THEN 3
            ELSE 4
        END,
        ain.session_date DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to update action item with metadata
CREATE OR REPLACE FUNCTION update_action_item_metadata(
    p_session_id VARCHAR(100),
    p_item_index INTEGER,
    p_field VARCHAR(32),
    p_value TEXT
) RETURNS BOOLEAN AS $$
DECLARE
    v_current_items JSONB;
    v_updated_item JSONB;
BEGIN
    -- Get current action items
    SELECT action_items INTO v_current_items
    FROM conversation_summaries
    WHERE session_id = p_session_id;

    IF v_current_items IS NULL OR jsonb_array_length(v_current_items) <= p_item_index THEN
        RETURN FALSE;
    END IF;

    -- Update the specific field
    v_updated_item = v_current_items->p_item_index || jsonb_build_object(p_field, p_value);

    -- Update the array
    v_current_items = jsonb_set(v_current_items, ARRAY[p_item_index::TEXT], v_updated_item);

    -- Save back
    UPDATE conversation_summaries
    SET action_items = v_current_items,
        updated_at = NOW()
    WHERE session_id = p_session_id;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Document the standardized schema
COMMENT ON VIEW action_items_normalized IS 'Normalized view of action items with metadata fields. Schema v2 adds: started_at, completed_at, last_mentioned, context_keywords, estimated_effort, source, version';

COMMENT ON FUNCTION update_action_item_metadata IS 'Update metadata field on an action item. Fields: started_at, completed_at, last_mentioned, estimated_effort, etc.';

-- Grant permissions
GRANT SELECT ON action_items_normalized TO ndninja;
GRANT EXECUTE ON FUNCTION get_pending_action_items TO ndninja;
GRANT EXECUTE ON FUNCTION update_action_item_metadata TO ndninja;
GRANT SELECT, INSERT ON action_item_events TO ndninja;
GRANT USAGE ON SEQUENCE action_item_events_id_seq TO ndninja;
