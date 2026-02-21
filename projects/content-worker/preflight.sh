#!/bin/bash
# Pipeline Preflight — validates environment before accepting work
# Exit code 0 = healthy, non-zero = broken
set -euo pipefail

ERRORS=0
WARNINGS=0

echo "=== PIPELINE PREFLIGHT CHECK ==="
echo "Date: $(date -Iseconds)"
echo ""

# 1. Python version check (must be 3.13+ for f-string syntax used in ninja_content.py)
echo -n "[CHECK] Python version... "
PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if python3 -c "import sys; assert sys.version_info >= (3,13)"; then
    echo "OK ($PY_VER)"
else
    echo "FAIL ($PY_VER, need 3.13+)"
    ((ERRORS++))
fi

# 2. Critical Python imports
echo -n "[CHECK] Python dependencies... "
MISSING_DEPS=""
for pkg in celery requests fal_client keyring google.genai; do
    if ! python3 -c "import $pkg" 2>/dev/null; then
        MISSING_DEPS="$MISSING_DEPS $pkg"
    fi
done
if [ -z "$MISSING_DEPS" ]; then
    echo "OK"
else
    echo "FAIL (missing:$MISSING_DEPS)"
    ((ERRORS++))
fi

# 3. Required env vars — must be non-empty
echo -n "[CHECK] API keys present... "
MISSING_KEYS=""
for var in ELEVENLABS_API_KEY GOOGLE_CLOUD_PROJECT; do
    if [ -z "${!var:-}" ]; then
        MISSING_KEYS="$MISSING_KEYS $var"
    fi
done
# fal.ai: accept either FAL_KEY or FAL_AI_API_KEY
if [ -z "${FAL_KEY:-}" ] && [ -z "${FAL_AI_API_KEY:-}" ]; then
    MISSING_KEYS="$MISSING_KEYS FAL_KEY/FAL_AI_API_KEY"
fi
if [ -z "$MISSING_KEYS" ]; then
    echo "OK"
else
    echo "FAIL (missing:$MISSING_KEYS)"
    ((ERRORS++))
fi

# 4. fal.ai env var name normalization (the FAL_KEY vs FAL_AI_API_KEY bug)
echo -n "[CHECK] fal.ai key normalization... "
if [ -n "${FAL_KEY:-}" ] && [ -z "${FAL_AI_API_KEY:-}" ]; then
    export FAL_AI_API_KEY="$FAL_KEY"
    echo "FIXED (FAL_KEY -> FAL_AI_API_KEY)"
elif [ -z "${FAL_KEY:-}" ] && [ -n "${FAL_AI_API_KEY:-}" ]; then
    export FAL_KEY="$FAL_AI_API_KEY"
    echo "FIXED (FAL_AI_API_KEY -> FAL_KEY)"
else
    echo "OK"
fi

# 5. Volume mount paths — must exist and be writable
echo -n "[CHECK] Output directory... "
OUTPUT="${OUTPUT_DIR:-/data/output}"
if [ -d "$OUTPUT" ] && [ -w "$OUTPUT" ]; then
    echo "OK ($OUTPUT)"
else
    echo "FAIL ($OUTPUT not writable)"
    ((ERRORS++))
fi

echo -n "[CHECK] Scripts directory... "
SCRIPT="${CONTENT_SCRIPT:-/app/scripts/ninja_content.py}"
if [ -f "$SCRIPT" ]; then
    echo "OK ($SCRIPT)"
else
    echo "FAIL ($SCRIPT not found)"
    ((ERRORS++))
fi

echo -n "[CHECK] Assets directory... "
AVATAR="/app/assets/reference/ninja_helmet_v4_hires.jpg"
if [ -f "$AVATAR" ]; then
    echo "OK"
else
    echo "WARN (avatar image not found at $AVATAR)"
    ((WARNINGS++))
fi

echo -n "[CHECK] B-roll directory... "
BROLL="${BROLL_DIR:-/data/output/broll}"
if [ -d "$BROLL" ]; then
    COUNT=$(find "$BROLL" -name "*.mp4" 2>/dev/null | wc -l)
    echo "OK ($COUNT clips)"
else
    echo "WARN (no broll dir at $BROLL)"
    ((WARNINGS++))
fi

# 6. ffmpeg/ffprobe available
echo -n "[CHECK] ffmpeg... "
if command -v ffmpeg &>/dev/null && command -v ffprobe &>/dev/null; then
    echo "OK ($(ffmpeg -version 2>&1 | head -1 | cut -d' ' -f3))"
else
    echo "FAIL (ffmpeg/ffprobe not installed)"
    ((ERRORS++))
fi

# 7. Redis/Celery broker reachable
echo -n "[CHECK] Redis broker... "
BROKER="${CELERY_BROKER_URL:-}"
if [ -n "$BROKER" ]; then
    REDIS_HOST=$(echo "$BROKER" | sed 's|redis://||;s|:.*||')
    REDIS_PORT=$(echo "$BROKER" | grep -oP ':\K[0-9]+' | head -1)
    if timeout 3 bash -c "echo PING | nc -q1 $REDIS_HOST ${REDIS_PORT:-6379}" 2>/dev/null | grep -q PONG; then
        echo "OK ($REDIS_HOST:${REDIS_PORT:-6379})"
    else
        echo "WARN (cannot reach $REDIS_HOST:${REDIS_PORT:-6379})"
        ((WARNINGS++))
    fi
else
    echo "SKIP (no CELERY_BROKER_URL)"
fi

# 8. API key connectivity test (lightweight — just check auth, don't generate)
echo -n "[CHECK] ElevenLabs API reachable... "
if [ -n "${ELEVENLABS_API_KEY:-}" ]; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "xi-api-key: $ELEVENLABS_API_KEY" \
        "https://api.elevenlabs.io/v1/user" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        echo "OK"
    else
        echo "FAIL (HTTP $HTTP_CODE)"
        ((ERRORS++))
    fi
else
    echo "SKIP (no key)"
fi

echo ""
echo "=== PREFLIGHT RESULT: $ERRORS errors, $WARNINGS warnings ==="

if [ $ERRORS -gt 0 ]; then
    echo "PREFLIGHT FAILED — container should NOT accept work"
    exit 1
fi

echo "PREFLIGHT PASSED"
exit 0
