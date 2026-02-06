-- scripts/context7/schema.sql
-- Context7 Proactive Retrieval Database Schema
-- Database: claude_memory

-- Main cache table
CREATE TABLE IF NOT EXISTS context7_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fingerprint VARCHAR(255) UNIQUE NOT NULL,
    library_id VARCHAR(255) NOT NULL,
    library_version VARCHAR(50) NOT NULL,
    query_intent VARCHAR(255) NOT NULL,
    content JSONB NOT NULL,
    citations JSONB,
    query_count INTEGER DEFAULT 1,
    last_accessed TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_context7_cache_fingerprint ON context7_cache(fingerprint);
CREATE INDEX IF NOT EXISTS idx_context7_cache_library ON context7_cache(library_id, library_version);
CREATE INDEX IF NOT EXISTS idx_context7_cache_accessed ON context7_cache(last_accessed DESC);

-- Project library tracking
CREATE TABLE IF NOT EXISTS context7_project_libraries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_path VARCHAR(500) NOT NULL,
    library_id VARCHAR(255) NOT NULL,
    library_version VARCHAR(50),
    detection_source VARCHAR(50),
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_path, library_id)
);

CREATE INDEX IF NOT EXISTS idx_context7_proj_libs_path ON context7_project_libraries(project_path);
CREATE INDEX IF NOT EXISTS idx_context7_proj_libs_used ON context7_project_libraries(last_used DESC);

-- Query history for analytics
CREATE TABLE IF NOT EXISTS context7_query_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fingerprint VARCHAR(255) NOT NULL,
    original_query TEXT,
    cache_hit BOOLEAN,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_context7_log_created ON context7_query_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_context7_log_hits ON context7_query_log(cache_hit);
