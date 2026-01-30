#!/usr/bin/env python3
"""
ninja_content.py — Full content pipeline: News → Script → Video → Ready to Post

The Neurodivergent Ninja content factory.

Usage:
    # Full auto mode (discovers news, picks top story, generates everything)
    ninja-content --auto
    
    # Interactive mode (choose your story)
    ninja-content --discover
    ninja-content --pick 3
    
    # From custom script
    ninja-content --script "Your script text here"
    
    # From script file
    ninja-content --script-file script.txt
"""

import argparse
import json
import os
import subprocess
import sys
import time
import tempfile
import requests
from pathlib import Path

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
DEFAULT_VOICE_ID = "pDrEFcc78kuc76ECGkU8"  # Neurodivergent Ninja - user's cloned voice


def get_api_keys():
    """Load API keys from environment or config files."""
    keys = {}
    
    # Google/Veo
    keys['google'] = os.environ.get('GOOGLE_API_KEY', 'AIzaSyAFQJmUow1dsNqYTXRvEuRVZowzpr8-cXk')
    
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


def generate_tts(script_text, output_path, voice_id=DEFAULT_VOICE_ID, pad_start=0.5):
    """Generate TTS audio using ElevenLabs with optional padding."""
    print("🎙️ Generating voice audio...")
    
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
            "text": script_text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.3
            }
        }
    )
    
    if response.status_code == 200:
        # Save raw audio first
        raw_path = output_path + ".raw.mp3"
        with open(raw_path, "wb") as f:
            f.write(response.content)
        
        # Add padding at start to prevent first word cutoff
        if pad_start > 0:
            print(f"   🔇 Adding {pad_start}s padding at start...")
            delay_ms = int(pad_start * 1000)
            subprocess.run([
                "ffmpeg", "-y",
                "-i", raw_path,
                "-af", f"adelay={delay_ms}|{delay_ms},apad=pad_dur={pad_start}",
                "-c:a", "libmp3lame", "-q:a", "2",  # High quality MP3
                output_path
            ], capture_output=True)
            os.remove(raw_path)
        else:
            os.rename(raw_path, output_path)
        
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


def run_pipeline(script_text, reference_image=None, output_name="ninja_content", multiclip=False, no_music=False, broll=False, capcut=False):
    """Run the full content pipeline."""
    print("\n" + "="*60)
    print("🥷 NINJA CONTENT PIPELINE" + (" (MULTI-CLIP MODE)" if multiclip else ""))
    print("="*60 + "\n")
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # 1. Generate TTS
        audio_path = tmpdir / "voice.mp3"
        if not generate_tts(script_text, str(audio_path)):
            return None
        
        audio_duration = get_audio_duration(str(audio_path))
        print(f"   Audio duration: {audio_duration:.1f}s")
        
        # 2. Generate video (single or multi-clip)
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
            if not generate_veo_video(video_prompt, audio_duration, str(raw_video), reference_image):
                return None
        
        # 3. Loop video to match audio (muted for CapCut, with audio for normal)
        looped_video = tmpdir / "looped_video.mp4"
        loop_video_to_duration(str(raw_video), audio_duration, str(looped_video))
        
        # 6. B-roll cutaways (generate early if capcut mode needs them)
        broll_paths = []
        if broll:
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
            
            shutil.copy(str(looped_video), str(final_video))
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
        # 4. Combine video + audio
        combined = tmpdir / "combined.mp4"
        combine_video_audio(str(looped_video), str(audio_path), str(combined))
        
        # 5. Burn captions
        captioned = tmpdir / "captioned.mp4"
        burn_captions(str(combined), script_text, str(captioned), audio_path=str(audio_path))
        
        # Composite B-roll if generated
        video_for_music = captioned
        if broll_paths:
            from ninja_broll_compositor import compose_with_broll
            broll_composed = tmpdir / "with_broll.mp4"
            if compose_with_broll(str(captioned), broll_paths, str(broll_composed)):
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
                        default=str(ASSETS_DIR / "reference" / "ninja_concept.jpg"))
    parser.add_argument("--output", type=str, default="ninja_content", help="Output filename prefix")
    parser.add_argument("--category", type=str, default="tech", help="News category")
    parser.add_argument("--multiclip", action="store_true", 
                        help="Generate multiple varied clips for more natural movement (slower but better)")
    parser.add_argument("--no-music", action="store_true",
                        help="Skip adding background music")
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
                        help="Generate and insert B-roll cutaways to hide loop points")
    parser.add_argument("--capcut", action="store_true",
                        help="Output as CapCut draft for manual editing (requires CapCut API server)")
    
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
    output = run_pipeline(script_text, ref_image, args.output, multiclip=args.multiclip, no_music=args.no_music, broll=args.broll, capcut=args.capcut)
    
    if output:
        print(f"\n🎉 Content ready: {output}")
        
        # Generate thumbnail if requested
        thumb_output = None
        if args.thumbnail:
            from ninja_thumbnail import generate_thumbnail
            # Extract topic from script (first sentence after "Hey Ninjas!")
            topic = script_text.split("!")[1].strip().split(".")[0] if "!" in script_text else script_text[:50]
            thumb_output = str(Path(output).with_suffix('.thumb.png'))
            generate_thumbnail(topic, args.thumb_style, thumb_output)
        
        # Publish if requested
        if args.publish == "youtube":
            from youtube.youtube_upload import upload_video
            # Build title and description
            title = script_text.split("!")[1].strip().split(".")[0][:100] if "!" in script_text else "Ninja Tech Update"
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
