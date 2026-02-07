#!/usr/bin/env python3
"""
Ken Burns effect generator for static images.
Creates professional slow zoom/pan animation for news-style videos.
"""

import subprocess
import sys
from pathlib import Path
import random

def generate_kenburns_video(
    image_path: str,
    output_path: str,
    duration: float,
    effect: str = "zoom_in",
    fps: int = 30
) -> bool:
    """
    Generate Ken Burns effect video from static image.
    
    Args:
        image_path: Path to source image
        output_path: Where to save the video
        duration: Video duration in seconds
        effect: One of 'zoom_in', 'zoom_out', 'pan_left', 'pan_right', 'random'
        fps: Frames per second
    
    Returns:
        True on success
    """
    image_path = Path(image_path)
    if not image_path.exists():
        print(f"   ❌ Image not found: {image_path}")
        return False
    
    # Output resolution (9:16 for shorts/vertical)
    out_w, out_h = 1080, 1920
    
    # Zoom range (start/end scale factors)
    # Subtle zoom: 1.0 to 1.15 over the duration
    if effect == "random":
        effect = random.choice(["zoom_in", "zoom_out", "pan_left", "pan_right"])
    
    # Build the zoompan filter
    # zoompan: z=zoom, x/y=position, d=duration in frames, s=output size
    frames = int(duration * fps)
    
    if effect == "zoom_in":
        # Start at 1.0, end at 1.15
        zoom_filter = f"zoompan=z='1+0.15*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={out_w}x{out_h}:fps={fps}"
    elif effect == "zoom_out":
        # Start at 1.15, end at 1.0
        zoom_filter = f"zoompan=z='1.15-0.15*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={out_w}x{out_h}:fps={fps}"
    elif effect == "pan_left":
        # Pan from right to left, slight zoom
        zoom_filter = f"zoompan=z='1.1':x='iw*0.1+iw*0.05*on/{frames}':y='ih/2-(ih/zoom/2)':d={frames}:s={out_w}x{out_h}:fps={fps}"
    elif effect == "pan_right":
        # Pan from left to right, slight zoom
        zoom_filter = f"zoompan=z='1.1':x='iw*0.15-iw*0.05*on/{frames}':y='ih/2-(ih/zoom/2)':d={frames}:s={out_w}x{out_h}:fps={fps}"
    else:
        # Default center zoom in
        zoom_filter = f"zoompan=z='1+0.15*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={out_w}x{out_h}:fps={fps}"
    
    print(f"   🎬 Generating Ken Burns effect ({effect}, {duration:.1f}s)...")
    
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(image_path),
        "-vf", zoom_filter,
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"   ❌ FFmpeg error: {result.stderr[:500]}")
        return False
    
    print(f"   ✅ Ken Burns video saved: {output_path}")
    return True


def add_audio_to_video(video_path: str, audio_path: str, output_path: str) -> bool:
    """Combine video with audio track."""
    print(f"   🔊 Adding audio track...")
    
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"   ❌ FFmpeg error: {result.stderr[:500]}")
        return False
    
    return True


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: ninja_kenburns.py <image> <output.mp4> <duration_sec> [effect]")
        print("Effects: zoom_in, zoom_out, pan_left, pan_right, random")
        sys.exit(1)
    
    image = sys.argv[1]
    output = sys.argv[2]
    duration = float(sys.argv[3])
    effect = sys.argv[4] if len(sys.argv) > 4 else "zoom_in"
    
    success = generate_kenburns_video(image, output, duration, effect)
    sys.exit(0 if success else 1)
