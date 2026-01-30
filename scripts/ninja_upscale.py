#!/usr/bin/env python3
"""
ninja_upscale.py — Upscale Ditto TalkingHead video to Shorts/Reels resolution.

Upscales 288×512 (or any input) → 1080×1920 (9:16 vertical) using ffmpeg
with lanczos scaling for high-quality results.

Usage:
    python ninja_upscale.py --input input.mp4 --output upscaled.mp4
    python ninja_upscale.py --input input.mp4 --output upscaled.mp4 --width 1080 --height 1920
    python ninja_upscale.py --input input.mp4 --output upscaled.mp4 --crf 16
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


# Default target: YouTube Shorts / Instagram Reels (9:16 vertical)
DEFAULT_WIDTH = 1080
DEFAULT_HEIGHT = 1920
DEFAULT_CRF = 18  # High quality (lower = better quality, bigger file)


def get_video_info(video_path: str) -> dict:
    """Get video dimensions, fps, and duration via ffprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_streams", "-show_format", "-select_streams", "v:0",
         video_path],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")

    data = json.loads(result.stdout)
    stream = data["streams"][0]
    fmt = data.get("format", {})

    return {
        "width": int(stream["width"]),
        "height": int(stream["height"]),
        "fps": stream.get("r_frame_rate", "25/1"),
        "duration": float(fmt.get("duration", 0)),
        "codec": stream.get("codec_name", "unknown"),
    }


def upscale_video(
    input_path: str,
    output_path: str,
    target_width: int = DEFAULT_WIDTH,
    target_height: int = DEFAULT_HEIGHT,
    crf: int = DEFAULT_CRF,
    preset: str = "slow",
) -> str:
    """
    Upscale video using ffmpeg with lanczos interpolation.

    Uses a two-pass approach:
      1. Lanczos upscale (best quality for scaling up)
      2. Slight unsharp mask to recover detail lost in upscaling

    Args:
        input_path: Source video path
        output_path: Destination video path
        target_width: Target width (default 1080)
        target_height: Target height (default 1920)
        crf: Quality factor (default 18, lower = better)
        preset: x264 encoding preset (default "slow" for quality)

    Returns:
        Path to upscaled video
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input video not found: {input_path}")

    # Get source info
    info = get_video_info(input_path)
    src_w, src_h = info["width"], info["height"]

    print(f"📐 Source: {src_w}×{src_h} ({info['codec']}, {info['duration']:.1f}s)")
    print(f"📐 Target: {target_width}×{target_height}")

    # Check if upscaling is actually needed
    if src_w >= target_width and src_h >= target_height:
        print(f"   ℹ️  Video is already {src_w}×{src_h}, no upscaling needed")
        # Just copy if dimensions match or exceed target
        if input_path != output_path:
            import shutil
            shutil.copy2(input_path, output_path)
        return output_path

    # Calculate scale factor for reporting
    scale_x = target_width / src_w
    scale_y = target_height / src_h
    print(f"   Scale factor: {scale_x:.2f}x width, {scale_y:.2f}x height")

    # Build the filter chain:
    # 1. scale with lanczos (best upscaling quality in ffmpeg)
    # 2. light unsharp mask to add back some sharpness post-upscale
    #    (5x5 luma, strength 0.5 — subtle, avoids artifacts)
    vf_chain = (
        f"scale={target_width}:{target_height}:flags=lanczos,"
        f"unsharp=5:5:0.5:5:5:0.0"
    )

    # Ensure output directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # Build ffmpeg command
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", vf_chain,
        "-c:v", "libx264",
        "-preset", preset,
        "-crf", str(crf),
        "-profile:v", "high",
        "-level", "4.1",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        output_path,
    ]

    print(f"🔄 Upscaling with ffmpeg lanczos + unsharp...")
    print(f"   Preset: {preset}, CRF: {crf}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg upscale failed:\n{result.stderr}")

    # Verify output
    if not os.path.exists(output_path):
        raise RuntimeError("ffmpeg produced no output file")

    out_info = get_video_info(output_path)
    out_size = os.path.getsize(output_path)
    in_size = os.path.getsize(input_path)

    print(f"   ✅ Upscaled: {out_info['width']}×{out_info['height']}")
    print(f"   📦 Size: {in_size:,} → {out_size:,} bytes ({out_size/in_size:.1f}x)")

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Upscale video for YouTube Shorts / Instagram Reels (1080×1920)"
    )
    parser.add_argument(
        "--input", "-i", required=True,
        help="Input video file path"
    )
    parser.add_argument(
        "--output", "-o", required=True,
        help="Output video file path"
    )
    parser.add_argument(
        "--width", type=int, default=DEFAULT_WIDTH,
        help=f"Target width (default: {DEFAULT_WIDTH})"
    )
    parser.add_argument(
        "--height", type=int, default=DEFAULT_HEIGHT,
        help=f"Target height (default: {DEFAULT_HEIGHT})"
    )
    parser.add_argument(
        "--crf", type=int, default=DEFAULT_CRF,
        help=f"Quality (lower=better, default: {DEFAULT_CRF})"
    )
    parser.add_argument(
        "--preset", default="slow",
        choices=["ultrafast", "superfast", "veryfast", "faster", "fast",
                 "medium", "slow", "slower", "veryslow"],
        help="x264 encoding preset (default: slow)"
    )

    args = parser.parse_args()

    try:
        result = upscale_video(
            input_path=args.input,
            output_path=args.output,
            target_width=args.width,
            target_height=args.height,
            crf=args.crf,
            preset=args.preset,
        )
        print(f"\n🎬 Output: {result}")
    except Exception as e:
        print(f"❌ Upscaling failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
