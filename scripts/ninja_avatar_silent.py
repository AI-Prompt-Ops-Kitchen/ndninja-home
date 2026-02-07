#!/usr/bin/env python3
"""
Silent Avatar animation - Kling Avatar with silent audio for natural movement without lip-sync.
"""

import os
import sys
import subprocess
import time
import requests
import keyring
from pathlib import Path

def generate_silent_avatar(
    image_path: str,
    output_path: str,
    duration: float = 5
) -> bool:
    """
    Generate Avatar animation with silent audio (no lip-sync).
    
    Args:
        image_path: Path to character image
        output_path: Where to save the video
        duration: Clip duration (5 or 10 seconds)
    """
    # Get fal.ai API key
    fal_key = keyring.get_password("fal_ai", "api_key")
    if not fal_key:
        print("   ❌ fal.ai API key not found")
        return False
    
    os.environ["FAL_KEY"] = fal_key
    
    try:
        import fal_client
    except ImportError:
        print("   ❌ fal_client not installed")
        return False
    
    # Create silent audio
    silence_path = "/tmp/silence_avatar.mp3"
    dur = "5" if duration <= 5 else "10"
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
        "-t", dur, "-c:a", "libmp3lame", silence_path
    ], capture_output=True)
    
    print(f"   🎬 Generating silent Avatar animation ({dur}s)...")
    
    # Upload files
    with open(image_path, "rb") as f:
        image_url = fal_client.upload(f.read(), "image/jpeg")
    with open(silence_path, "rb") as f:
        audio_url = fal_client.upload(f.read(), "audio/mpeg")
    
    start_time = time.time()
    
    try:
        result = fal_client.subscribe(
            "fal-ai/kling-video/ai-avatar/v2/standard",
            arguments={
                "image_url": image_url,
                "audio_url": audio_url,
                "prompt": "Subtle breathing, gentle body sway, occasional slow blink. Natural idle animation. Mouth closed, not talking."
            },
            with_logs=True
        )
    except Exception as e:
        print(f"   ❌ Avatar generation failed: {e}")
        return False
    
    elapsed = time.time() - start_time
    print(f"   ⏱️ Generation took {elapsed:.1f}s")
    
    # Download video
    video_url = result.get("video", {}).get("url")
    if not video_url:
        print(f"   ❌ No video URL in response")
        return False
    
    resp = requests.get(video_url)
    with open(output_path, "wb") as f:
        f.write(resp.content)
    
    print(f"   ✅ Avatar clip saved: {output_path}")
    return True


def loop_video_to_duration(video_path: str, target_duration: float, output_path: str) -> bool:
    """Loop a short video to match target duration."""
    # Get video duration
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", video_path
    ], capture_output=True, text=True)
    
    clip_duration = float(probe.stdout.strip())
    loops_needed = int(target_duration / clip_duration) + 1
    
    print(f"   🔄 Looping {clip_duration:.1f}s clip {loops_needed}x for {target_duration:.1f}s...")
    
    # Create concat file
    concat_file = Path(video_path).parent / "concat_avatar.txt"
    with open(concat_file, "w") as f:
        for _ in range(loops_needed):
            f.write(f"file '{video_path}'\n")
    
    # Concat and trim
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-t", str(target_duration),
        "-c", "copy",
        output_path
    ], capture_output=True)
    
    concat_file.unlink()
    return True


def add_audio_to_video(video_path: str, audio_path: str, output_path: str) -> bool:
    """Combine video with audio track."""
    print(f"   🔊 Adding audio track...")
    
    result = subprocess.run([
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_path
    ], capture_output=True)
    
    return result.returncode == 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: ninja_avatar_silent.py <image> <output.mp4> [duration]")
        sys.exit(1)
    
    image = sys.argv[1]
    output = sys.argv[2]
    duration = float(sys.argv[3]) if len(sys.argv) > 3 else 5
    
    success = generate_silent_avatar(image, output, duration)
    sys.exit(0 if success else 1)
