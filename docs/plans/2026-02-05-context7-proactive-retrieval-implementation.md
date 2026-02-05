# Context7 Proactive Retrieval Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build intelligent documentation caching with Redis+PostgreSQL, proactive preloading via SessionStart hook, and usage-based learning to eliminate redundant Context7 API calls.

**Architecture:** Two-tier cache (Redis hot + PostgreSQL persistent), hybrid detection (manifest parsing + usage tracking), SessionStart hook for preloading, `/load-docs` skill for manual loading.

**Tech Stack:** Python 3, PostgreSQL (claude_memory DB), Redis, Context7 MCP plugin

---

## Phase 1: Foundation & Database Setup

### Task 1: Database Schema Creation

**Files:**
- Create: `scripts/context7/schema.sql`
- Create: `scripts/context7/test_schema.py`

**Step 1: Write schema validation test**

```python
# scripts/context7/test_schema.py
import psycopg2
import pytest

def test_context7_tables_exist():
    """Verify all Context7 tables exist with correct structure."""
    conn = psycopg2.connect(
        host="localhost",
        database="claude_memory",
        user="claude_mcp",
        password="REDACTED"
    )
    cur = conn.cursor()

    # Check context7_cache table
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'context7_cache'
        ORDER BY ordinal_position;
    """)
    columns = cur.fetchall()

    expected_columns = [
        ('id', 'uuid'),
        ('fingerprint', 'character varying'),
        ('library_id', 'character varying'),
        ('library_version', 'character varying'),
        ('query_intent', 'character varying'),
        ('content', 'jsonb'),
        ('citations', 'jsonb'),
        ('query_count', 'integer'),
        ('last_accessed', 'timestamp without time zone'),
        ('created_at', 'timestamp without time zone')
    ]

    assert len(columns) == len(expected_columns), f"Expected {len(expected_columns)} columns, got {len(columns)}"

    # Check unique constraint on fingerprint
    cur.execute("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = 'context7_cache' AND constraint_type = 'UNIQUE';
    """)
    constraints = cur.fetchall()
    assert len(constraints) > 0, "Missing UNIQUE constraint on fingerprint"

    conn.close()
```

**Step 2: Run test to verify it fails**

```bash
cd /home/ndninja/.worktrees/context7-proactive
pytest scripts/context7/test_schema.py::test_context7_tables_exist -v
```

Expected: FAIL - table does not exist

**Step 3: Create database schema**

```sql
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
```

**Step 4: Apply schema to database**

```bash
PGPASSWORD=REDACTED psql -U claude_mcp -h localhost -d claude_memory -f scripts/context7/schema.sql
```

Expected: CREATE TABLE (x3), CREATE INDEX (x7)

**Step 5: Run test to verify it passes**

```bash
pytest scripts/context7/test_schema.py::test_context7_tables_exist -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add scripts/context7/schema.sql scripts/context7/test_schema.py
git commit -m "feat: add Context7 database schema

Create tables for cache, project libraries, and query logging.
Includes indexes for performance and unique constraints.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 2: Redis Connection Handler

**Files:**
- Create: `.claude/hooks/lib/context7_redis.py`
- Create: `.claude/hooks/lib/test_context7_redis.py`

**Step 1: Write Redis connection test**

```python
# .claude/hooks/lib/test_context7_redis.py
import pytest
from context7_redis import RedisClient

def test_redis_connect():
    """Test Redis connection with auth."""
    client = RedisClient(
        host="100.77.248.9",
        port=6379,
        db=2
    )

    # Should connect without error
    assert client.ping() == True, "Redis ping failed"

    # Test basic operations
    client.set("test_key", "test_value", ttl=60)
    assert client.get("test_key") == "test_value"

    client.delete("test_key")
    assert client.get("test_key") is None

def test_redis_unavailable_graceful():
    """Test graceful handling when Redis unavailable."""
    client = RedisClient(host="invalid.host", port=6379, db=2)

    # Should not raise, just return None
    assert client.ping() == False
    assert client.get("any_key") is None
    assert client.set("key", "value") == False
```

**Step 2: Run test to verify it fails**

```bash
pytest .claude/hooks/lib/test_context7_redis.py -v
```

Expected: FAIL - module not found

**Step 3: Implement Redis client**

```python
# .claude/hooks/lib/context7_redis.py
import redis
import json
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

class RedisClient:
    """Redis client with graceful degradation."""

    def __init__(self, host: str, port: int, db: int, password: Optional[str] = None):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self._client = None
        self._connect()

    def _connect(self):
        """Establish Redis connection."""
        try:
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
                socket_connect_timeout=2
            )
            self._client.ping()
            logger.info(f"Connected to Redis at {self.host}:{self.port} DB{self.db}")
        except Exception as e:
            logger.warning(f"Redis unavailable: {e}")
            self._client = None

    def ping(self) -> bool:
        """Check if Redis is available."""
        if not self._client:
            return False
        try:
            return self._client.ping()
        except:
            return False

    def get(self, key: str) -> Optional[str]:
        """Get value from Redis."""
        if not self._client:
            return None
        try:
            return self._client.get(key)
        except Exception as e:
            logger.warning(f"Redis GET failed: {e}")
            return None

    def set(self, key: str, value: str, ttl: int = 86400) -> bool:
        """Set value in Redis with TTL (default 24h)."""
        if not self._client:
            return False
        try:
            self._client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.warning(f"Redis SET failed: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        if not self._client:
            return False
        try:
            self._client.delete(key)
            return True
        except:
            return False

    def get_json(self, key: str) -> Optional[dict]:
        """Get JSON value from Redis."""
        value = self.get(key)
        if value:
            try:
                return json.loads(value)
            except:
                return None
        return None

    def set_json(self, key: str, value: dict, ttl: int = 86400) -> bool:
        """Set JSON value in Redis."""
        try:
            return self.set(key, json.dumps(value), ttl)
        except:
            return False
```

**Step 4: Run test to verify it passes**

```bash
pytest .claude/hooks/lib/test_context7_redis.py -v
```

Expected: PASS (both tests)

**Step 5: Commit**

```bash
git add .claude/hooks/lib/context7_redis.py .claude/hooks/lib/test_context7_redis.py
git commit -m "feat: add Redis client with graceful degradation

Handles connection failures gracefully, returns None on errors.
Includes JSON helpers for cache operations.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 3: Fingerprinting System

**Files:**
- Create: `.claude/hooks/lib/context7_fingerprint.py`
- Create: `.claude/hooks/lib/test_context7_fingerprint.py`

**Step 1: Write fingerprint generation tests**

```python
# .claude/hooks/lib/test_context7_fingerprint.py
import pytest
from context7_fingerprint import generate_fingerprint, extract_intent

def test_extract_intent_basic():
    """Test basic intent extraction."""
    assert extract_intent("How do I implement Rails authentication?") == "authentication"
    assert extract_intent("Next.js dynamic routing guide") == "routing"
    assert extract_intent("React useEffect hook examples") == "hooks"

def test_extract_intent_normalization():
    """Test intent normalization (similar queries → same intent)."""
    # All should map to "authentication"
    queries = [
        "Rails authentication",
        "Rails auth",
        "Rails login system",
        "How to authenticate users in Rails"
    ]
    intents = [extract_intent(q) for q in queries]
    assert len(set(intents)) == 1, f"Expected same intent, got: {intents}"

def test_generate_fingerprint():
    """Test fingerprint generation."""
    fp = generate_fingerprint("rails", "7", "How do I implement Rails authentication?")
    assert fp == "rails-7:authentication"

    fp = generate_fingerprint("react", "18", "React hooks tutorial")
    assert fp == "react-18:hooks"

def test_fingerprint_deduplication():
    """Test that similar queries generate same fingerprint."""
    queries = [
        "Rails authentication",
        "Rails auth system",
        "How to add authentication to Rails"
    ]

    fingerprints = [generate_fingerprint("rails", "7", q) for q in queries]
    assert len(set(fingerprints)) == 1, f"Expected same fingerprint, got: {fingerprints}"
```

**Step 2: Run test to verify it fails**

```bash
pytest .claude/hooks/lib/test_context7_fingerprint.py -v
```

Expected: FAIL - module not found

**Step 3: Implement fingerprinting logic**

```python
# .claude/hooks/lib/context7_fingerprint.py
import re
from typing import Optional

# Intent keyword mappings (expand as needed)
INTENT_KEYWORDS = {
    'authentication': ['auth', 'authenticate', 'login', 'signup', 'sign up', 'session', 'oauth'],
    'routing': ['route', 'routing', 'navigation', 'navigate', 'url', 'path'],
    'hooks': ['hook', 'useeffect', 'usestate', 'usememo', 'usecallback'],
    'forms': ['form', 'input', 'validation', 'submit'],
    'database': ['db', 'database', 'query', 'sql', 'migration', 'model'],
    'testing': ['test', 'testing', 'spec', 'jest', 'pytest', 'rspec'],
    'styling': ['css', 'style', 'styling', 'theme', 'design'],
    'api': ['api', 'rest', 'graphql', 'endpoint', 'request', 'response'],
    'state': ['state', 'redux', 'context', 'store'],
    'performance': ['performance', 'optimize', 'optimization', 'cache', 'caching'],
}

def extract_intent(query: str) -> str:
    """
    Extract main intent from query using keyword matching.

    Returns most specific matching intent or 'general' if no match.
    """
    query_lower = query.lower()

    # Check each intent category
    for intent, keywords in INTENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in query_lower:
                return intent

    # Fall back to first significant word (3+ chars)
    words = re.findall(r'\b\w{3,}\b', query_lower)
    if words:
        # Filter out common words
        common_words = {'how', 'what', 'when', 'where', 'why', 'the', 'and', 'for', 'with'}
        significant = [w for w in words if w not in common_words]
        if significant:
            return significant[0]

    return 'general'

def generate_fingerprint(library: str, major_version: str, query: str) -> str:
    """
    Generate cache fingerprint for Context7 query.

    Format: {library}-{major_version}:{intent}
    Example: rails-7:authentication
    """
    intent = extract_intent(query)
    return f"{library}-{major_version}:{intent}"

def parse_fingerprint(fingerprint: str) -> Optional[dict]:
    """
    Parse fingerprint back into components.

    Returns: {'library': str, 'version': str, 'intent': str} or None
    """
    match = re.match(r'^([^-]+)-(\d+):(.+)$', fingerprint)
    if match:
        return {
            'library': match.group(1),
            'version': match.group(2),
            'intent': match.group(3)
        }
    return None
```

**Step 4: Run test to verify it passes**

```bash
pytest .claude/hooks/lib/test_context7_fingerprint.py -v
```

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add .claude/hooks/lib/context7_fingerprint.py .claude/hooks/lib/test_context7_fingerprint.py
git commit -m "feat: add fingerprinting system for cache deduplication

Intent extraction with keyword mapping for ~70% cache hit rate.
Format: library-version:intent (e.g., rails-7:authentication)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Phase 2: Core Cache Layer

### Task 4: Cache Manager (Redis + PostgreSQL)

**Files:**
- Create: `.claude/hooks/lib/context7_cache.py`
- Create: `.claude/hooks/lib/test_context7_cache.py`

**Step 1: Write cache manager tests**

```python
# .claude/hooks/lib/test_context7_cache.py
import pytest
from context7_cache import CacheManager
from context7_fingerprint import generate_fingerprint

@pytest.fixture
def cache_manager():
    """Create cache manager for testing."""
    return CacheManager(
        redis_host="100.77.248.9",
        redis_port=6379,
        redis_db=2,
        pg_config={
            'host': 'localhost',
            'database': 'claude_memory',
            'user': 'claude_mcp',
            'password': 'REDACTED'
        }
    )

def test_cache_miss_flow(cache_manager):
    """Test full cache miss flow: Redis → PostgreSQL → API."""
    fingerprint = generate_fingerprint("testlib", "1", "test query")

    # Clear any existing cache
    cache_manager.invalidate(fingerprint)

    # Cache miss should return None
    result = cache_manager.get(fingerprint)
    assert result is None

def test_cache_hit_redis(cache_manager):
    """Test cache hit from Redis (fast path)."""
    fingerprint = generate_fingerprint("testlib", "1", "test query")
    content = {"docs": "test content", "examples": []}

    # Store in Redis
    cache_manager.set(fingerprint, "testlib", "1", "test", content, None)

    # Should retrieve from Redis
    result = cache_manager.get(fingerprint)
    assert result is not None
    assert result['content'] == content

def test_cache_fallback_to_postgres(cache_manager):
    """Test fallback to PostgreSQL when Redis unavailable."""
    fingerprint = generate_fingerprint("testlib", "1", "test query")
    content = {"docs": "test content"}

    # Store directly in PostgreSQL (bypass Redis)
    cache_manager._store_postgres(fingerprint, "testlib", "1", "test", content, None)

    # Flush Redis to simulate unavailability
    cache_manager.redis.delete(f"context7:cache:{fingerprint}")

    # Should still retrieve from PostgreSQL
    result = cache_manager.get(fingerprint)
    assert result is not None
    assert result['content'] == content

def test_usage_tracking(cache_manager):
    """Test query count and last_accessed tracking."""
    fingerprint = generate_fingerprint("testlib", "1", "test query")
    content = {"docs": "test"}

    # Store once
    cache_manager.set(fingerprint, "testlib", "1", "test", content, None)

    # Access multiple times
    for _ in range(3):
        cache_manager.get(fingerprint)

    # Check query count increased
    stats = cache_manager.get_stats(fingerprint)
    assert stats['query_count'] >= 3
```

**Step 2: Run test to verify it fails**

```bash
pytest .claude/hooks/lib/test_context7_cache.py -v
```

Expected: FAIL - module not found

**Step 3: Implement cache manager** (continue in next task due to length)

```python
# .claude/hooks/lib/context7_cache.py
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from context7_redis import RedisClient

logger = logging.getLogger(__name__)

class CacheManager:
    """Two-tier cache manager (Redis + PostgreSQL)."""

    def __init__(self, redis_host: str, redis_port: int, redis_db: int,
                 pg_config: dict, redis_password: Optional[str] = None):
        self.redis = RedisClient(redis_host, redis_port, redis_db, redis_password)
        self.pg_config = pg_config

    def get(self, fingerprint: str) -> Optional[Dict[str, Any]]:
        """
        Get cached content (Redis → PostgreSQL → None).

        Returns: {'content': dict, 'citations': dict, 'query_count': int, 'last_accessed': datetime}
        """
        # Fast path: Check Redis
        cache_key = f"context7:cache:{fingerprint}"
        cached = self.redis.get_json(cache_key)
        if cached:
            logger.debug(f"Cache HIT (Redis): {fingerprint}")
            self._log_query(fingerprint, None, True, 0)
            self._update_access_time(fingerprint)
            return cached

        # Warm path: Check PostgreSQL
        cached = self._get_postgres(fingerprint)
        if cached:
            logger.debug(f"Cache HIT (PostgreSQL): {fingerprint}")
            # Populate Redis for next access
            self.redis.set_json(cache_key, cached, ttl=86400)
            self._log_query(fingerprint, None, True, 0)
            self._update_access_time(fingerprint)
            return cached

        # Cache miss
        logger.debug(f"Cache MISS: {fingerprint}")
        self._log_query(fingerprint, None, False, 0)
        return None

    def set(self, fingerprint: str, library_id: str, library_version: str,
            query_intent: str, content: dict, citations: Optional[dict]) -> bool:
        """Store content in both Redis and PostgreSQL."""
        data = {
            'content': content,
            'citations': citations,
            'query_count': 1,
            'last_accessed': datetime.now().isoformat()
        }

        # Store in Redis
        cache_key = f"context7:cache:{fingerprint}"
        self.redis.set_json(cache_key, data, ttl=86400)

        # Store in PostgreSQL
        return self._store_postgres(fingerprint, library_id, library_version,
                                    query_intent, content, citations)

    def _get_postgres(self, fingerprint: str) -> Optional[Dict[str, Any]]:
        """Get cached content from PostgreSQL."""
        try:
            conn = psycopg2.connect(**self.pg_config)
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("""
                SELECT content, citations, query_count, last_accessed
                FROM context7_cache
                WHERE fingerprint = %s;
            """, (fingerprint,))

            row = cur.fetchone()
            conn.close()

            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"PostgreSQL GET failed: {e}")
            return None

    def _store_postgres(self, fingerprint: str, library_id: str, library_version: str,
                       query_intent: str, content: dict, citations: Optional[dict]) -> bool:
        """Store content in PostgreSQL."""
        try:
            conn = psycopg2.connect(**self.pg_config)
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO context7_cache
                (fingerprint, library_id, library_version, query_intent, content, citations)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (fingerprint) DO UPDATE SET
                    content = EXCLUDED.content,
                    citations = EXCLUDED.citations,
                    query_count = context7_cache.query_count + 1,
                    last_accessed = NOW();
            """, (fingerprint, library_id, library_version, query_intent,
                  json.dumps(content), json.dumps(citations) if citations else None))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"PostgreSQL STORE failed: {e}")
            return False

    def _update_access_time(self, fingerprint: str):
        """Update last_accessed timestamp and increment query_count."""
        try:
            conn = psycopg2.connect(**self.pg_config)
            cur = conn.cursor()

            cur.execute("""
                UPDATE context7_cache
                SET last_accessed = NOW(), query_count = query_count + 1
                WHERE fingerprint = %s;
            """, (fingerprint,))

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Update access time failed: {e}")

    def _log_query(self, fingerprint: str, original_query: Optional[str],
                   cache_hit: bool, response_time_ms: int):
        """Log query to analytics table."""
        try:
            conn = psycopg2.connect(**self.pg_config)
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO context7_query_log
                (fingerprint, original_query, cache_hit, response_time_ms)
                VALUES (%s, %s, %s, %s);
            """, (fingerprint, original_query, cache_hit, response_time_ms))

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Log query failed: {e}")

    def invalidate(self, fingerprint: str) -> bool:
        """Remove entry from cache."""
        cache_key = f"context7:cache:{fingerprint}"
        self.redis.delete(cache_key)

        try:
            conn = psycopg2.connect(**self.pg_config)
            cur = conn.cursor()
            cur.execute("DELETE FROM context7_cache WHERE fingerprint = %s;", (fingerprint,))
            conn.commit()
            conn.close()
            return True
        except:
            return False

    def get_stats(self, fingerprint: str) -> Optional[dict]:
        """Get cache statistics for fingerprint."""
        try:
            conn = psycopg2.connect(**self.pg_config)
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("""
                SELECT query_count, last_accessed, created_at
                FROM context7_cache
                WHERE fingerprint = %s;
            """, (fingerprint,))

            row = cur.fetchone()
            conn.close()

            return dict(row) if row else None
        except:
            return None
```

**Step 4: Run test to verify it passes**

```bash
pytest .claude/hooks/lib/test_context7_cache.py -v
```

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add .claude/hooks/lib/context7_cache.py .claude/hooks/lib/test_context7_cache.py
git commit -m "feat: add two-tier cache manager (Redis + PostgreSQL)

Fast path: Redis (hot cache)
Warm path: PostgreSQL (persistent)
Includes usage tracking and analytics logging.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Phase 3: Manifest Parsers

### Task 5: Package.json Parser

**Files:**
- Create: `.claude/hooks/lib/manifest_parsers.py`
- Create: `.claude/hooks/lib/test_manifest_parsers.py`

**Step 1: Write package.json parser test**

```python
# .claude/hooks/lib/test_manifest_parsers.py
import pytest
import json
import os
from manifest_parsers import parse_package_json, parse_gemfile

def test_parse_package_json(tmp_path):
    """Test parsing package.json for dependencies."""
    package_json = {
        "dependencies": {
            "react": "^18.2.0",
            "next": "14.0.3"
        },
        "devDependencies": {
            "typescript": "^5.0.0"
        }
    }

    # Write test package.json
    pkg_file = tmp_path / "package.json"
    pkg_file.write_text(json.dumps(package_json))

    # Parse
    libraries = parse_package_json(str(tmp_path))

    assert len(libraries) == 3
    assert ("react", "18") in [(lib['library'], lib['major_version']) for lib in libraries]
    assert ("next", "14") in [(lib['library'], lib['major_version']) for lib in libraries]
    assert ("typescript", "5") in [(lib['library'], lib['major_version']) for lib in libraries]

def test_parse_package_json_missing(tmp_path):
    """Test handling missing package.json."""
    libraries = parse_package_json(str(tmp_path))
    assert libraries == []
```

**Step 2: Run test to verify it fails**

```bash
pytest .claude/hooks/lib/test_manifest_parsers.py::test_parse_package_json -v
```

Expected: FAIL - module not found

**Step 3: Implement package.json parser**

```python
# .claude/hooks/lib/manifest_parsers.py
import json
import os
import re
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

def extract_major_version(version_string: str) -> str:
    """Extract major version from version string."""
    # Handle ^18.2.0, ~18.2.0, 18.2.0, >=18.0.0, etc.
    match = re.search(r'(\d+)', version_string)
    return match.group(1) if match else "latest"

def parse_package_json(project_path: str) -> List[Dict[str, str]]:
    """
    Parse package.json for JavaScript/TypeScript dependencies.

    Returns: [{'library': str, 'major_version': str, 'source': 'manifest'}, ...]
    """
    pkg_file = os.path.join(project_path, "package.json")
    if not os.path.exists(pkg_file):
        return []

    try:
        with open(pkg_file, 'r') as f:
            pkg_data = json.load(f)

        libraries = []

        # Parse dependencies
        for dep, version in pkg_data.get('dependencies', {}).items():
            libraries.append({
                'library': dep,
                'major_version': extract_major_version(version),
                'source': 'manifest'
            })

        # Parse devDependencies
        for dep, version in pkg_data.get('devDependencies', {}).items():
            libraries.append({
                'library': dep,
                'major_version': extract_major_version(version),
                'source': 'manifest'
            })

        logger.info(f"Parsed {len(libraries)} libraries from package.json")
        return libraries

    except Exception as e:
        logger.error(f"Failed to parse package.json: {e}")
        return []

def parse_gemfile(project_path: str) -> List[Dict[str, str]]:
    """
    Parse Gemfile for Ruby gems.

    Returns: [{'library': str, 'major_version': str, 'source': 'manifest'}, ...]
    """
    gemfile = os.path.join(project_path, "Gemfile")
    if not os.path.exists(gemfile):
        return []

    try:
        with open(gemfile, 'r') as f:
            content = f.read()

        libraries = []

        # Match: gem 'rails', '~> 7.0'
        # Match: gem "rails", "~> 7.0"
        # Match: gem 'rails'
        pattern = r"gem\s+['\"]([^'\"]+)['\"](?:\s*,\s*['\"]([^'\"]+)['\"])?"

        for match in re.finditer(pattern, content):
            gem_name = match.group(1)
            version = match.group(2) if match.group(2) else "latest"

            libraries.append({
                'library': gem_name,
                'major_version': extract_major_version(version),
                'source': 'manifest'
            })

        logger.info(f"Parsed {len(libraries)} gems from Gemfile")
        return libraries

    except Exception as e:
        logger.error(f"Failed to parse Gemfile: {e}")
        return []

def parse_requirements_txt(project_path: str) -> List[Dict[str, str]]:
    """
    Parse requirements.txt for Python packages.

    Returns: [{'library': str, 'major_version': str, 'source': 'manifest'}, ...]
    """
    req_file = os.path.join(project_path, "requirements.txt")
    if not os.path.exists(req_file):
        return []

    try:
        with open(req_file, 'r') as f:
            lines = f.readlines()

        libraries = []

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Match: package==1.2.3, package>=1.2, package~=1.2
            match = re.match(r'^([a-zA-Z0-9_-]+)([=~><]+)?([\d.]+)?', line)
            if match:
                package = match.group(1)
                version = match.group(3) if match.group(3) else "latest"

                libraries.append({
                    'library': package,
                    'major_version': extract_major_version(version),
                    'source': 'manifest'
                })

        logger.info(f"Parsed {len(libraries)} packages from requirements.txt")
        return libraries

    except Exception as e:
        logger.error(f"Failed to parse requirements.txt: {e}")
        return []

def parse_all_manifests(project_path: str) -> List[Dict[str, str]]:
    """Parse all supported manifest files in project."""
    all_libraries = []

    all_libraries.extend(parse_package_json(project_path))
    all_libraries.extend(parse_gemfile(project_path))
    all_libraries.extend(parse_requirements_txt(project_path))

    return all_libraries
```

**Step 4: Run test to verify it passes**

```bash
pytest .claude/hooks/lib/test_manifest_parsers.py -v
```

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add .claude/hooks/lib/manifest_parsers.py .claude/hooks/lib/test_manifest_parsers.py
git commit -m "feat: add manifest parsers for npm, gem, pip

Extracts dependencies with major versions from:
- package.json (npm/yarn)
- Gemfile (Ruby gems)
- requirements.txt (Python packages)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Phase 4: Skills & Hooks

### Task 6: `/load-docs` Skill

**Files:**
- Create: `.claude/skills/load-docs/skill.md`
- Create: `.claude/skills/load-docs/load_docs.py`

**Step 1: Write skill definition**

```markdown
# .claude/skills/load-docs/skill.md
---
name: load-docs
description: Manually load Context7 documentation for specified libraries with intelligent caching
---

# Load Documentation

Load Context7 documentation for one or more libraries with intelligent caching.

## Usage

```bash
/load-docs rails hotwire react
/load-docs nextjs --version 14
/load-docs typescript --refresh
```

## Flags

- `--refresh` - Force refresh from Context7 API (bypass cache)
- `--version N` - Specify major version (default: auto-detect from project)

## How it works

1. Resolves library names to Context7 library IDs
2. Detects versions from project manifest files
3. Checks cache (Redis → PostgreSQL)
4. Fetches from Context7 API on cache miss
5. Updates usage statistics for smart preloading

## Output

```
Loading documentation...
✓ Rails 7 (from cache - 15ms)
✓ Hotwire 8 (from cache - 12ms)
✓ React 18 (fetched - 1.2s)

Loaded 3 libraries (2 from cache, 1 fetched)
Total time: 1.23s
```

## Implementation

Run: `python3 ~/.claude/skills/load-docs/load_docs.py "$@"`
```

**Step 2: Write skill script** (partial - full implementation in separate task)

```python
# .claude/skills/load-docs/load_docs.py
#!/usr/bin/env python3
"""
Load Context7 documentation with intelligent caching.
Usage: /load-docs rails hotwire react [--refresh]
"""

import sys
import os
import time
import logging
from pathlib import Path

# Add lib to path
sys.path.insert(0, os.path.expanduser('~/.claude/hooks/lib'))

from context7_cache import CacheManager
from context7_fingerprint import generate_fingerprint
from manifest_parsers import parse_all_manifests

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.FileHandler(os.path.expanduser('~/.logs/context7-skill.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# TODO: Implement library name → Context7 library ID resolution
# TODO: Implement Context7 MCP query
# TODO: Implement usage tracking

def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: /load-docs <library> [<library>...] [--refresh]")
        return 1

    # Parse flags
    force_refresh = '--refresh' in args
    libraries = [arg for arg in args if not arg.startswith('--')]

    print(f"Loading documentation for: {', '.join(libraries)}")

    # TODO: Implementation
    print("⚠️  Not yet implemented - coming in next phase")

    return 0

if __name__ == '__main__':
    sys.exit(main())
```

**Step 3: Make skill executable and test stub**

```bash
chmod +x .claude/skills/load-docs/load_docs.py
python3 .claude/skills/load-docs/load_docs.py rails
```

Expected: "Not yet implemented" message

**Step 4: Commit skill stub**

```bash
git add .claude/skills/load-docs/
git commit -m "feat: add /load-docs skill stub

Manual documentation loading with caching support.
Full implementation requires Context7 MCP integration.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 7: SessionStart Hook

**Files:**
- Create: `.claude/hooks/on-session-start-context7.sh`
- Create: `.claude/hooks/context7-preloader.py`

**Step 1: Write SessionStart hook**

```bash
# .claude/hooks/on-session-start-context7.sh
#!/bin/bash
# Context7 Proactive Preloader
# Runs in background, doesn't block session start

python3 ~/.claude/hooks/context7-preloader.py \
    --project-path "$PWD" \
    --max-preload 5 \
    --timeout 10 \
    >> ~/.logs/context7-preload.log 2>&1 &
```

**Step 2: Write preloader script** (stub for now)

```python
# .claude/hooks/context7-preloader.py
#!/usr/bin/env python3
"""
Context7 session preloader.
Detects project libraries and preloads top N docs.
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add lib to path
sys.path.insert(0, os.path.expanduser('~/.claude/hooks/lib'))

from manifest_parsers import parse_all_manifests
from context7_cache import CacheManager

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-path', required=True)
    parser.add_argument('--max-preload', type=int, default=5)
    parser.add_argument('--timeout', type=int, default=10)
    args = parser.parse_args()

    logger.info("="*60)
    logger.info("Context7 SessionStart Preloader")
    logger.info(f"Project: {args.project_path}")

    # Parse manifests
    libraries = parse_all_manifests(args.project_path)
    logger.info(f"Detected {len(libraries)} libraries from manifests")

    # TODO: Query PostgreSQL for usage-based libraries
    # TODO: Rank and preload top N
    # TODO: Store in Redis

    logger.info("Preloading not yet implemented")
    logger.info("="*60)

    return 0

if __name__ == '__main__':
    sys.exit(main())
```

**Step 3: Make executable and test**

```bash
chmod +x .claude/hooks/on-session-start-context7.sh
chmod +x .claude/hooks/context7-preloader.py
bash .claude/hooks/on-session-start-context7.sh
```

Expected: Log entry in `~/.logs/context7-preload.log`

**Step 4: Add hook to settings.json**

```bash
# Manual step - add to settings.json:
# "SessionStart": [
#   {
#     "hooks": [
#       {
#         "type": "command",
#         "command": "~/.claude/hooks/on-session-start-context7.sh",
#         "timeout": 15
#       }
#     ]
#   }
# ]
```

**Step 5: Commit**

```bash
git add .claude/hooks/on-session-start-context7.sh .claude/hooks/context7-preloader.py
git commit -m "feat: add SessionStart hook for context7 preloading

Runs in background, parses manifests, prepares for preloading.
Full implementation requires Context7 MCP integration.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Phase 5: Context7 MCP Integration

### Task 8: Context7 MCP Client Wrapper

**Note:** This task requires understanding the actual Context7 MCP API.
The implementation will depend on the MCP tool signatures.

**Files:**
- Create: `.claude/hooks/lib/context7_mcp.py`
- Create: `.claude/hooks/lib/test_context7_mcp.py`

**Placeholder:** This task should:
1. Query available Context7 MCP tools
2. Implement library name → library ID resolution
3. Implement query execution with error handling
4. Add rate limiting (max 10 queries per preload)
5. Add timeout protection

**Commit message:** `feat: add Context7 MCP client wrapper`

---

## Phase 6: Integration & Polish

### Task 9: Complete `/load-docs` Implementation

**Update:** `.claude/skills/load-docs/load_docs.py`

Complete the TODO sections:
- Library ID resolution via Context7 MCP
- Cache check & fetch logic
- Usage statistics tracking
- Error handling & retries

**Commit message:** `feat: complete /load-docs skill implementation`

---

### Task 10: Complete Preloader Implementation

**Update:** `.claude/hooks/context7-preloader.py`

Complete the TODO sections:
- Query PostgreSQL for usage-based libraries
- Rank by manifest + usage
- Preload top 5 via Context7 MCP
- Store in Redis + PostgreSQL

**Commit message:** `feat: complete SessionStart preloader implementation`

---

### Task 11: Health Check Skill

**Files:**
- Create: `.claude/skills/check-context7/skill.md`
- Create: `.claude/skills/check-context7/check_context7.py`

Implement `/check-context7` command showing:
- Redis connection status
- PostgreSQL connection status
- Context7 API status
- Cache hit rate (last 7 days)
- Top 5 libraries by usage
- Current project's detected libraries

**Commit message:** `feat: add /check-context7 health check skill`

---

### Task 12: Documentation

**Files:**
- Create: `docs/context7-proactive-retrieval-user-guide.md`

Write user guide covering:
- Installation steps
- Configuration (Redis auth)
- Using `/load-docs` skill
- Understanding SessionStart preloading
- Reading `/check-context7` output
- Troubleshooting common issues

**Commit message:** `docs: add Context7 Proactive Retrieval user guide`

---

## Success Criteria

- [ ] All tests pass (`pytest .claude/hooks/lib/test_*.py`)
- [ ] Database schema applied and verified
- [ ] Redis connection working with auth
- [ ] `/load-docs` skill functional
- [ ] SessionStart hook preloads libraries
- [ ] Cache hit rate >50% after first use
- [ ] Graceful degradation when services unavailable
- [ ] All code committed with clear messages
- [ ] User documentation complete

---

## Execution Notes

**Testing Strategy:**
- Unit tests for each component
- Integration test with real Context7 queries
- Manual testing of SessionStart hook
- Cache performance verification

**Rollback Plan:**
- Remove SessionStart hook from settings.json
- Drop Context7 tables if needed
- Flush Redis DB 2

**Dependencies:**
- Python packages: `redis`, `psycopg2`
- Context7 MCP plugin must be enabled
- Redis server running on 100.77.248.9:6379
- PostgreSQL claude_memory database accessible
