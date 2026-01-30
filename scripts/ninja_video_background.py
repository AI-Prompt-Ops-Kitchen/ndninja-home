#!/usr/bin/env python3
"""
ninja_video_background.py — Composite avatar over animated video backgrounds

Uses rembg for proper AI-powered background removal on each frame.

Part of the Neurodivergent Ninja content pipeline.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import threading

try:
    from rembg import remove, new_session
    from PIL import Image
    import numpy as np
    HAS_REMBG = True
except ImportError:
    HAS_REMBG = False
    print("Error: rembg required. Install with: pip install rembg", file=sys.stderr)

# Scene configuration
SCENES_DIR = Path(__file__).resolve().parent.parent / "assets" / "scenes"

SCENE_CONFIGS = {
    "dojo": {
        "background": "dojo/dojo_animated.mp4",
        "static_fallback": "dojo/dojo_background.png",
    },
    "zen_garden": {
        "background": "zen_garden/zen_garden_animated.mp4",
        "static_fallback": "zen_garden/zen_garden_background.png",
    },
    "tea_house": {
        "background": "tea_house/tea_house_animated.mp4",
        "static_fallback": "tea_house/tea_house_background.png",
    },
    "scholars_study": {
        "background": "scholars_study/scholars_study_animated.mp4",
        "static_fallback": "scholars_study/scholars_study_background.png",
    },
}


def get_video_info(path: str) -> dict:
    """Get video metadata using ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-show_entries", "format=duration:stream=width,height,r_frame_rate,nb_frames",
        "-of", "json", path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)
    
    stream = data.get("streams", [{}])[0]
    fmt = data.get("format", {})
    
    fps_str = stream.get("r_frame_rate", "25/1")
    if "/" in fps_str:
        num, den = map(int, fps_str.split("/"))
        fps = num / den if den else 25
    else:
        fps = float(fps_str)
    
    return {
        "width": stream.get("width", 1080),
        "height": stream.get("height", 1920),
        "fps": fps,
        "duration": float(fmt.get("duration", 0)),
        "frames": int(stream.get("nb_frames", 0)) or int(fps * float(fmt.get("duration", 0))),
    }


def composite_video_with_rembg(
    input_video: str,
    background_video: str,
    output_video: str,
    target_width: int = 1080,
    target_height: int = 1920,
) -> None:
    """
    Composite avatar video over animated background using rembg for clean isolation.
    """
    if not HAS_REMBG:
        print("❌ rembg required for proper background removal", file=sys.stderr)
        sys.exit(1)
    
    avatar_info = get_video_info(input_video)
    bg_info = get_video_info(background_video)
    
    print(f"[VideoBackground] Avatar: {avatar_info['width']}x{avatar_info['height']}, {avatar_info['fps']:.1f}fps, {avatar_info['duration']:.1f}s")
    print(f"[VideoBackground] Background: {bg_info['width']}x{bg_info['height']}, {bg_info['fps']:.1f}fps, {bg_info['duration']:.1f}s")
    print(f"[VideoBackground] Output: {target_width}x{target_height}")
    
    # Initialize rembg session (reuse for speed)
    print("[VideoBackground] Loading rembg model...")
    session = new_session("u2net")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        avatar_frames_dir = os.path.join(tmpdir, "avatar_frames")
        bg_frames_dir = os.path.join(tmpdir, "bg_frames")
        output_frames_dir = os.path.join(tmpdir, "output_frames")
        os.makedirs(avatar_frames_dir)
        os.makedirs(bg_frames_dir)
        os.makedirs(output_frames_dir)
        
        # Extract avatar frames
        print("[VideoBackground] Extracting avatar frames...")
        subprocess.run([
            "ffmpeg", "-y", "-i", input_video,
            "-vf", f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:color=black",
            f"{avatar_frames_dir}/frame_%06d.png"
        ], capture_output=True)
        
        # Calculate loops needed for background
        loops_needed = int(avatar_info['duration'] / bg_info['duration']) + 1
        
        # Extract background frames (looped)
        print("[VideoBackground] Extracting background frames...")
        subprocess.run([
            "ffmpeg", "-y",
            "-stream_loop", str(loops_needed),
            "-i", background_video,
            "-t", str(avatar_info['duration']),
            "-vf", f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2",
            "-r", str(avatar_info['fps']),
            f"{bg_frames_dir}/frame_%06d.png"
        ], capture_output=True)
        
        # Get frame lists
        avatar_frames = sorted([f for f in os.listdir(avatar_frames_dir) if f.endswith('.png')])
        bg_frames = sorted([f for f in os.listdir(bg_frames_dir) if f.endswith('.png')])
        
        total_frames = len(avatar_frames)
        print(f"[VideoBackground] Processing {total_frames} frames with rembg...")
        
        # Cache the mask from first frame (avatar doesn't move much)
        first_avatar = Image.open(os.path.join(avatar_frames_dir, avatar_frames[0]))
        first_result = remove(first_avatar, session=session)
        cached_mask = first_result.split()[3] if first_result.mode == 'RGBA' else None
        
        # Process frames
        processed = 0
        lock = threading.Lock()
        
        def process_frame(i):
            nonlocal processed
            
            avatar_path = os.path.join(avatar_frames_dir, avatar_frames[i])
            bg_idx = i % len(bg_frames)
            bg_path = os.path.join(bg_frames_dir, bg_frames[bg_idx])
            output_path = os.path.join(output_frames_dir, f"frame_{i+1:06d}.png")
            
            # Load images
            avatar = Image.open(avatar_path).convert('RGB')
            bg = Image.open(bg_path).convert('RGB')
            
            # Remove background from avatar using rembg
            # Use cached mask for speed (avatar position is consistent)
            if cached_mask is not None and i > 0:
                # Apply cached mask to current frame
                avatar_rgba = avatar.copy()
                avatar_rgba.putalpha(cached_mask)
            else:
                avatar_rgba = remove(avatar, session=session)
            
            # Composite: background + avatar
            bg_rgba = bg.convert('RGBA')
            bg_rgba.paste(avatar_rgba, (0, 0), avatar_rgba)
            
            # Save
            bg_rgba.convert('RGB').save(output_path, 'PNG')
            
            with lock:
                processed += 1
                if processed % 50 == 0 or processed == total_frames:
                    print(f"[VideoBackground] Frame {processed}/{total_frames}")
        
        # Process frames (single-threaded for consistent mask)
        for i in range(total_frames):
            process_frame(i)
        
        # Encode output video
        print("[VideoBackground] Encoding video...")
        subprocess.run([
            "ffmpeg", "-y",
            "-framerate", str(avatar_info['fps']),
            "-i", f"{output_frames_dir}/frame_%06d.png",
            "-c:v", "libx264", "-crf", "18", "-preset", "medium",
            "-pix_fmt", "yuv420p",
            f"{tmpdir}/video_only.mp4"
        ], capture_output=True)
        
        # Mux audio
        print("[VideoBackground] Muxing audio...")
        subprocess.run([
            "ffmpeg", "-y",
            "-i", f"{tmpdir}/video_only.mp4",
            "-i", input_video,
            "-map", "0:v",
            "-map", "1:a?",
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            output_video
        ], capture_output=True)
    
    if os.path.exists(output_video):
        size = os.path.getsize(output_video)
        print(f"[VideoBackground] ✅ Output: {output_video} ({size/1024:.0f}KB)")
    else:
        print("[VideoBackground] ❌ Output not created")


def main():
    parser = argparse.ArgumentParser(description="Composite avatar over animated video background")
    parser.add_argument("--input", "-i", required=True, help="Input avatar video")
    parser.add_argument("--output", "-o", required=True, help="Output video")
    parser.add_argument("--background", "-b", help="Background video file")
    parser.add_argument("--scene", "-s", choices=list(SCENE_CONFIGS.keys()), help="Use a predefined scene")
    parser.add_argument("--width", type=int, default=1080, help="Output width (default: 1080)")
    parser.add_argument("--height", type=int, default=1920, help="Output height (default: 1920)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"❌ Input not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    
    # Determine background
    if args.scene:
        config = SCENE_CONFIGS[args.scene]
        bg_path = SCENES_DIR / config["background"]
        if not bg_path.exists():
            bg_path = SCENES_DIR / config["static_fallback"]
            if not bg_path.exists():
                print(f"❌ Scene not found: {args.scene}", file=sys.stderr)
                sys.exit(1)
            print(f"[VideoBackground] Using static fallback for {args.scene}")
        background = str(bg_path)
    elif args.background:
        background = args.background
        if not os.path.exists(background):
            print(f"❌ Background not found: {background}", file=sys.stderr)
            sys.exit(1)
    else:
        print("❌ Must specify --background or --scene", file=sys.stderr)
        sys.exit(1)
    
    composite_video_with_rembg(
        args.input,
        background,
        args.output,
        args.width,
        args.height,
    )


if __name__ == "__main__":
    main()
