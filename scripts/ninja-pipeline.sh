#!/usr/bin/env bash
# ninja-pipeline.sh — Automated ninja avatar talking head pipeline
# Text → ElevenLabs TTS → Ditto lip-sync → background → upscale → captions → music → finished MP4
set -euo pipefail

###############################################################################
# Configuration
###############################################################################
STEAM_HOST="Steam@100.98.226.75"
DEFAULT_VOICE_ID="pDrEFcc78kuc76ECGkU8"
ELEVENLABS_MODEL="eleven_multilingual_v2"
ENV_FILE="/home/ndninja/projects/content-automation/.env"
AVATAR_PATH="/home/steam/musetalk/data/video/ninja_avatar.jpg"
DITTO_CHECKPOINTS="/home/steam/ditto/checkpoints"
DITTO_OUTPUT="/home/steam/ditto/output"
LOCAL_OUTPUT_DIR="/home/ndninja/clawd/output"

###############################################################################
# Helpers
###############################################################################
log()  { echo "[$(date '+%H:%M:%S')] $*"; }
die()  { echo "ERROR: $*" >&2; exit 1; }

usage() {
    cat <<'EOF'
ninja-pipeline.sh — Ninja avatar talking head video generator

USAGE:
    ninja-pipeline.sh [OPTIONS] "Your script text here"
    ninja-pipeline.sh [OPTIONS] --file script.txt

ARGUMENTS:
    TEXT            The text to speak (required unless --file is used)

OPTIONS:
    -o, --output    Output filename (default: ninja_<timestamp>.mp4)
    -v, --voice     ElevenLabs voice ID (default: cloned voice 5hxLrDDIrA21my3IkPxP)
    -f, --file      Read text from file instead of argument
    -k, --keep      Keep intermediate files (audio, etc.)
    --stability     Voice stability 0.0-1.0 (default: 0.5)
    --similarity    Voice similarity boost 0.0-1.0 (default: 0.75)
    --no-music      Skip background music step
    --music FILE    Use specific music file (default: random from assets/music/)
    --music-vol N   Music volume 0.0-1.0 (default: 0.15)
    --background F  Custom background image/video for compositing
    --bg-style S    Built-in background style (cyberpunk|dark_studio|gaming|dojo|matrix)
    --bg-method M   Background removal method (rembg|luminance|grabcut, default: rembg)
    --no-bg         Skip background compositing step
    --dry-run       Show what would be done without executing
    -h, --help      Show this help message

EXAMPLES:
    ninja-pipeline.sh "Shadow Operators reporting in."
    ninja-pipeline.sh -o intro.mp4 "Welcome to the channel"
    ninja-pipeline.sh --file script.txt -o episode1.mp4
    ninja-pipeline.sh -v VOICE_ID "Custom voice test"
    ninja-pipeline.sh --bg-style cyberpunk "Check this out"
    ninja-pipeline.sh --background my_bg.png "Custom background"

PIPELINE:
    1. Text → ElevenLabs TTS (MP3) → WAV 16kHz mono
    2. WAV → SCP to Steam PC → Ditto TalkingHead (Docker + RTX 4090)
    3. Result MP4 → SCP back → local output
    4. Retrieve result from Steam PC
    5. Composite avatar over background (optional, skip with --no-bg)
    6. Upscale 288×512 → 1080×1920 (lanczos + unsharp)
    7. Burn styled captions at full resolution
    8. Add background music (optional, skip with --no-music)
EOF
    exit 0
}

###############################################################################
# Parse arguments
###############################################################################
TEXT=""
OUTPUT_NAME=""
VOICE_ID="$DEFAULT_VOICE_ID"
TEXT_FILE=""
KEEP_INTERMEDIATES=false
STABILITY="0.5"
SIMILARITY="0.75"
DRY_RUN=false
NO_MUSIC=false
MUSIC_FILE=""
MUSIC_VOLUME="0.15"
BACKGROUND=""
BG_STYLE=""
BG_METHOD="rembg"
NO_BG=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)       usage ;;
        -o|--output)     OUTPUT_NAME="$2"; shift 2 ;;
        -v|--voice)      VOICE_ID="$2"; shift 2 ;;
        -f|--file)       TEXT_FILE="$2"; shift 2 ;;
        -k|--keep)       KEEP_INTERMEDIATES=true; shift ;;
        --stability)     STABILITY="$2"; shift 2 ;;
        --similarity)    SIMILARITY="$2"; shift 2 ;;
        --no-music)      NO_MUSIC=true; shift ;;
        --music)         MUSIC_FILE="$2"; shift 2 ;;
        --music-vol)     MUSIC_VOLUME="$2"; shift 2 ;;
        --background)    BACKGROUND="$2"; shift 2 ;;
        --bg-style)      BG_STYLE="$2"; shift 2 ;;
        --bg-method)     BG_METHOD="$2"; shift 2 ;;
        --no-bg)         NO_BG=true; shift ;;
        --dry-run)       DRY_RUN=true; shift ;;
        -*)              die "Unknown option: $1 (try --help)" ;;
        *)               TEXT="$1"; shift ;;
    esac
done

# Read text from file if specified
if [[ -n "$TEXT_FILE" ]]; then
    [[ -f "$TEXT_FILE" ]] || die "Text file not found: $TEXT_FILE"
    TEXT="$(cat "$TEXT_FILE")"
fi

[[ -n "$TEXT" ]] || die "No text provided. Use --help for usage."

# Load API key
[[ -f "$ENV_FILE" ]] || die "Env file not found: $ENV_FILE"
ELEVENLABS_API_KEY="$(grep '^ELEVENLABS_API_KEY=' "$ENV_FILE" | cut -d'=' -f2-)"
[[ -n "$ELEVENLABS_API_KEY" ]] || die "ELEVENLABS_API_KEY not found in $ENV_FILE"

# Generate output name if not provided
TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"
if [[ -z "$OUTPUT_NAME" ]]; then
    # Create a slug from the first few words
    SLUG="$(echo "$TEXT" | tr '[:upper:]' '[:lower:]' | tr -cs '[:alnum:]' '_' | cut -c1-30 | sed 's/_$//')"
    OUTPUT_NAME="ninja_${SLUG}_${TIMESTAMP}.mp4"
fi
# Ensure .mp4 extension
[[ "$OUTPUT_NAME" == *.mp4 ]] || OUTPUT_NAME="${OUTPUT_NAME}.mp4"

# Create work directories
mkdir -p "$LOCAL_OUTPUT_DIR"
WORK_DIR="$(mktemp -d /tmp/ninja-pipeline-XXXXXX)"
trap 'if ! $KEEP_INTERMEDIATES; then rm -rf "$WORK_DIR"; fi' EXIT

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "🥷 Ninja Avatar Pipeline"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "Text:     ${TEXT:0:80}$([ ${#TEXT} -gt 80 ] && echo '...')"
log "Voice:    $VOICE_ID"
log "Output:   $OUTPUT_NAME"
log "Work dir: $WORK_DIR"
log ""

if $DRY_RUN; then
    log "[DRY RUN] Would execute pipeline steps — exiting"
    exit 0
fi

###############################################################################
# STEP 1: Text → Speech (ElevenLabs)
###############################################################################
log "📢 Step 1/8: Generating speech via ElevenLabs..."

TTS_MP3="$WORK_DIR/tts_output.mp3"
TTS_WAV="$WORK_DIR/audio.wav"

HTTP_CODE=$(curl -s -w '%{http_code}' -o "$TTS_MP3" \
    -X POST \
    "https://api.elevenlabs.io/v1/text-to-speech/$VOICE_ID" \
    -H "xi-api-key: $ELEVENLABS_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$(cat <<JSONEOF
{
    "text": $(echo "$TEXT" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))'),
    "model_id": "$ELEVENLABS_MODEL",
    "voice_settings": {
        "stability": $STABILITY,
        "similarity_boost": $SIMILARITY
    }
}
JSONEOF
)")

if [[ "$HTTP_CODE" != "200" ]]; then
    log "❌ ElevenLabs API returned HTTP $HTTP_CODE"
    cat "$TTS_MP3" >&2
    die "TTS generation failed"
fi

MP3_SIZE=$(stat -c%s "$TTS_MP3" 2>/dev/null || stat -f%z "$TTS_MP3")
log "   ✅ TTS audio generated (${MP3_SIZE} bytes)"

###############################################################################
# STEP 2: Convert to WAV 16kHz mono for Ditto
###############################################################################
log "🔊 Step 2/8: Converting audio to WAV 16kHz mono (with silence padding)..."

# Convert TTS to WAV
TTS_WAV_RAW="$WORK_DIR/audio_raw.wav"
TTS_WAV_PAD="$WORK_DIR/silence_pad.wav"
ffmpeg -y -i "$TTS_MP3" -ar 16000 -ac 1 -acodec pcm_s16le "$TTS_WAV_RAW" 2>/dev/null

# Prepend 500ms silence to prevent AAC encoder from clipping the first word
ffmpeg -y -f lavfi -i "anullsrc=r=16000:cl=mono" -t 0.5 -acodec pcm_s16le "$TTS_WAV_PAD" 2>/dev/null
ffmpeg -y -i "$TTS_WAV_PAD" -i "$TTS_WAV_RAW" \
    -filter_complex "[0:a][1:a]concat=n=2:v=0:a=1[out]" -map "[out]" \
    -ar 16000 -ac 1 -acodec pcm_s16le "$TTS_WAV" 2>/dev/null
WAV_SIZE=$(stat -c%s "$TTS_WAV" 2>/dev/null || stat -f%z "$TTS_WAV")
DURATION=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$TTS_WAV" | cut -d. -f1)
log "   ✅ WAV converted (${WAV_SIZE} bytes, ~${DURATION}s)"

###############################################################################
# STEP 3: Lip-sync via Ditto on Steam PC
###############################################################################
log "🎬 Step 3/8: Running Ditto lip-sync on Steam PC (RTX 4090)..."

# Sanitize output name for remote use (no spaces or special chars in basename)
REMOTE_OUTPUT_BASE="$(basename "$OUTPUT_NAME")"

# Create the Docker run script
DOCKER_SCRIPT="$WORK_DIR/run.sh"
cat > "$DOCKER_SCRIPT" <<RUNEOF
#!/bin/bash
set -e
echo "[Ditto] Installing runtime dependencies..."
pip install -q einops pillow
echo "[Ditto] Running inference..."
python inference.py \
    --data_root ./checkpoints/ditto_pytorch \
    --cfg_pkl ./checkpoints/ditto_cfg/v0.4_hubert_cfg_pytorch.pkl \
    --audio_path /data/input/audio.wav \
    --source_path /data/input/source.jpg \
    --output_path /data/output/${REMOTE_OUTPUT_BASE}
echo "[Ditto] Inference complete"
RUNEOF
chmod +x "$DOCKER_SCRIPT"

# Upload audio and run script to Steam PC (WSL)
log "   Uploading audio to Steam PC..."
# Copy to Windows first, then into WSL
scp -q "$TTS_WAV" "${STEAM_HOST}:C:/Users/Steam/audio.wav"
scp -q "$DOCKER_SCRIPT" "${STEAM_HOST}:C:/Users/Steam/run.sh"

# Move from Windows into WSL filesystem
ssh "$STEAM_HOST" "wsl mkdir -p /tmp/ninja-pipeline"
ssh "$STEAM_HOST" "wsl cp /mnt/c/Users/Steam/audio.wav /tmp/ninja-pipeline/audio.wav"
ssh "$STEAM_HOST" "wsl cp /mnt/c/Users/Steam/run.sh /tmp/ninja-pipeline/run.sh"
ssh "$STEAM_HOST" "wsl chmod +x /tmp/ninja-pipeline/run.sh"

log "   Running Ditto Docker container..."
ssh "$STEAM_HOST" "wsl docker run --rm --gpus all --entrypoint bash \
    -v ${DITTO_CHECKPOINTS}:/app/ditto/checkpoints \
    -v ${AVATAR_PATH}:/data/input/source.jpg \
    -v /tmp/ninja-pipeline/audio.wav:/data/input/audio.wav \
    -v ${DITTO_OUTPUT}:/data/output \
    -v /tmp/ninja-pipeline/run.sh:/tmp/run.sh \
    ditto:latest /tmp/run.sh" 2>&1 | while IFS= read -r line; do
    log "   [Ditto] $line"
done

# Verify output was created
ssh "$STEAM_HOST" "wsl test -f ${DITTO_OUTPUT}/${REMOTE_OUTPUT_BASE}" \
    || die "Ditto output not found at ${DITTO_OUTPUT}/${REMOTE_OUTPUT_BASE}"

log "   ✅ Ditto video generated"

###############################################################################
# STEP 4: Retrieve result
###############################################################################
log "📦 Step 4/8: Retrieving video..."

# Copy from WSL to Windows
ssh "$STEAM_HOST" "wsl cp ${DITTO_OUTPUT}/${REMOTE_OUTPUT_BASE} /mnt/c/Users/Steam/${REMOTE_OUTPUT_BASE}"

# SCP from Windows to local
FINAL_OUTPUT="${LOCAL_OUTPUT_DIR}/${OUTPUT_NAME}"
scp -q "${STEAM_HOST}:C:/Users/Steam/${REMOTE_OUTPUT_BASE}" "$FINAL_OUTPUT"

# Verify
[[ -f "$FINAL_OUTPUT" ]] || die "Failed to retrieve output video"
FINAL_SIZE=$(stat -c%s "$FINAL_OUTPUT" 2>/dev/null || stat -f%z "$FINAL_OUTPUT")

# Quick ffprobe for video info
VIDEO_INFO=$(ffprobe -v quiet -show_entries format=duration:stream=width,height -of json "$FINAL_OUTPUT" 2>/dev/null || echo '{}')
VIDEO_DURATION=$(echo "$VIDEO_INFO" | python3 -c "import json,sys; d=json.load(sys.stdin); print(f\"{float(d.get('format',{}).get('duration',0)):.1f}s\")" 2>/dev/null || echo "unknown")

# Cleanup remote temp files
ssh "$STEAM_HOST" "wsl rm -rf /tmp/ninja-pipeline" 2>/dev/null || true
ssh "$STEAM_HOST" "del C:\\Users\\Steam\\audio.wav C:\\Users\\Steam\\run.sh C:\\Users\\Steam\\${REMOTE_OUTPUT_BASE}" 2>/dev/null || true

###############################################################################
# STEP 5: Background Compositing (optional)
###############################################################################
BG_STATUS="⏭️  skipped"
BG_SCRIPT="$(dirname "$0")/ninja_background.py"

if $NO_BG; then
    log "🎨 Step 5/8: Background compositing — skipped (--no-bg)"
elif [[ ! -f "$BG_SCRIPT" ]]; then
    log "🎨 Step 5/8: Background compositing — skipped (script not found)"
elif [[ -z "$BACKGROUND" && -z "$BG_STYLE" ]]; then
    log "🎨 Step 5/8: Background compositing — skipped (no --background or --bg-style)"
else
    log "🎨 Step 5/8: Compositing avatar over background..."

    PRE_BG="$WORK_DIR/pre_bg_$(basename "$FINAL_OUTPUT")"
    mv "$FINAL_OUTPUT" "$PRE_BG"

    BG_ARGS=(
        --input "$PRE_BG"
        --output "$FINAL_OUTPUT"
        --method "$BG_METHOD"
    )
    [[ -n "$BACKGROUND" ]] && BG_ARGS+=(--background "$BACKGROUND")
    [[ -n "$BG_STYLE" ]] && BG_ARGS+=(--bg-style "$BG_STYLE")

    if python3 "$BG_SCRIPT" "${BG_ARGS[@]}" 2>&1 | while IFS= read -r line; do
            log "   $line"
        done; then
        BG_STATUS="✅"
        log "   ✅ Background composited"
    else
        log "   ⚠️  Background compositing failed, using original"
        mv "$PRE_BG" "$FINAL_OUTPUT"
    fi
fi

###############################################################################
# STEP 6: Upscale to 1080×1920 (Shorts/Reels resolution)
###############################################################################
log "🔍 Step 6/8: Upscaling video to 1080×1920..."

UPSCALE_SCRIPT="$(dirname "$0")/ninja_upscale.py"
if [[ -f "$UPSCALE_SCRIPT" ]]; then
    PRESCALE="$WORK_DIR/prescale_$(basename "$FINAL_OUTPUT")"
    mv "$FINAL_OUTPUT" "$PRESCALE"

    if python3 "$UPSCALE_SCRIPT" \
        --input "$PRESCALE" \
        --output "$FINAL_OUTPUT" \
        --preset slow --crf 18 2>&1 | while IFS= read -r line; do
            log "   $line"
        done; then
        log "   ✅ Upscaled to 1080×1920"
    else
        log "   ⚠️  Upscaling failed, continuing with original resolution"
        mv "$PRESCALE" "$FINAL_OUTPUT"
    fi
else
    log "   ⚠️  Upscale script not found at $UPSCALE_SCRIPT, skipping"
fi

###############################################################################
# STEP 7: Burn captions into video
###############################################################################
log "📝 Step 7/8: Burning captions into video..."

CAPTION_SCRIPT="$(dirname "$0")/ninja_captions.py"
if [[ -f "$CAPTION_SCRIPT" ]]; then
    # Extract audio from the video for Whisper transcription
    CAPTION_AUDIO="$WORK_DIR/caption_audio.wav"
    ffmpeg -y -i "$FINAL_OUTPUT" -vn -ar 16000 -ac 1 "$CAPTION_AUDIO" 2>/dev/null

    UNCAPTIONED="$WORK_DIR/uncaptioned_$(basename "$FINAL_OUTPUT")"
    mv "$FINAL_OUTPUT" "$UNCAPTIONED"

    if python3 "$CAPTION_SCRIPT" \
        --audio "$CAPTION_AUDIO" \
        --video "$UNCAPTIONED" \
        --output "$FINAL_OUTPUT" 2>&1 | while IFS= read -r line; do
            log "   $line"
        done; then
        log "   ✅ Captions burned in"
    else
        log "   ⚠️  Captioning failed, using uncaptioned video"
        mv "$UNCAPTIONED" "$FINAL_OUTPUT"
    fi
else
    log "   ⚠️  Caption script not found at $CAPTION_SCRIPT, skipping"
fi

###############################################################################
# STEP 8: Add background music (optional)
###############################################################################
MUSIC_STATUS="⏭️  skipped"
MUSIC_SCRIPT="$(dirname "$0")/ninja_music.py"
MUSIC_DIR="$(dirname "$0")/../assets/music"

if $NO_MUSIC; then
    log "🎵 Step 8/8: Background music — skipped (--no-music)"
elif [[ ! -f "$MUSIC_SCRIPT" ]]; then
    log "🎵 Step 8/8: Background music — skipped (script not found)"
elif [[ -n "$MUSIC_FILE" && ! -f "$MUSIC_FILE" ]]; then
    log "🎵 Step 8/8: Background music — skipped (music file not found: $MUSIC_FILE)"
elif [[ -z "$MUSIC_FILE" ]] && ! ls "$MUSIC_DIR"/*.{mp3,wav,ogg,flac,m4a,aac,opus} >/dev/null 2>&1; then
    log "🎵 Step 8/8: Background music — skipped (no tracks in $MUSIC_DIR)"
else
    log "🎵 Step 8/8: Adding background music..."

    PRE_MUSIC="$WORK_DIR/pre_music_$(basename "$FINAL_OUTPUT")"
    mv "$FINAL_OUTPUT" "$PRE_MUSIC"

    MUSIC_ARGS=(
        --input "$PRE_MUSIC"
        --output "$FINAL_OUTPUT"
        --music-volume "$MUSIC_VOLUME"
    )
    [[ -n "$MUSIC_FILE" ]] && MUSIC_ARGS+=(--music "$MUSIC_FILE")
    [[ -n "$MUSIC_DIR" ]] && MUSIC_ARGS+=(--music-dir "$MUSIC_DIR")

    if python3 "$MUSIC_SCRIPT" "${MUSIC_ARGS[@]}" 2>&1 | while IFS= read -r line; do
            log "   $line"
        done; then
        MUSIC_STATUS="✅"
        log "   ✅ Background music added"
    else
        log "   ⚠️  Music mixing failed, using version without music"
        mv "$PRE_MUSIC" "$FINAL_OUTPUT"
    fi
fi

FINAL_SIZE=$(stat -c%s "$FINAL_OUTPUT" 2>/dev/null || stat -f%z "$FINAL_OUTPUT")

# Quick ffprobe for video info
VIDEO_INFO=$(ffprobe -v quiet -show_entries format=duration:stream=width,height -of json "$FINAL_OUTPUT" 2>/dev/null || echo '{}')
VIDEO_DURATION=$(echo "$VIDEO_INFO" | python3 -c "import json,sys; d=json.load(sys.stdin); print(f\"{float(d.get('format',{}).get('duration',0)):.1f}s\")" 2>/dev/null || echo "unknown")

log ""
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "🥷 Pipeline complete!"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "   Output:     $FINAL_OUTPUT"
log "   Size:       $(numfmt --to=iec $FINAL_SIZE 2>/dev/null || echo "${FINAL_SIZE} bytes")"
log "   Duration:   $VIDEO_DURATION"
log "   Background: $BG_STATUS"
log "   Captions:   ✅"
log "   Music:      $MUSIC_STATUS"
log ""

if $KEEP_INTERMEDIATES; then
    log "   Intermediates kept in: $WORK_DIR"
fi

echo "$FINAL_OUTPUT"
