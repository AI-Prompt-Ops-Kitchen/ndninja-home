#!/usr/bin/env python3
"""
ninja_content.py — Full content pipeline: News → Script → Video → Ready to Post

The Neurodivergent Ninja content factory.
Now with LIP-SYNC powered by fal.ai Kling Avatar v2!

Usage:
    # Full auto mode with lip-sync (DEFAULT)
    ninja-content --auto
    
    # Custom script with lip-sync
    ninja-content --script "Your script text here"
    
    # Use pro quality lip-sync ($0.115/sec vs $0.056/sec)
    ninja-content --script "..." --kling-model pro
    
    # Disable lip-sync (fall back to Veo looping)
    ninja-content --script "..." --no-lip-sync
    
    # Motion mode for masked characters (animated but no lip-sync)
    ninja-content --script "..." --motion
    
    # From script file
    ninja-content --script-file script.txt
    
    # With thumbnail and auto-publish
    ninja-content --auto --thumbnail --publish youtube
"""

import argparse
import json
import os
import subprocess
import sys
import time
import tempfile
import requests
import keyring
from pathlib import Path

# Normalize fal.ai env var names (Swarm uses FAL_KEY, fal_client expects FAL_KEY)
if os.environ.get('FAL_AI_API_KEY') and not os.environ.get('FAL_KEY'):
    os.environ['FAL_KEY'] = os.environ['FAL_AI_API_KEY']
elif os.environ.get('FAL_KEY') and not os.environ.get('FAL_AI_API_KEY'):
    os.environ['FAL_AI_API_KEY'] = os.environ['FAL_KEY']

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
ASSETS_DIR = PROJECT_DIR / "assets"
OUTPUT_DIR = PROJECT_DIR / "output"

# Character reference image
CHARACTER_IMAGE = ASSETS_DIR / "reference" / "ninja_pixar_user_example.mp4"  # Will extract frame
CHARACTER_IMAGE_STILL = ASSETS_DIR / "scenes" / "news_studio" / "ninja_concept.jpg"

# Config
DEFAULT_VOICE_ID = "aQspKon0UdKOuBZQQrEE"  # Neurodivergent Ninja Remix voice (use with eleven_v3)


def extract_topic_from_script(script_text: str) -> str:
    """Extract the actual topic/news from a script, skipping intro and outro."""
    lines = script_text.strip().split('\n')
    
    # Skip intro patterns (first 1-2 sentences usually)
    intro_patterns = [
        "what's up", "hey ninja", "fellow ninja", "neurodivergent ninja here",
        "back with another", "quick update", "let's dive", "welcome back"
    ]
    outro_patterns = [
        "thanks for watching", "like, follow", "subscribe", "signing off",
        "see you in", "next video", "don't forget to"
    ]
    
    # Find the content section (skip intro, stop before outro)
    content_sentences = []
    for line in lines:
        line_lower = line.lower()
        # Skip intro lines
        if any(p in line_lower for p in intro_patterns):
            continue
        # Stop at outro lines
        if any(p in line_lower for p in outro_patterns):
            break
        if line.strip():
            content_sentences.append(line.strip())
    
    # Get the first meaningful content sentence (the topic)
    if content_sentences:
        # Take first 1-2 sentences that describe the news
        topic = ' '.join(content_sentences[:2])
        # Limit length but keep it descriptive
        if len(topic) > 150:
            topic = topic[:150].rsplit(' ', 1)[0] + '...'
        return topic
    
    # Fallback: use middle portion of script
    return script_text[100:250] if len(script_text) > 250 else script_text


def identify_broll_moments(script_text, audio_duration, num_moments=3, clip_duration=4.0):
    """Use Gemini Flash to identify hype moments in the script for B-roll insertion.

    Returns: [{"timestamp": 12.5, "duration": 4.0, "topic": "Nioh 3"}, ...]
    """
    print(f"   🧠 Identifying {num_moments} B-roll moments in script...")

    min_gap = 8.0       # Minimum seconds between cuts
    pad = 3.0            # No cuts in first/last 3s
    usable = audio_duration - 2 * pad

    if usable < min_gap:
        print("   ⚠️ Audio too short for B-roll")
        return []

    # Clamp num_moments to what fits
    max_possible = max(1, int(usable / min_gap))
    num_moments = min(num_moments, max_possible)

    try:
        from google import genai
        from google.genai import types

        project = os.environ.get('GOOGLE_CLOUD_PROJECT', 'gen-lang-client-0601509945')
        location = os.environ.get('GOOGLE_CLOUD_LOCATION', 'us-central1')
        client = genai.Client(vertexai=True, project=project, location=location)

        prompt = f"""Analyze this video script and identify the {num_moments} most visually exciting moments —
the sentences where game footage or action shots would have the most impact.

Script:
{script_text}

For each moment, return a JSON array of objects with:
- "sentence": the exact sentence or phrase from the script
- "topic": the game or subject name (1-4 words, e.g. "Nioh 3", "Avowed")
- "position": what fraction through the script this sentence appears (0.0 to 1.0)

Rules:
- Pick moments that describe ACTION or VISUALS (trailers, gameplay, reveals)
- Avoid intro/outro lines
- Spread them out across the script
- Return ONLY valid JSON array, no other text

JSON:"""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=500,
            )
        )

        # Parse LLM response
        import re
        text = response.text.strip()
        # Extract JSON array from response
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            raw_moments = json.loads(match.group())
        else:
            raise ValueError("No JSON array in response")

        # Convert position fractions to timestamps
        moments = []
        for m in raw_moments[:num_moments]:
            pos = float(m.get("position", 0.5))
            ts = pad + pos * usable
            moments.append({
                "timestamp": round(ts, 2),
                "duration": clip_duration,
                "topic": m.get("topic", ""),
                "sentence": m.get("sentence", ""),
            })

        # Enforce min_gap: remove moments too close together
        moments.sort(key=lambda x: x["timestamp"])
        filtered = []
        for m in moments:
            if not filtered or (m["timestamp"] - filtered[-1]["timestamp"]) >= min_gap:
                # Also ensure B-roll doesn't extend past end
                if m["timestamp"] + m["duration"] <= audio_duration - 1.0:
                    filtered.append(m)

        if filtered:
            print(f"   ✅ Found {len(filtered)} moments: {[f'{m['topic']}@{m['timestamp']:.1f}s' for m in filtered]}")
            return filtered

    except Exception as e:
        print(f"   ⚠️ LLM moment detection failed ({e}), using even distribution...")

    # Fallback: evenly distribute cuts
    # Use generic topics so resolve_broll_clips can still assign clips via fuzzy match
    fallback_topics = ["gameplay", "action", "combat", "game"]
    interval = usable / (num_moments + 1)
    moments = []
    for i in range(num_moments):
        ts = pad + interval * (i + 1)
        if ts + clip_duration <= audio_duration - 1.0:
            moments.append({
                "timestamp": round(ts, 2),
                "duration": clip_duration,
                "topic": fallback_topics[i % len(fallback_topics)],
                "sentence": "",
            })

    print(f"   📍 Fallback: {len(moments)} evenly spaced moments")
    return moments


def resolve_broll_clips(moments, broll_dir=None, broll_map=None):
    """Find video files for each moment's topic.

    Priority: explicit broll_map → scan broll_dir filenames → BROLL_MAP from longform → skip
    Adds 'clip_path' to each moment dict. Skips moments with no match.
    """
    print("   🔍 Resolving B-roll clips...")

    # Build lookup from explicit map (e.g. {"nioh": "nioh3.mp4"})
    explicit_map = {}
    if broll_map:
        for entry in broll_map:
            if ':' in entry:
                key, val = entry.split(':', 1)
                explicit_map[key.strip().lower()] = val.strip()

    # Try to import BROLL_MAP from longform as fallback
    longform_map = {}
    try:
        from ninja_longform import BROLL_MAP
        longform_map = {k.lower(): v for k, v in BROLL_MAP.items()}
    except ImportError:
        pass

    # Scan broll_dir for available files
    dir_files = {}
    if broll_dir and Path(broll_dir).is_dir():
        for f in Path(broll_dir).iterdir():
            if f.suffix.lower() in ('.mp4', '.mov', '.webm'):
                dir_files[f.stem.lower()] = str(f)

    for m in moments:
        topic = m.get("topic", "").lower()
        if not topic:
            continue

        # 1. Explicit map
        for key, filename in explicit_map.items():
            if key in topic or topic in key:
                path = Path(filename) if Path(filename).is_absolute() else Path(broll_dir or '.') / filename
                if path.exists():
                    m["clip_path"] = str(path)
                    break

        if "clip_path" in m:
            continue

        # 2. Scan broll_dir filenames
        for stem, filepath in dir_files.items():
            # Fuzzy: check if topic words appear in filename or vice versa
            topic_words = topic.split()
            if any(w in stem for w in topic_words) or any(stem_part in topic for stem_part in stem.split('_')):
                m["clip_path"] = filepath
                break

        if "clip_path" in m:
            continue

        # 3. Longform BROLL_MAP
        for key, filename in longform_map.items():
            if any(w in key for w in topic.split()) or any(w in topic for w in key.split()):
                path = Path(broll_dir or '.') / filename if broll_dir else Path(filename)
                if path.exists():
                    m["clip_path"] = str(path)
                    break

    resolved = [m for m in moments if "clip_path" in m]

    # Last resort: round-robin assign available clips to any unmatched moments
    if len(resolved) < len(moments) and dir_files:
        all_clips = list(dir_files.values())
        clip_idx = 0
        for m in moments:
            if "clip_path" not in m:
                m["clip_path"] = all_clips[clip_idx % len(all_clips)]
                clip_idx += 1
        resolved = [m for m in moments if "clip_path" in m]
        print(f"   🔄 Round-robin assigned remaining: {len(resolved)}/{len(moments)} total")

    print(f"   ✅ Resolved {len(resolved)}/{len(moments)} clips: {[m['topic'] for m in resolved]}")
    return moments


def assemble_with_broll(avatar_video, moments, output_path, crossfade=0.15):
    """Cut avatar video at B-roll timestamps and splice in B-roll clips.

    Audio plays continuously from the original avatar video over everything.
    B-roll replaces avatar frames (doesn't add time).
    """
    print(f"🎬 Assembling video with {len(moments)} B-roll cutaways...")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # 1. Extract audio from avatar video (plays continuously over everything)
        audio_file = tmpdir / "audio.wav"
        subprocess.run([
            "ffmpeg", "-y", "-i", avatar_video,
            "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
            str(audio_file)
        ], capture_output=True)

        # Get avatar video dimensions and fps
        probe = subprocess.run([
            "ffprobe", "-v", "quiet", "-select_streams", "v:0",
            "-show_entries", "stream=width,height,r_frame_rate",
            "-of", "csv=p=0", avatar_video
        ], capture_output=True, text=True)
        parts = probe.stdout.strip().split(',')
        width, height = int(parts[0]), int(parts[1])

        # 2. Build segment list: avatar → broll → avatar → broll → avatar
        segments = []
        prev_end = 0.0

        for i, m in enumerate(moments):
            ts = m["timestamp"]
            dur = m["duration"]
            clip_path = m["clip_path"]

            # Avatar segment before this B-roll
            if ts > prev_end:
                seg_file = tmpdir / f"avatar_{i}.mp4"
                subprocess.run([
                    "ffmpeg", "-y", "-i", avatar_video,
                    "-ss", str(prev_end),
                    "-t", str(ts - prev_end),
                    "-c:v", "libx264", "-crf", "18", "-preset", "fast",
                    "-an", str(seg_file)
                ], capture_output=True)
                if seg_file.exists() and seg_file.stat().st_size > 0:
                    segments.append(str(seg_file))

            # B-roll segment (scaled to match avatar dimensions)
            broll_file = tmpdir / f"broll_{i}.mp4"
            if height > width:
                # Portrait/Shorts — scale to cover then center-crop to fill frame
                broll_vf = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},fps=30"
            else:
                # Landscape — scale+pad (preserve letterbox)
                broll_vf = f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:-1:-1,fps=30"
            subprocess.run([
                "ffmpeg", "-y", "-i", clip_path,
                "-t", str(dur),
                "-vf", broll_vf,
                "-c:v", "libx264", "-crf", "18", "-preset", "fast",
                "-an", str(broll_file)
            ], capture_output=True)
            if broll_file.exists() and broll_file.stat().st_size > 0:
                segments.append(str(broll_file))

            prev_end = ts + dur

        # Final avatar segment after last B-roll
        avatar_dur = float(subprocess.run([
            "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
            "-of", "csv=p=0", avatar_video
        ], capture_output=True, text=True).stdout.strip())

        if prev_end < avatar_dur:
            final_seg = tmpdir / "avatar_final.mp4"
            subprocess.run([
                "ffmpeg", "-y", "-i", avatar_video,
                "-ss", str(prev_end),
                "-c:v", "libx264", "-crf", "18", "-preset", "fast",
                "-an", str(final_seg)
            ], capture_output=True)
            if final_seg.exists() and final_seg.stat().st_size > 0:
                segments.append(str(final_seg))

        if not segments:
            print("   ❌ No segments created")
            return False

        # 3. Write concat list
        concat_file = tmpdir / "concat.txt"
        with open(concat_file, "w") as f:
            for seg in segments:
                f.write(f"file '{seg}'\n")

        # 4. Concatenate video segments (video only)
        video_only = tmpdir / "video_only.mp4"
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_file),
            "-c:v", "libx264", "-crf", "18", "-preset", "fast",
            "-an", str(video_only)
        ], capture_output=True)

        if not video_only.exists():
            print("   ❌ Video concatenation failed")
            return False

        # 5. Mux original continuous audio back on
        subprocess.run([
            "ffmpeg", "-y",
            "-i", str(video_only),
            "-i", str(audio_file),
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-map", "0:v:0", "-map", "1:a:0",
            "-shortest",
            output_path
        ], capture_output=True)

        if Path(output_path).exists():
            final_dur = float(subprocess.run([
                "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                "-of", "csv=p=0", output_path
            ], capture_output=True, text=True).stdout.strip())
            print(f"   ✅ Assembled: {output_path} ({final_dur:.1f}s)")
            return True

        print("   ❌ Final mux failed")
        return False


def get_api_keys():
    """Load API keys from environment or config files."""
    keys = {}
    
    # Google/Veo
    keys['google'] = os.environ.get('GOOGLE_API_KEY')
    
    # ElevenLabs
    keys['elevenlabs'] = os.environ.get('ELEVENLABS_API_KEY', '')
    if not keys['elevenlabs']:
        env_file = Path("/home/ndninja/projects/content-automation/.env")
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    if line.startswith('ELEVENLABS_API_KEY='):
                        keys['elevenlabs'] = line.strip().split('=', 1)[1].strip('"\'')
                        break
    
    return keys


def discover_news(category="tech"):
    """Discover latest news stories."""
    print("📰 Discovering latest news...")
    result = subprocess.run([
        sys.executable, str(SCRIPT_DIR / "ninja_scriptgen.py"),
        "--discover", "--category", category
    ], capture_output=True, text=True)
    print(result.stdout)
    
    # Load discovered stories
    stories_file = Path("/tmp/ninja_discovered_stories.json")
    if stories_file.exists():
        with open(stories_file) as f:
            return json.load(f)
    return []


def generate_script(story_index=None, topic=None, auto=False):
    """Generate a ninja script from news or topic."""
    args = [sys.executable, str(SCRIPT_DIR / "ninja_scriptgen.py")]
    
    if auto:
        args.append("--auto")
    elif story_index:
        args.extend(["--pick", str(story_index)])
    elif topic:
        args.extend(["--topic", topic])
    
    args.extend(["--output", "/tmp/ninja_script.json"])
    
    result = subprocess.run(args, capture_output=True, text=True)
    print(result.stdout)
    
    # Load generated script
    script_file = Path("/tmp/ninja_latest_script.txt")
    if script_file.exists():
        return script_file.read_text().strip()
    return None


def inject_expressive_tags(script_text):
    """Inject ElevenLabs v3 audio tags into script for natural expressive delivery.

    Audio tags are the primary expressiveness mechanism for eleven_v3.
    Tags like [excited], [laughs], [whispering] are interpreted as performance
    directions — they're not spoken aloud.

    Adds tags at key points:
    - Intro gets [excited] for energy
    - Hype/reveal moments get [excited]
    - Sign-offs get [excited] for warm energy
    - Surprise/shock moments get [gasps]

    Skips injection if tags are already present in the script.
    """
    # Don't double-tag if user already added tags
    known_tags = {"[excited]", "[laughs]", "[whispers]", "[whispering]", "[sighs]",
                  "[slow]", "[gasps]", "[calm]", "[sad]", "[angry]", "[curious]",
                  "[nervous]", "[sarcastic]", "[pause]"}
    if any(tag in script_text.lower() for tag in known_tags):
        return script_text

    lines = script_text.strip().split('\n')
    tagged_lines = []

    for i, line in enumerate(lines):
        lower = line.lower().strip()
        if not lower:
            tagged_lines.append(line)
            continue

        # Intro line — add excited energy
        if any(p in lower for p in ["what's up", "hey ninja", "fellow ninja", "back with another"]):
            tagged_lines.append(f"[excited] {line.strip()}")
        # Outro / sign-off — warm send-off
        elif any(p in lower for p in ["thanks for watching", "peace out", "see you next"]):
            tagged_lines.append(f"[excited] {line.strip()}")
        # Hype / reveal moments
        elif any(p in lower for p in ["just dropped", "just announced", "game changer",
                                       "huge news", "breaking", "finally", "revealed",
                                       "number one", "the winner"]):
            tagged_lines.append(f"[excited] {line.strip()}")
        else:
            tagged_lines.append(line)

    return '\n'.join(tagged_lines)


def generate_tts(script_text, output_path, voice_id=DEFAULT_VOICE_ID, pad_start=0.5,
                 voice_style="expressive"):
    """Generate TTS audio using ElevenLabs with Expressive Mode support.

    Args:
        voice_style: Expressiveness preset:
            "expressive" (default) - High energy, emotional range (style=0.8, stability=0.3)
            "natural"   - Balanced delivery (style=0.5, stability=0.5)
            "calm"      - Steady, controlled (style=0.3, stability=0.7)
    """
    # Voice style presets for eleven_v3
    # NOTE: v3 only accepts stability 0.0 / 0.5 / 1.0 and does NOT support 'style' param
    # Expressiveness is driven by audio tags ([excited], [laughs], etc.) not settings knobs
    # Higher similarity_boost preserves voice identity when using Creative stability
    VOICE_STYLES = {
        "expressive": {"stability": 0.0, "similarity_boost": 0.85},
        "natural":    {"stability": 0.5, "similarity_boost": 0.80},
        "calm":       {"stability": 1.0, "similarity_boost": 0.75},
    }
    voice_settings = VOICE_STYLES.get(voice_style, VOICE_STYLES["expressive"])

    print(f"🎙️ Generating voice audio (style: {voice_style})...")
    print(f"   Settings: stability={voice_settings['stability']}, similarity_boost={voice_settings['similarity_boost']}")

    # Inject expressive audio tags for emotional delivery
    tagged_text = inject_expressive_tags(script_text)
    if tagged_text != script_text:
        print("   🎭 Injected expressive audio tags")

    keys = get_api_keys()
    if not keys['elevenlabs']:
        print("   ❌ ElevenLabs API key not found")
        return None

    response = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={
            "xi-api-key": keys['elevenlabs'],
            "Content-Type": "application/json"
        },
        json={
            "text": tagged_text,
            "model_id": "eleven_v3",
            "voice_settings": voice_settings
        }
    )
    
    if response.status_code == 200:
        # Save raw audio first
        raw_path = output_path + ".raw.mp3"
        with open(raw_path, "wb") as f:
            f.write(response.content)
        
        # Step 1: Trim excessive silences (shorten gaps >0.6s down to 0.3s)
        compressed_path = output_path + ".compressed.mp3"
        print(f"   🔇 Trimming long pauses (>0.6s → 0.3s)...")
        # Use silenceremove to strip only the excess portion of long silences
        # Keep natural breathing room but cut dead air
        subprocess.run([
            "ffmpeg", "-y",
            "-i", raw_path,
            "-af", (
                "silenceremove="
                "stop_periods=-1:"
                "stop_duration=0.6:"       # Only touch silences longer than 0.6s
                "stop_threshold=-35dB:"    # Conservative threshold
                "stop_silence=0.3"         # Leave 0.3s of silence in place
            ),
            "-c:a", "libmp3lame", "-q:a", "2",
            compressed_path
        ], capture_output=True)
        
        # Step 2: Add padding at start to prevent first word cutoff
        source = compressed_path if os.path.exists(compressed_path) else raw_path
        if pad_start > 0:
            print(f"   🔇 Adding {pad_start}s padding at start...")
            delay_ms = int(pad_start * 1000)
            subprocess.run([
                "ffmpeg", "-y",
                "-i", source,
                "-af", f"adelay={delay_ms}|{delay_ms},apad=pad_dur={pad_start}",
                "-c:a", "libmp3lame", "-q:a", "2",
                output_path
            ], capture_output=True)
        else:
            os.rename(source, output_path)
        
        # Cleanup temp files
        for tmp in [raw_path, compressed_path]:
            if os.path.exists(tmp) and tmp != output_path:
                os.remove(tmp)
        
        size = os.path.getsize(output_path)
        print(f"   ✅ Audio saved: {output_path} ({size/1024:.0f}KB)")
        return output_path
    else:
        print(f"   ❌ TTS failed: {response.status_code}")
        print(f"   {response.text[:200]}")
        return None


def get_audio_duration(audio_path):
    """Get duration of audio file in seconds."""
    result = subprocess.run([
        "ffprobe", "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "csv=p=0", audio_path
    ], capture_output=True, text=True)
    return float(result.stdout.strip())


def generate_kling_avatar_video(image_path, audio_path, output_path, model="standard"):
    """Generate lip-synced video using fal.ai Kling Avatar v2.
    
    Args:
        image_path: Path to character image
        audio_path: Path to audio file (voice)
        output_path: Where to save the generated video
        model: "standard" ($0.056/sec) or "pro" ($0.115/sec, higher quality)
    
    Returns:
        output_path on success, None on failure
    """
    print("🎬 Generating lip-synced video with Kling Avatar v2...")
    
    # Get fal.ai API key from environment or keyring
    fal_key = os.environ.get('FAL_AI_API_KEY')
    if not fal_key:
        # Try .env file
        env_file = Path("/home/ndninja/projects/content-automation/.env")
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    if line.startswith('FAL_AI_API_KEY='):
                        fal_key = line.strip().split('=', 1)[1].strip('"\'')
                        break
    if not fal_key:
        try:
            fal_key = keyring.get_password("fal_ai", "api_key")
        except:
            pass
    if not fal_key:
        print("   ❌ fal.ai API key not found")
        print("   Set FAL_AI_API_KEY environment variable or add to .env")
        return None
    
    os.environ["FAL_KEY"] = fal_key
    
    try:
        import fal_client
    except ImportError:
        print("   ❌ fal_client not installed. Run: pip install fal-client")
        return None
    
    # Upload image
    print(f"   📤 Uploading image: {image_path}")
    with open(image_path, "rb") as f:
        image_data = f.read()
    image_url = fal_client.upload(image_data, "image/jpeg")
    
    # Upload audio
    print(f"   📤 Uploading audio: {audio_path}")
    with open(audio_path, "rb") as f:
        audio_data = f.read()
    audio_url = fal_client.upload(audio_data, "audio/mpeg")
    
    # Select model
    model_id = f"fal-ai/kling-video/ai-avatar/v2/{model}"
    print(f"   🎭 Model: {model_id}")
    print(f"   ⏳ Generating (typically 2-5 min)...")
    
    start_time = time.time()
    
    try:
        result = fal_client.subscribe(
            model_id,
            arguments={
                "image_url": image_url,
                "audio_url": audio_url,
                "prompt": "Static camera, stable framing. Professional news anchor presenting directly to camera. Subtle head movements with natural nodding, maintain consistent eye contact. No camera movement or zoom."
            },
            with_logs=True
        )
    except Exception as e:
        print(f"   ❌ Kling Avatar failed: {e}")
        return None
    
    elapsed = time.time() - start_time
    duration = result.get("duration", "N/A")
    print(f"   ✅ Generated in {elapsed:.1f}s (video: {duration}s)")
    
    # Download video
    video_url = result.get("video", {}).get("url")
    if not video_url:
        print(f"   ❌ No video URL in response: {result}")
        return None
    
    print(f"   📥 Downloading video...")
    r = requests.get(video_url)
    with open(output_path, "wb") as f:
        f.write(r.content)
    
    size = os.path.getsize(output_path)
    print(f"   ✅ Video saved: {output_path} ({size/1024/1024:.1f}MB)")
    
    return output_path


def generate_veo_video(prompt, duration_seconds, output_path, reference_image=None, use_vertex=True):
    """Generate video using Veo (Vertex AI by default for higher rate limits)."""
    print("🎬 Generating video with Veo...")
    
    from google import genai
    from google.genai import types
    
    if use_vertex:
        # Vertex AI - higher rate limits
        client = genai.Client(
            vertexai=True,
            project="gen-lang-client-0601509945",
            location="us-central1"
        )
        print("   🔧 Using Vertex AI")
    else:
        keys = get_api_keys()
        client = genai.Client(api_key=keys['google'])
        print("   🔧 Using AI Studio")
    
    # Cap duration at 8 seconds (Veo limit), we'll loop if needed
    veo_duration = min(duration_seconds, 8)
    
    config = types.GenerateVideosConfig(
        aspect_ratio="9:16",
        duration_seconds=int(veo_duration),
    )
    
    # Use reference image if provided
    image = None
    if reference_image and Path(reference_image).exists():
        print(f"   📸 Using reference image: {reference_image}")
        with open(reference_image, "rb") as f:
            image_bytes = f.read()
        image = types.Image(image_bytes=image_bytes, mime_type="image/jpeg")
    
    try:
        if image:
            op = client.models.generate_videos(
                model="veo-3.1-generate-preview",
                prompt=prompt,
                image=image,
                config=config,
            )
        else:
            op = client.models.generate_videos(
                model="veo-3.1-generate-preview",
                prompt=prompt,
                config=config,
            )
        
        print(f"   Operation: {op.name}")
        
        while not op.done:
            print("   ⏳ Generating...")
            time.sleep(15)
            op = client.operations.get(op)
        
        if op.result and op.result.generated_videos:
            video = op.result.generated_videos[0]
            
            # Handle both AI Studio and Vertex AI response formats
            if hasattr(video, 'video') and video.video:
                if hasattr(video.video, 'uri') and video.video.uri:
                    # AI Studio format
                    file_uri = video.video.uri.replace(":download?alt=media", "")
                    keys = get_api_keys()
                    response = requests.get(
                        f"{file_uri}:download",
                        params={"key": keys['google'], "alt": "media"},
                        stream=True
                    )
                elif hasattr(video.video, 'video_bytes') and video.video.video_bytes:
                    # Vertex AI format - direct bytes
                    with open(output_path, "wb") as f:
                        f.write(video.video.video_bytes)
                    size = os.path.getsize(output_path)
                    print(f"   ✅ Video saved: {output_path} ({size/1024:.0f}KB)")
                    return output_path
                else:
                    print(f"   ❌ Unknown video format: {dir(video.video)}")
                    return None
            else:
                print(f"   ❌ No video in response: {dir(video)}")
                return None
            
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                size = os.path.getsize(output_path)
                print(f"   ✅ Video saved: {output_path} ({size/1024:.0f}KB)")
                return output_path
        
        print("   ❌ No video generated")
        return None
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


def loop_video_to_duration(video_path, target_duration, output_path, crossfade_duration=0):
    """Loop video to match target duration with crossfade at loop points (strips Veo AI audio)."""
    print(f"🔁 Looping video to {target_duration:.1f}s with {crossfade_duration}s crossfade...")
    
    # Get video duration
    result = subprocess.run([
        "ffprobe", "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "csv=p=0", video_path
    ], capture_output=True, text=True)
    video_duration = float(result.stdout.strip())
    
    if video_duration >= target_duration:
        # Just trim (strip audio)
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path,
            "-t", str(target_duration),
            "-c:v", "copy", "-an",  # Strip audio
            output_path
        ], capture_output=True)
    else:
        # Calculate loops needed (accounting for crossfade overlap)
        effective_duration = video_duration - crossfade_duration
        loops_needed = int((target_duration - video_duration) / effective_duration) + 2
        
        if loops_needed <= 1 or crossfade_duration == 0:
            # Simple loop without crossfade
            subprocess.run([
                "ffmpeg", "-y",
                "-stream_loop", str(loops_needed),
                "-i", video_path,
                "-t", str(target_duration),
                "-c:v", "libx264", "-crf", "18", "-an",
                output_path
            ], capture_output=True)
        else:
            # Build xfade filter chain for seamless loops
            inputs = []
            for i in range(loops_needed):
                inputs.extend(["-i", video_path])
            
            # Build xfade chain: [0][1]xfade -> [v1], [v1][2]xfade -> [v2], etc.
            filter_parts = []
            offset = video_duration - crossfade_duration
            
            for i in range(loops_needed - 1):
                if i == 0:
                    in1, in2 = "[0:v]", "[1:v]"
                else:
                    in1 = f"[v{i}]"
                    in2 = f"[{i+1}:v]"
                
                if i == loops_needed - 2:
                    out = "[outv]"
                else:
                    out = f"[v{i+1}]"
                
                current_offset = offset * (i + 1)
                filter_parts.append(f"{in1}{in2}xfade=transition=fade:duration={crossfade_duration}:offset={current_offset}{out}")
            
            filter_complex = ";".join(filter_parts)
            
            cmd = [
                "ffmpeg", "-y",
                *inputs,
                "-filter_complex", filter_complex,
                "-map", "[outv]",
                "-t", str(target_duration),
                "-c:v", "libx264", "-crf", "18",
                output_path
            ]
            subprocess.run(cmd, capture_output=True)
    
    print(f"   ✅ Looped video: {output_path}")
    return output_path


def combine_video_audio(video_path, audio_path, output_path):
    """Combine video and audio, adjusting to match durations."""
    print("🔗 Combining video + audio...")
    
    video_dur = float(subprocess.run([
        "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
        "-of", "csv=p=0", video_path
    ], capture_output=True, text=True).stdout.strip())
    
    audio_dur = get_audio_duration(audio_path)
    
    print(f"   Video: {video_dur:.1f}s, Audio: {audio_dur:.1f}s")
    
    # Speed up/slow down audio slightly to match video if close
    tempo = audio_dur / video_dur
    if 0.8 <= tempo <= 1.5:
        # Adjust audio tempo
        subprocess.run([
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-filter_complex", f"[1:a]atempo={tempo}[a]",
            "-map", "0:v", "-map", "[a]",
            "-c:v", "copy", "-c:a", "aac",
            "-shortest", output_path
        ], capture_output=True)
    else:
        # Just use shortest
        subprocess.run([
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-map", "0:v", "-map", "1:a",
            "-c:v", "copy", "-c:a", "aac",
            "-shortest", output_path
        ], capture_output=True)
    
    print(f"   ✅ Combined: {output_path}")
    return output_path


def burn_captions(video_path, script_text, output_path, audio_path=None, style="animated"):
    """Burn animated Instagram-style captions into video using Whisper word sync."""
    print(f"📝 Burning {style} captions...")
    
    # Prefer Whisper-synced captions for accurate word-by-word highlighting
    if audio_path:
        try:
            from ninja_synced_captions import burn_synced_captions
            print("   🎙️ Using Whisper word-sync for accurate timing...")
            # Pass original script to avoid transcription errors (e.g., 'Genie' -> 'G & E')
            burn_synced_captions(video_path, audio_path, output_path, model_size="tiny", original_script=script_text)
            print(f"   ✅ Synced captions burned: {output_path}")
            return output_path
        except Exception as e:
            print(f"   ⚠️ Whisper sync failed ({e}), falling back to estimated timing...")
    
    # Fallback: Use estimated timing (ninja_captions)
    try:
        from ninja_captions import generate_ass_captions, burn_ass_captions
        
        # Get video duration
        duration = float(subprocess.run([
            "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
            "-of", "csv=p=0", video_path
        ], capture_output=True, text=True).stdout.strip())
        
        # Generate ASS captions
        ass_path = "/tmp/ninja_captions.ass"
        generate_ass_captions(script_text, duration, ass_path, style)
        
        # Burn into video
        burn_ass_captions(video_path, ass_path, output_path)
        print(f"   ✅ Animated captions burned: {output_path}")
        return output_path
        
    except ImportError:
        # Fallback to simple SRT if module not available
        print("   ⚠️ Falling back to simple captions...")
        srt_path = "/tmp/captions.srt"
        
        duration = float(subprocess.run([
            "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
            "-of", "csv=p=0", video_path
        ], capture_output=True, text=True).stdout.strip())
        
        words = script_text.split()
        chunks = []
        chunk_size = 5
        for i in range(0, len(words), chunk_size):
            chunks.append(" ".join(words[i:i+chunk_size]))
        
        time_per_chunk = duration / len(chunks)
        with open(srt_path, "w") as f:
            for i, chunk in enumerate(chunks):
                start = i * time_per_chunk
                end = (i + 1) * time_per_chunk
                f.write(f"{i+1}\n")
                f.write(f"{format_srt_time(start)} --> {format_srt_time(end)}\n")
                f.write(f"{chunk}\n\n")
        
        subprocess.run([
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", f"subtitles={srt_path}:force_style='FontSize=24,FontName=Arial,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=2,Alignment=2'",
            "-c:a", "copy",
            output_path
        ], capture_output=True)
        
        print(f"   ✅ Captions burned: {output_path}")
        return output_path


def format_srt_time(seconds):
    """Format seconds as SRT timestamp."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def add_background_music(video_path, output_path, music_volume=0.1):
    """Add background music (if available)."""
    music_dir = ASSETS_DIR / "music"
    if not music_dir.exists():
        print("🎵 No music directory found, skipping...")
        subprocess.run(["cp", video_path, output_path])
        return output_path
    
    # Find a music file
    music_files = list(music_dir.glob("*.mp3")) + list(music_dir.glob("*.wav"))
    if not music_files:
        print("🎵 No music files found, skipping...")
        subprocess.run(["cp", video_path, output_path])
        return output_path
    
    music_file = music_files[0]
    print(f"🎵 Adding background music: {music_file.name}")
    
    subprocess.run([
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", str(music_file),
        "-filter_complex", f"[1:a]volume={music_volume}[music];[0:a][music]amix=inputs=2:duration=first[a]",
        "-map", "0:v", "-map", "[a]",
        "-c:v", "copy", "-c:a", "aac",
        "-shortest", output_path
    ], capture_output=True)
    
    print(f"   ✅ Music added: {output_path}")
    return output_path


def generate_capcut_draft(video_path, audio_path, broll_clips, captions_srt, output_name):
    """Generate a CapCut draft for manual editing."""
    import requests
    
    CAPCUT_API = "http://127.0.0.1:9000"
    
    def api_call(endpoint, data):
        try:
            r = requests.post(f"{CAPCUT_API}/{endpoint}", json=data, timeout=60)
            return r.json()
        except Exception as e:
            print(f"   ❌ API error: {e}")
            return {"success": False, "error": str(e)}
    
    # Check server
    try:
        requests.get(f"{CAPCUT_API}/", timeout=3)
    except:
        print("   ❌ CapCut API server not running!")
        print("   Start with: cd /home/ndninja/projects/capcut-api && source venv/bin/activate && python capcut_server.py &")
        return None
    
    print("📋 Creating CapCut draft...")
    
    # Create draft
    result = api_call("create_draft", {"width": 1080, "height": 1920, "name": output_name})
    if not result.get("success"):
        print(f"   ❌ Failed to create draft: {result.get('error')}")
        return None
    
    # draft_id is in the output dict
    output = result.get("output", {})
    draft_id = output.get("draft_id") if isinstance(output, dict) else None
    if not draft_id:
        print(f"   ❌ No draft_id in response: {result}")
        return None
    print(f"   Draft ID: {draft_id}")
    
    # Get durations
    audio_duration = float(subprocess.run([
        "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
        "-of", "csv=p=0", audio_path
    ], capture_output=True, text=True).stdout.strip())
    
    video_duration = float(subprocess.run([
        "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
        "-of", "csv=p=0", video_path
    ], capture_output=True, text=True).stdout.strip())
    
    # Add main video track (loop if needed)
    print("🎥 Adding video track...")
    video_path = str(Path(video_path).resolve())
    num_loops = int(audio_duration / video_duration) + 1
    current_time = 0
    
    for i in range(num_loops):
        segment_dur = min(video_duration, audio_duration - current_time)
        if segment_dur <= 0:
            break
        
        api_call("add_video", {
            "draft_id": draft_id,
            "video_url": f"file://{video_path}",
            "start": 0,
            "end": segment_dur,
            "target_start": current_time,
            "volume": 0,
            "transition": "Fade" if i > 0 else None,
            "transition_duration": 0.5 if i > 0 else 0,
            "track_name": "main_video"
        })
        current_time += segment_dur
    
    # Add B-roll clips
    if broll_clips:
        print(f"🎬 Adding {len(broll_clips)} B-roll clips...")
        interval = audio_duration / (len(broll_clips) + 1)
        for i, broll_path in enumerate(broll_clips):
            insert_time = interval * (i + 1)
            broll_path = str(Path(broll_path).resolve())
            broll_dur = min(4, float(subprocess.run([
                "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                "-of", "csv=p=0", broll_path
            ], capture_output=True, text=True).stdout.strip()))
            
            api_call("add_video", {
                "draft_id": draft_id,
                "video_url": f"file://{broll_path}",
                "start": 0,
                "end": broll_dur,
                "target_start": insert_time,
                "volume": 0,
                "transition": "Fade",
                "transition_duration": 0.3,
                "track_name": f"broll_{i+1}"
            })
    
    # Add audio
    print("🔊 Adding audio track...")
    audio_path = str(Path(audio_path).resolve())
    api_call("add_audio", {
        "draft_id": draft_id,
        "audio_url": f"file://{audio_path}",
        "start": 0,
        "end": audio_duration,
        "target_start": 0,
        "volume": 1.0,
        "track_name": "voice"
    })
    
    # Add subtitles
    if captions_srt and Path(captions_srt).exists():
        print("📝 Adding captions...")
        captions_srt = str(Path(captions_srt).resolve())
        api_call("add_subtitle", {
            "draft_id": draft_id,
            "subtitle_url": f"file://{captions_srt}",
            "font_size": 42,
            "font_color": "#FFFFFF"
        })
    
    # Save draft
    print("💾 Saving draft...")
    result = api_call("save_draft", {"draft_id": draft_id})
    
    # Handle different response formats
    output = result.get("output", {})
    if isinstance(output, dict):
        draft_url = output.get("draft_url", "")
    else:
        draft_url = ""
    
    print(f"\n✅ CapCut draft created!")
    print(f"   Draft ID: {draft_id}")
    if draft_url:
        print(f"   Preview: {draft_url}")
    print(f"\n   Open in CapCut to review and export!")
    
    return draft_id


def run_pipeline(script_text, reference_image=None, output_name="ninja_content", multiclip=False, no_music=False, no_captions=True, broll=False, capcut=False, lip_sync=True, kenburns=False, motion=False, kling_model="standard", broll_dir=None, broll_map=None, broll_count=3, broll_duration=4.0, voice_style="expressive"):
    """Run the full content pipeline.
    
    Args:
        lip_sync: If True (default), use Kling Avatar for lip-synced video.
                  If False, use Veo looping background video.
        kling_model: "standard" or "pro" for Kling Avatar quality.
    """
    mode_str = ""
    if lip_sync:
        mode_str = " (LIP-SYNC MODE)"
    elif multiclip:
        mode_str = " (MULTI-CLIP MODE)"
    
    print("\n" + "="*60)
    print("🥷 NINJA CONTENT PIPELINE" + mode_str)
    print("="*60 + "\n")
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # 1. Generate TTS
        audio_path = tmpdir / "voice.mp3"
        if not generate_tts(script_text, str(audio_path), voice_style=voice_style):
            return None
        
        audio_duration = get_audio_duration(str(audio_path))
        print(f"   Audio duration: {audio_duration:.1f}s")
        
        # 2. Generate video
        if lip_sync:
            # === LIP-SYNC MODE: Use Kling Avatar ===
            # Generates lip-synced video directly from image + audio
            # No looping needed - video matches audio duration perfectly
            lip_sync_video = tmpdir / "lip_sync_video.mp4"
            
            if not reference_image or not Path(reference_image).exists():
                print("   ❌ Lip-sync requires a reference image (--image)")
                return None
            
            if not generate_kling_avatar_video(
                reference_image, 
                str(audio_path), 
                str(lip_sync_video),
                model=kling_model
            ):
                print("   ❌ Kling Avatar failed. Not falling back to Veo (per pipeline rules).")
                print("   💡 Tip: Re-run the command to retry Kling.")
                return None
            else:
                # Lip-sync video already has audio baked in!
                # Skip straight to captions
                combined = lip_sync_video

                # B-roll cutaways for lip-sync mode
                if broll:
                    print("\n🎬 Adding B-roll cutaways to lip-sync video...")
                    moments = identify_broll_moments(script_text, audio_duration, broll_count, broll_duration)
                    moments = resolve_broll_clips(moments, broll_dir, broll_map)
                    valid = [m for m in moments if 'clip_path' in m]
                    if valid:
                        broll_out = tmpdir / "with_broll.mp4"
                        if assemble_with_broll(str(combined), valid, str(broll_out)):
                            combined = broll_out
                            print(f"   ✅ Inserted {len(valid)} B-roll cutaways")
                        else:
                            print("   ⚠️ B-roll assembly failed, using avatar-only video")
                    else:
                        print("   ⚠️ No B-roll clips found, using avatar-only video")

        if kenburns:
            # === KEN BURNS MODE: Static image with slow zoom/pan ===
            # For masked characters where lip-sync doesn't work
            from ninja_kenburns import generate_kenburns_video, add_audio_to_video
            
            if not reference_image or not Path(reference_image).exists():
                print("   ❌ Ken Burns mode requires a reference image (--image)")
                return None
            
            print("🎬 Using Ken Burns effect (no lip-sync)...")
            kenburns_video = tmpdir / "kenburns_video.mp4"
            kenburns_with_audio = tmpdir / "kenburns_with_audio.mp4"
            
            # Generate Ken Burns effect matching audio duration
            if not generate_kenburns_video(
                reference_image,
                str(kenburns_video),
                audio_duration,
                effect="zoom_in"  # Subtle zoom in looks professional
            ):
                print("   ❌ Ken Burns generation failed")
                return None
            
            # Add audio track
            if not add_audio_to_video(
                str(kenburns_video),
                str(audio_path),
                str(kenburns_with_audio)
            ):
                print("   ❌ Failed to add audio to Ken Burns video")
                return None
            
            combined = kenburns_with_audio
        
        if motion:
            # === MOTION MODE: Kling i2v animation without lip-sync ===
            # For masked characters - animates body/head but no mouth
            from ninja_motion import generate_motion_video, loop_video_to_duration
            from ninja_kenburns import add_audio_to_video
            
            if not reference_image or not Path(reference_image).exists():
                print("   ❌ Motion mode requires a reference image (--image)")
                return None
            
            print("🎬 Using Kling motion animation (no lip-sync)...")
            motion_video = tmpdir / "motion_video.mp4"
            motion_looped = tmpdir / "motion_looped.mp4"
            motion_with_audio = tmpdir / "motion_with_audio.mp4"
            
            # Generate 5s motion clip (will be looped)
            if not generate_motion_video(
                reference_image,
                str(motion_video),
                duration=5
            ):
                print("   ❌ Motion video generation failed")
                return None
            
            # Loop to match audio duration
            loop_video_to_duration(str(motion_video), audio_duration, str(motion_looped))
            
            # Add audio track
            if not add_audio_to_video(
                str(motion_looped),
                str(audio_path),
                str(motion_with_audio)
            ):
                print("   ❌ Failed to add audio to motion video")
                return None
            
            combined = motion_with_audio
        
        if not lip_sync and not kenburns and not motion:
            # === VEO MODE: Generate background video and loop ===
            if multiclip:
                # Import and use multi-clip generator
                from ninja_multiclip import generate_multiclip
                
                # Calculate how many clips we need (8s each, want ~30s unique)
                num_clips = min(4, max(2, int(audio_duration / 8) + 1))
                print(f"🎬 Generating {num_clips} varied clips for more natural movement...")
                
                raw_video = tmpdir / "raw_video.mp4"
                # Use Vertex AI for higher rate limits
                if not generate_multiclip(reference_image, str(raw_video), num_clips, use_vertex=True):
                    print("   ⚠️ Multi-clip failed, falling back to single clip...")
                    multiclip = False
            
            if not multiclip:
                # Single clip mode
                video_prompt = """Animate this 3D Pixar-style ninja character at the tech news desk.
CONTINUOUS SEAMLESS IDLE LOOP: Character breathes naturally, subtle rhythmic body sway,
periodic slow eye blinks, gentle micro-movements that flow smoothly and loop seamlessly.
Head perfectly still, eyes locked on camera, facing directly forward throughout.
Professional news anchor posture. Animation must START and END in identical neutral pose
for seamless looping. Smooth Pixar-quality animation with no pauses or freezes.
Camera locked in static medium shot. No camera movement. Studio background unchanged."""
                
                raw_video = tmpdir / "raw_video.mp4"
                # Request short clip to create multiple loops → more B-roll insertion points
                # Veo minimum is 4s. A 4s clip looped for ~40s audio = ~10 loops = many seams for B-roll
                veo_clip_duration = 4
                if not generate_veo_video(video_prompt, veo_clip_duration, str(raw_video), reference_image):
                    return None
            
            # 3. Loop video to match audio (muted for CapCut, with audio for normal)
            looped_video = tmpdir / "looped_video.mp4"
            loop_video_to_duration(str(raw_video), audio_duration, str(looped_video))
        
        # 6. Veo B-roll cutaways — only for non-lip-sync mode (Veo looping background)
        # In lip-sync mode, file-based B-roll was already assembled above via assemble_with_broll
        broll_paths = []
        if broll and not lip_sync:
            from ninja_broll_veo import generate_broll_clips  # Veo-generated video B-roll

            print("\n🎬 Generating B-roll cutaways...")
            broll_dir = tmpdir / "broll"
            broll_clips = generate_broll_clips(script_text, str(broll_dir), num_clips=4)

            if broll_clips:
                broll_paths = [c["path"] for c in broll_clips if "path" in c]
        
        # CapCut mode: create draft with word-by-word animated captions
        if capcut:
            print("\n🎬 CapCut Mode: Creating draft with animated word captions...")
            
            from capcut_word_captions import generate_capcut_draft_with_word_captions
            
            # Copy assets to output dir
            import shutil
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            capcut_dir = OUTPUT_DIR / f"capcut_{output_name}_{timestamp}"
            capcut_dir.mkdir(exist_ok=True)
            
            final_video = capcut_dir / "main_video.mp4"
            final_audio = capcut_dir / "voice.mp3"
            
            # Use lip-sync video if available, otherwise looped video
            source_video = str(lip_sync_video) if lip_sync else str(looped_video)
            shutil.copy(source_video, str(final_video))
            shutil.copy(str(audio_path), str(final_audio))
            
            # Copy B-roll if any
            final_broll = []
            for i, bp in enumerate(broll_paths):
                dest = capcut_dir / f"broll_{i+1}.mp4"
                shutil.copy(bp, str(dest))
                final_broll.append(str(dest))
            
            # Generate CapCut draft with word-by-word animated captions
            draft_id = generate_capcut_draft_with_word_captions(
                str(final_video),
                str(final_audio),
                output_name,
                original_script=script_text,
                font_size=12.0,  # Smaller, cleaner size
                animation="Pop_Up",  # Word pop effect
                broll_clips=final_broll if final_broll else None
            )
            
            print("\n" + "="*60)
            print(f"✅ CapCut draft created: {draft_id}")
            print(f"   Assets: {capcut_dir}")
            print(f"   - Word-by-word animated captions")
            print(f"   - Pop_Up animation on each word")
            if final_broll:
                print(f"   - {len(final_broll)} B-roll clips")
            print("="*60 + "\n")
            
            return str(capcut_dir)
        
        # Normal mode: burn captions and composite
        # 4. Combine video + audio (skip if lip-sync, kenburns, or motion already has audio)
        if lip_sync:
            # combined is already set above in the lip_sync block — either lip_sync_video
            # (no B-roll) or broll_out (B-roll assembled). Do NOT overwrite it here.
            pass
        elif kenburns or motion:
            pass  # combined already set with audio in their respective blocks
        else:
            combined = tmpdir / "combined.mp4"
            combine_video_audio(str(looped_video), str(audio_path), str(combined))
        
        # 5. Burn captions (optional - skipped by default)
        if no_captions:
            print("📝 Skipping captions (--no-captions)")
            video_for_broll = combined
        else:
            captioned = tmpdir / "captioned.mp4"
            burn_captions(str(combined), script_text, str(captioned), audio_path=str(audio_path))
            video_for_broll = captioned
        
        # Composite B-roll if generated
        video_for_music = video_for_broll
        if broll_paths:
            from ninja_broll_compositor import compose_with_broll
            broll_composed = tmpdir / "with_broll.mp4"
            # Pass the base clip duration so compositor knows where loop seams are
            base_clip_dur = 4.0  # Matches veo_clip_duration set earlier
            if compose_with_broll(str(video_for_broll), broll_paths, str(broll_composed), 
                                  loop_clip_duration=base_clip_dur):
                video_for_music = broll_composed
                print("   ✅ B-roll inserted")
        
        # 7. Add background music
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        final_output = OUTPUT_DIR / f"{output_name}_{timestamp}.mp4"
        
        if no_music:
            # Just copy video to final
            import shutil
            shutil.copy(str(video_for_music), str(final_output))
            print("🎵 Skipping background music (--no-music)")
        else:
            add_background_music(str(video_for_music), str(final_output))
        
        print("\n" + "="*60)
        print(f"✅ DONE! Output: {final_output}")
        print(f"   Size: {final_output.stat().st_size / 1024:.0f}KB")
        print("="*60 + "\n")
        
        return str(final_output)


def main():
    parser = argparse.ArgumentParser(description="Ninja Content Pipeline")
    
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--auto", action="store_true", help="Full auto: discover news, pick top, generate everything")
    mode.add_argument("--discover", action="store_true", help="Discover news stories")
    mode.add_argument("--pick", type=int, metavar="N", help="Pick story N from discovered list")
    mode.add_argument("--script", type=str, help="Use custom script text")
    mode.add_argument("--script-file", type=str, help="Use script from file")
    
    parser.add_argument("--image", type=str, help="Reference image for character", 
                        default=str(ASSETS_DIR / "reference" / "ninja_helmet_v4_hires.jpg"))
    parser.add_argument("--output", type=str, default="ninja_content", help="Output filename prefix")
    parser.add_argument("--category", type=str, default="tech", help="News category")
    parser.add_argument("--multiclip", action="store_true", 
                        help="Generate multiple varied clips for more natural movement (slower but better)")
    parser.add_argument("--no-music", action="store_true",
                        help="Skip adding background music")
    parser.add_argument("--no-captions", action="store_true", default=True,
                        help="Skip burning captions into video (default: True, use --captions to enable)")
    parser.add_argument("--captions", action="store_true",
                        help="Burn captions into video (disabled by default)")
    parser.add_argument("--thumbnail", action="store_true",
                        help="Also generate a thumbnail image")
    parser.add_argument("--thumb-style", default="excited",
                        choices=["engaging", "shocked", "thinking", "pointing", "excited"],
                        help="Thumbnail ninja pose style")
    parser.add_argument("--publish", choices=["youtube"],
                        help="Auto-publish to platform after generation")
    parser.add_argument("--privacy", default="private",
                        choices=["private", "unlisted", "public"],
                        help="Privacy status for published video")
    parser.add_argument("--broll", action="store_true",
                        help="Insert B-roll cutaways (works in lip-sync and Veo modes)")
    parser.add_argument("--broll-dir", type=str, default=None,
                        help="Directory containing B-roll clips (e.g. ~/output/feb_games/broll/)")
    parser.add_argument("--broll-map", nargs="+", default=None,
                        help="Explicit keyword:file.mp4 mappings (repeatable, e.g. nioh:nioh3.mp4)")
    parser.add_argument("--broll-count", type=int, default=3,
                        help="Number of B-roll cutaways (default: 3)")
    parser.add_argument("--broll-duration", type=float, default=4.0,
                        help="Duration per B-roll clip in seconds (default: 4.0)")
    parser.add_argument("--capcut", action="store_true",
                        help="Output as CapCut draft for manual editing (requires CapCut API server)")
    parser.add_argument("--no-lip-sync", action="store_true",
                        help="Disable lip-sync (use Veo looping instead of Kling Avatar)")
    parser.add_argument("--kenburns", action="store_true",
                        help="Use Ken Burns effect instead of lip-sync (for masked characters)")
    parser.add_argument("--motion", action="store_true",
                        help="Use Kling motion animation without lip-sync (for masked characters)")
    parser.add_argument("--kling-model", default="standard",
                        choices=["standard", "pro"],
                        help="Kling Avatar quality: standard ($0.056/sec) or pro ($0.115/sec)")
    parser.add_argument("--voice-style", default="expressive",
                        choices=["expressive", "natural", "calm"],
                        help="ElevenLabs voice expressiveness: expressive (high energy), natural (balanced), calm (steady)")
    
    args = parser.parse_args()
    
    # Find reference image
    ref_image = None
    if args.image and Path(args.image).exists():
        ref_image = args.image
    else:
        # Try to find the user's concept image
        possible_images = [
            ASSETS_DIR / "reference" / "ninja_concept.jpg",
            Path("/home/ndninja/.clawdbot/media/inbound/387141bd-1a6a-40b7-898a-fa3c2cb38b4e.jpg"),
        ]
        for img in possible_images:
            if img.exists():
                ref_image = str(img)
                break
    
    if args.discover:
        discover_news(args.category)
        return
    
    script_text = None
    
    if args.auto:
        discover_news(args.category)
        script_text = generate_script(auto=True)
    elif args.pick:
        script_text = generate_script(story_index=args.pick)
    elif args.script:
        script_text = args.script
    elif args.script_file:
        script_text = Path(args.script_file).read_text().strip()
    
    if not script_text:
        print("❌ No script generated or provided")
        return
    
    print(f"\n📜 Script ({len(script_text.split())} words):")
    print("-" * 40)
    print(script_text)
    print("-" * 40 + "\n")
    
    # Run pipeline
    # Captions are disabled by default; use --captions to enable
    skip_captions = not args.captions
    output = run_pipeline(
        script_text,
        ref_image,
        args.output,
        multiclip=args.multiclip,
        no_music=args.no_music,
        no_captions=skip_captions,
        broll=args.broll,
        capcut=args.capcut,
        lip_sync=not args.no_lip_sync and not args.kenburns and not args.motion,
        kenburns=args.kenburns,
        motion=args.motion,
        kling_model=args.kling_model,
        broll_dir=args.broll_dir,
        broll_map=args.broll_map,
        broll_count=args.broll_count,
        broll_duration=args.broll_duration,
        voice_style=args.voice_style,
    )
    
    if output:
        print(f"\n🎉 Content ready: {output}")
        
        # Generate thumbnail if requested
        thumb_output = None
        if args.thumbnail:
            from ninja_thumbnail import generate_thumbnail
            # Extract actual topic from script (skip intro lines)
            topic = extract_topic_from_script(script_text)
            thumb_output = str(Path(output).with_suffix('.thumb.png'))
            generate_thumbnail(topic, args.thumb_style, thumb_output)
        
        # Publish if requested
        if args.publish == "youtube":
            from youtube.youtube_upload import upload_video
            # Build title and description using extracted topic
            topic_for_title = extract_topic_from_script(script_text)
            # Shorten for title (max 100 chars, first sentence)
            title = topic_for_title.split('.')[0][:100] if '.' in topic_for_title else topic_for_title[:100]
            description = f"""🥷 {title}

{script_text}

#TechNews #NeurodivergentNinja #Shorts
---
Follow for daily ninja briefings!
"""
            tags = ["tech", "news", "shorts", "ninja", "neurodivergent"]
            
            video_id = upload_video(
                output, 
                title, 
                description, 
                tags, 
                thumb_output,
                args.privacy
            )
            if video_id:
                print(f"📺 Published to YouTube: https://youtube.com/watch?v={video_id}")


if __name__ == "__main__":
    main()
