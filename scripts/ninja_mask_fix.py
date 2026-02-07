#!/usr/bin/env python3
"""
Fix mouth-through-mask issue by compositing static mask area over animated video.
"""

import subprocess
import sys
from pathlib import Path

def create_mask_overlay(
    original_image: str,
    animated_video: str,
    output_video: str,
    mask_region: tuple = None  # (x, y, width, height) of mask area
) -> bool:
    """
    Overlay the mask region from original image onto animated video.
    
    If mask_region not specified, uses lower face area by default.
    """
    original_image = Path(original_image)
    animated_video = Path(animated_video)
    
    if not original_image.exists() or not animated_video.exists():
        print("   ❌ Input files not found")
        return False
    
    # Get video dimensions
    probe = subprocess.run([
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=p=0",
        animated_video
    ], capture_output=True, text=True)
    
    w, h = map(int, probe.stdout.strip().split(","))
    
    # Default mask region: lower third of face (where mouth/mask would be)
    # Adjust these values based on your ninja image
    if not mask_region:
        # For 9:16 vertical video, mask is roughly in center-lower area
        mask_x = int(w * 0.25)  # Start 25% from left
        mask_y = int(h * 0.35)  # Start 35% from top
        mask_w = int(w * 0.50)  # 50% width
        mask_h = int(h * 0.20)  # 20% height
    else:
        mask_x, mask_y, mask_w, mask_h = mask_region
    
    print(f"   🎭 Applying mask fix: region ({mask_x},{mask_y}) {mask_w}x{mask_h}")
    
    # FFmpeg filter: overlay cropped region from original image onto video
    # 1. Scale original image to match video size
    # 2. Crop the mask region
    # 3. Overlay onto video at same position
    
    filter_complex = f"""
    [1:v]scale={w}:{h}[scaled];
    [scaled]crop={mask_w}:{mask_h}:{mask_x}:{mask_y}[mask_crop];
    [0:v][mask_crop]overlay={mask_x}:{mask_y}[out]
    """
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(animated_video),
        "-i", str(original_image),
        "-filter_complex", filter_complex.strip(),
        "-map", "[out]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "copy",
        str(output_video)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"   ❌ FFmpeg error: {result.stderr[:500]}")
        return False
    
    print(f"   ✅ Mask-fixed video saved: {output_video}")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: ninja_mask_fix.py <original_image> <animated_video> <output>")
        print("Optional: Add x,y,w,h for custom mask region")
        sys.exit(1)
    
    image = sys.argv[1]
    video = sys.argv[2]
    output = sys.argv[3]
    
    region = None
    if len(sys.argv) > 4:
        region = tuple(map(int, sys.argv[4].split(",")))
    
    success = create_mask_overlay(image, video, output, region)
    sys.exit(0 if success else 1)
