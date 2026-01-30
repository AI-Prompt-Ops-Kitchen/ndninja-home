#!/usr/bin/env python3
"""
ninja_broll_compositor.py — Compose main video with B-roll cutaways

Takes main ninja video + B-roll clips, inserts B-roll at strategic points
to hide loop transitions and add visual interest.

Usage:
    python ninja_broll_compositor.py --main video.mp4 --broll broll_dir/ --output final.mp4
"""

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Optional


def get_video_duration(video_path: str) -> float:
    """Get video duration in seconds."""
    result = subprocess.run([
        "ffprobe", "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "csv=p=0", video_path
    ], capture_output=True, text=True)
    return float(result.stdout.strip())


def find_broll_insert_points(main_duration: float, loop_duration: float = 8.0,
                              broll_duration: float = 5.0, num_broll: int = 3) -> List[float]:
    """Calculate optimal points to insert B-roll to hide loop transitions."""
    
    insert_points = []
    
    # Insert B-roll at each loop point (every 8 seconds)
    # Offset slightly before the loop point so the cut feels natural
    current = loop_duration - 1.0  # First insert at ~7 seconds
    
    while len(insert_points) < num_broll and current < main_duration - broll_duration:
        insert_points.append(current)
        current += loop_duration + broll_duration  # Next insert after B-roll plays
    
    return insert_points


def compose_with_broll(main_video: str, broll_clips: List[str], output_path: str,
                       broll_duration: float = 5.0) -> Optional[str]:
    """Compose main video with B-roll cutaways."""
    
    print(f"🎬 Composing video with {len(broll_clips)} B-roll clips")
    
    main_duration = get_video_duration(main_video)
    print(f"   Main video: {main_duration:.1f}s")
    
    # Calculate insert points
    insert_points = find_broll_insert_points(main_duration, 8.0, broll_duration, len(broll_clips))
    print(f"   Insert points: {[f'{p:.1f}s' for p in insert_points]}")
    
    if not insert_points:
        print("   ⚠️ Video too short for B-roll, copying as-is")
        subprocess.run(["cp", main_video, output_path])
        return output_path
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Split main video into segments
        segments = []
        prev_end = 0.0
        
        for i, insert_point in enumerate(insert_points):
            if i >= len(broll_clips):
                break
                
            # Main segment before B-roll
            main_seg = f"{tmpdir}/main_{i}.mp4"
            subprocess.run([
                "ffmpeg", "-y", "-i", main_video,
                "-ss", str(prev_end), "-t", str(insert_point - prev_end),
                "-c:v", "libx264", "-crf", "18", "-c:a", "aac",
                main_seg
            ], capture_output=True)
            segments.append(main_seg)
            
            # Prepare B-roll (ensure same format as main video - 9:16 vertical)
            broll_seg = f"{tmpdir}/broll_{i}.mp4"
            subprocess.run([
                "ffmpeg", "-y", "-i", broll_clips[i],
                "-t", str(broll_duration),
                "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:-1:-1,fps=30",
                "-c:v", "libx264", "-crf", "18",
                "-an",  # No audio for B-roll
                broll_seg
            ], capture_output=True)
            segments.append(broll_seg)
            
            prev_end = insert_point
        
        # Final main segment after last B-roll
        if prev_end < main_duration:
            final_seg = f"{tmpdir}/main_final.mp4"
            subprocess.run([
                "ffmpeg", "-y", "-i", main_video,
                "-ss", str(prev_end),
                "-c:v", "libx264", "-crf", "18", "-c:a", "aac",
                final_seg
            ], capture_output=True)
            segments.append(final_seg)
        
        # Create concat file
        concat_file = f"{tmpdir}/concat.txt"
        with open(concat_file, "w") as f:
            for seg in segments:
                if Path(seg).exists():
                    f.write(f"file '{seg}'\n")
        
        # Get audio from main video (we'll mix it back)
        audio_file = f"{tmpdir}/audio.aac"
        subprocess.run([
            "ffmpeg", "-y", "-i", main_video,
            "-vn", "-c:a", "aac", audio_file
        ], capture_output=True)
        
        # Concatenate all segments
        video_only = f"{tmpdir}/video_only.mp4"
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", concat_file,
            "-c:v", "libx264", "-crf", "18",
            "-an", video_only
        ], capture_output=True)
        
        # Mix audio back (loop/stretch to match new video duration)
        new_duration = get_video_duration(video_only)
        print(f"   New duration: {new_duration:.1f}s")
        
        # Final composition with audio
        subprocess.run([
            "ffmpeg", "-y",
            "-i", video_only,
            "-i", audio_file,
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            output_path
        ], capture_output=True)
    
    if Path(output_path).exists():
        final_duration = get_video_duration(output_path)
        print(f"   ✅ Final video: {output_path} ({final_duration:.1f}s)")
        return output_path
    
    print("   ❌ Composition failed")
    return None


def main():
    parser = argparse.ArgumentParser(description="Compose video with B-roll")
    parser.add_argument("--main", required=True, help="Main video file")
    parser.add_argument("--broll", required=True, help="B-roll directory or manifest JSON")
    parser.add_argument("--output", required=True, help="Output video path")
    parser.add_argument("--duration", type=float, default=5.0, help="B-roll clip duration")
    
    args = parser.parse_args()
    
    # Load B-roll clips
    broll_path = Path(args.broll)
    if broll_path.is_file() and broll_path.suffix == ".json":
        # Load from manifest
        with open(broll_path) as f:
            manifest = json.load(f)
        broll_clips = [item["path"] for item in manifest if "path" in item]
    elif broll_path.is_dir():
        # Find clips in directory
        broll_clips = sorted([str(p) for p in broll_path.glob("broll_*.mp4")])
    else:
        print(f"❌ Invalid B-roll path: {args.broll}")
        return
    
    print(f"📂 Found {len(broll_clips)} B-roll clips")
    
    compose_with_broll(args.main, broll_clips, args.output, args.duration)


if __name__ == "__main__":
    main()
