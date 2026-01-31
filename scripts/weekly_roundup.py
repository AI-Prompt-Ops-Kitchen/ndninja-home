#!/usr/bin/env python3
"""
Weekly Roundup Pipeline
Compiles the week's Shorts into a single long-form video (~5 min)

Usage:
    python weekly_roundup.py                    # Auto-select top 5-7 from this week
    python weekly_roundup.py --count 7          # Specify clip count
    python weekly_roundup.py --manual v1.mp4 v2.mp4 ...  # Manual selection
    python weekly_roundup.py --publish youtube  # Upload when done
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from ninja_content import (
    generate_tts_audio,
    generate_kling_avatar_video,
    add_captions_to_video,
    VOICE_CLONE_ID,
    DEFAULT_IMAGE
)

OUTPUT_DIR = Path("output")
SHORTS_DIR = OUTPUT_DIR / "shorts"  # Where daily shorts are saved
ROUNDUP_DIR = OUTPUT_DIR / "roundups"

# Templates
INTRO_SCRIPT = """Welcome back ninjas! It's time for your weekly tech roundup. 
Here are the biggest stories that shaped this week in tech."""

OUTRO_SCRIPT = """And that's your week in tech! If you enjoyed this roundup, 
smash that subscribe button and I'll see you next week. Stay curious, ninjas!"""

TRANSITION_PHRASES = [
    "Next up...",
    "Moving on to our next story...",
    "Here's another big one...",
    "You won't believe this next one...",
    "And speaking of tech news...",
]


def get_shorts_from_week(days_back: int = 7) -> list[Path]:
    """Find all shorts from the past week, sorted by date."""
    if not SHORTS_DIR.exists():
        # Fallback: check main output dir
        search_dir = OUTPUT_DIR
    else:
        search_dir = SHORTS_DIR
    
    cutoff = datetime.now() - timedelta(days=days_back)
    shorts = []
    
    for f in search_dir.glob("*.mp4"):
        # Try to parse date from filename (format: *_YYYYMMDD_*.mp4)
        try:
            stat = f.stat()
            mtime = datetime.fromtimestamp(stat.st_mtime)
            if mtime >= cutoff:
                shorts.append((mtime, f))
        except:
            continue
    
    # Sort by date, newest first
    shorts.sort(key=lambda x: x[0], reverse=True)
    return [s[1] for s in shorts]


def generate_intro_video(output_path: Path) -> Path:
    """Generate the intro segment with avatar."""
    print("🎬 Generating intro segment...")
    
    # Generate TTS
    intro_audio = output_path.parent / "intro_audio.mp3"
    generate_tts_audio(INTRO_SCRIPT, str(intro_audio))
    
    # Generate avatar video
    intro_video = output_path.parent / "intro_raw.mp4"
    generate_kling_avatar_video(
        image_path=DEFAULT_IMAGE,
        audio_path=str(intro_audio),
        output_path=str(intro_video)
    )
    
    # Add captions
    intro_captioned = output_path.parent / "intro_captioned.mp4"
    add_captions_to_video(str(intro_video), str(intro_audio), str(intro_captioned))
    
    return intro_captioned


def generate_outro_video(output_path: Path) -> Path:
    """Generate the outro segment with avatar."""
    print("🎬 Generating outro segment...")
    
    # Generate TTS
    outro_audio = output_path.parent / "outro_audio.mp3"
    generate_tts_audio(OUTRO_SCRIPT, str(outro_audio))
    
    # Generate avatar video
    outro_video = output_path.parent / "outro_raw.mp4"
    generate_kling_avatar_video(
        image_path=DEFAULT_IMAGE,
        audio_path=str(outro_audio),
        output_path=str(outro_video)
    )
    
    # Add captions
    outro_captioned = output_path.parent / "outro_captioned.mp4"
    add_captions_to_video(str(outro_video), str(outro_audio), str(outro_captioned))
    
    return outro_captioned


def create_transition(text: str, output_path: Path, duration: float = 2.0) -> Path:
    """Create a simple text transition card."""
    # Create a dark background with text using FFmpeg
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c=0x1a1a2e:s=1080x1920:d={duration}",
        "-vf", f"drawtext=text='{text}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2:font=Arial",
        "-c:v", "libx264",
        "-t", str(duration),
        str(output_path)
    ]
    subprocess.run(cmd, capture_output=True)
    return output_path


def compile_roundup(
    shorts: list[Path],
    intro: Path,
    outro: Path,
    output_path: Path
) -> Path:
    """Compile all segments into final roundup video."""
    print(f"🎬 Compiling roundup from {len(shorts)} shorts...")
    
    work_dir = output_path.parent / "work"
    work_dir.mkdir(exist_ok=True)
    
    # Build segment list
    segments = [intro]
    
    for i, short in enumerate(shorts):
        # Add transition between shorts (except before first)
        if i > 0:
            transition_text = TRANSITION_PHRASES[i % len(TRANSITION_PHRASES)]
            trans_path = work_dir / f"transition_{i}.mp4"
            create_transition(transition_text, trans_path)
            segments.append(trans_path)
        
        segments.append(short)
    
    segments.append(outro)
    
    # Create concat file
    concat_file = work_dir / "concat.txt"
    with open(concat_file, "w") as f:
        for seg in segments:
            f.write(f"file '{seg.absolute()}'\n")
    
    # Concatenate with FFmpeg
    # First, normalize all videos to same format
    normalized = []
    for i, seg in enumerate(segments):
        norm_path = work_dir / f"norm_{i}.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-i", str(seg),
            "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fps=30",
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "aac", "-ar", "44100", "-ac", "2",
            "-shortest",
            str(norm_path)
        ]
        subprocess.run(cmd, capture_output=True)
        normalized.append(norm_path)
    
    # Update concat file with normalized versions
    with open(concat_file, "w") as f:
        for seg in normalized:
            f.write(f"file '{seg.absolute()}'\n")
    
    # Final concat
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264", "-preset", "medium",
        "-c:a", "aac",
        str(output_path)
    ]
    subprocess.run(cmd, check=True)
    
    print(f"✅ Roundup saved: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generate weekly roundup video")
    parser.add_argument("--count", type=int, default=5, help="Number of shorts to include (default: 5)")
    parser.add_argument("--manual", nargs="+", help="Manually specify short videos to include")
    parser.add_argument("--days", type=int, default=7, help="Look back N days for shorts")
    parser.add_argument("--publish", choices=["youtube"], help="Publish to platform when done")
    parser.add_argument("--title", help="Custom title for the roundup")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be compiled without doing it")
    
    args = parser.parse_args()
    
    # Setup output directory
    ROUNDUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    work_dir = ROUNDUP_DIR / f"roundup_{timestamp}"
    work_dir.mkdir(exist_ok=True)
    
    # Get shorts to include
    if args.manual:
        shorts = [Path(s) for s in args.manual]
    else:
        shorts = get_shorts_from_week(args.days)[:args.count]
    
    if not shorts:
        print("❌ No shorts found! Generate some daily shorts first.")
        sys.exit(1)
    
    print(f"📹 Found {len(shorts)} shorts for roundup:")
    for s in shorts:
        print(f"   - {s.name}")
    
    if args.dry_run:
        print("\n🔍 Dry run - would compile these into roundup")
        return
    
    # Generate segments
    intro = generate_intro_video(work_dir)
    outro = generate_outro_video(work_dir)
    
    # Compile final video
    output_path = ROUNDUP_DIR / f"weekly_roundup_{timestamp}.mp4"
    compile_roundup(shorts, intro, outro, output_path)
    
    # Publish if requested
    if args.publish == "youtube":
        title = args.title or f"This Week in Tech - {datetime.now().strftime('%B %d, %Y')}"
        print(f"📤 Would upload to YouTube: {title}")
        # TODO: Integrate with youtube_upload.py
    
    print(f"\n✅ Weekly roundup complete!")
    print(f"   Output: {output_path}")


if __name__ == "__main__":
    main()
