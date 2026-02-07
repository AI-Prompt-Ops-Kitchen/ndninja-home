#!/usr/bin/env python3
"""
Subtle motion animation for static images using Kling Image-to-Video.
Animates breathing, swaying, etc. WITHOUT lip-sync.
"""

import os
import sys
import time
import requests
import keyring
from pathlib import Path

def generate_motion_video(
    image_path: str,
    output_path: str,
    duration: float = 5,
    prompt: str = None
) -> bool:
    """
    Generate subtle motion video from static image using Kling i2v.
    
    Args:
        image_path: Path to source image
        output_path: Where to save the video
        duration: Video duration (5 or 10 seconds)
        prompt: Motion prompt (optional)
    
    Returns:
        True on success
    """
    # Get fal.ai API key
    fal_key = keyring.get_password("fal_ai", "api_key")
    if not fal_key:
        print("   ❌ fal.ai API key not found in keyring")
        return False
    
    os.environ["FAL_KEY"] = fal_key
    
    try:
        import fal_client
    except ImportError:
        print("   ❌ fal_client not installed. Run: pip install fal-client")
        return False
    
    image_path = Path(image_path)
    if not image_path.exists():
        print(f"   ❌ Image not found: {image_path}")
        return False
    
    # Default prompt for subtle idle animation
    if not prompt:
        prompt = """Subtle idle animation. Character breathes naturally with gentle chest movement.
Very slight body sway. Occasional slow blink. Micro-movements that feel alive.
Camera perfectly static. No dramatic motion. Professional news anchor energy.
Seamless loopable animation. Character wears a mask covering lower face."""
    
    # Negative prompt to prevent mouth showing through mask
    negative_prompt = "visible mouth, lips, open mouth, mouth movement, teeth, tongue, speaking, talking, lip sync, exposed face, unmasked"
    
    print(f"   🎬 Generating motion video ({duration}s)...")
    print(f"   📝 Prompt: {prompt[:80]}...")
    
    # Upload image
    with open(image_path, "rb") as f:
        image_data = f.read()
    image_url = fal_client.upload(image_data, "image/jpeg")
    
    # Use Kling 2.1 Pro (faster and reliable)
    model_id = "fal-ai/kling-video/v2.1/pro/image-to-video"
    
    start_time = time.time()
    
    try:
        result = fal_client.subscribe(
            model_id,
            arguments={
                "image_url": image_url,
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "duration": "5" if duration <= 5 else "10",
                "aspect_ratio": "9:16"
            },
            with_logs=True
        )
    except Exception as e:
        print(f"   ❌ Kling i2v failed: {e}")
        return False
    
    elapsed = time.time() - start_time
    print(f"   ⏱️ Generation took {elapsed:.1f}s")
    
    # Download video
    video_url = result.get("video", {}).get("url")
    if not video_url:
        print(f"   ❌ No video URL in response: {result}")
        return False
    
    print(f"   📥 Downloading video...")
    resp = requests.get(video_url)
    with open(output_path, "wb") as f:
        f.write(resp.content)
    
    print(f"   ✅ Motion video saved: {output_path}")
    return True


def loop_video_to_duration(video_path: str, target_duration: float, output_path: str) -> bool:
    """Loop a short video to match target duration."""
    import subprocess
    
    # Get video duration
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", video_path
    ], capture_output=True, text=True)
    
    clip_duration = float(probe.stdout.strip())
    loops_needed = int(target_duration / clip_duration) + 1
    
    print(f"   🔄 Looping {clip_duration:.1f}s clip {loops_needed}x for {target_duration:.1f}s...")
    
    # Create concat file
    concat_file = Path(video_path).parent / "concat.txt"
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


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: ninja_motion.py <image> <output.mp4> [duration] [prompt]")
        sys.exit(1)
    
    image = sys.argv[1]
    output = sys.argv[2]
    duration = float(sys.argv[3]) if len(sys.argv) > 3 else 5
    prompt = sys.argv[4] if len(sys.argv) > 4 else None
    
    success = generate_motion_video(image, output, duration, prompt)
    sys.exit(0 if success else 1)
