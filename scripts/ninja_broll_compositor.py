#!/usr/bin/env python3
"""
ninja_broll_compositor.py — Compose main video with B-roll cutaways

Takes main ninja video + B-roll clips, inserts B-roll at strategic points
to hide loop transitions (freeze frames) and add visual interest.

Usage:
    python ninja_broll_compositor.py --main video.mp4 --broll broll_dir/ --output final.mp4
"""

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import hashlib


def get_video_duration(video_path: str) -> float:
    """Get video duration in seconds."""
    result = subprocess.run([
        "ffprobe", "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "csv=p=0", video_path
    ], capture_output=True, text=True)
    return float(result.stdout.strip())


def detect_freeze_frames(video_path: str, threshold: float = 0.98) -> List[float]:
    """
    Detect freeze frames by comparing consecutive frames.
    Returns list of timestamps where freezes START.
    """
    print("   🔍 Detecting freeze frames...")
    
    freeze_points = []
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Extract frames at 4fps for analysis
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path,
            "-vf", "fps=4,scale=160:90",  # Low res for fast comparison
            f"{tmpdir}/frame_%04d.jpg"
        ], capture_output=True)
        
        frames = sorted(Path(tmpdir).glob("frame_*.jpg"))
        
        if len(frames) < 2:
            return []
        
        # Compare consecutive frames using file hash (fast approximation)
        prev_hash = None
        freeze_start = None
        freeze_count = 0
        
        for i, frame in enumerate(frames):
            # Simple hash-based comparison
            with open(frame, 'rb') as f:
                current_hash = hashlib.md5(f.read()).hexdigest()
            
            if prev_hash is not None:
                if current_hash == prev_hash:
                    # Identical frame detected
                    if freeze_start is None:
                        freeze_start = i / 4.0  # Convert frame index to seconds
                    freeze_count += 1
                else:
                    # Freeze ended
                    if freeze_count >= 2:  # At least 0.5s freeze
                        freeze_points.append(freeze_start)
                        print(f"      Found freeze at {freeze_start:.1f}s (duration: {freeze_count * 0.25:.1f}s)")
                    freeze_start = None
                    freeze_count = 0
            
            prev_hash = current_hash
    
    print(f"   📍 Detected {len(freeze_points)} freeze points")
    return freeze_points


def find_broll_insert_points(main_duration: float, freeze_points: List[float],
                              num_broll: int = 3, min_gap: float = 3.0) -> List[float]:
    """
    Calculate optimal B-roll insert points.
    PRIORITY: Use freeze points (loop seams) first, then fill with even distribution.
    """
    
    padding_start = 1.5  # Don't insert in first 1.5s
    padding_end = 1.5    # Don't insert in last 1.5s
    
    # Filter freeze points to usable range
    usable_freezes = [
        fp for fp in freeze_points 
        if padding_start < fp < (main_duration - padding_end)
    ]
    
    if usable_freezes:
        print(f"   🎯 Using {len(usable_freezes)} freeze points for B-roll insertion")
        # Use freeze points as primary insert locations
        # Limit to num_broll clips
        insert_points = sorted(usable_freezes)[:num_broll]
        
        # If we have fewer freeze points than B-roll clips, fill gaps with even distribution
        if len(insert_points) < num_broll:
            remaining = num_broll - len(insert_points)
            usable_duration = main_duration - padding_start - padding_end
            interval = usable_duration / (remaining + 1)
            
            for i in range(remaining):
                candidate = padding_start + interval * (i + 1)
                # Only add if not too close to existing points
                if all(abs(candidate - ep) > min_gap for ep in insert_points):
                    insert_points.append(candidate)
            
            insert_points = sorted(insert_points)[:num_broll]
        
        print(f"   📍 Insert points: {[f'{p:.1f}s' for p in insert_points]}")
        return insert_points
    
    # Fallback: even distribution if no freeze points detected
    print(f"   ⚠️ No freeze points detected, using even distribution")
    usable_duration = main_duration - padding_start - padding_end
    
    if usable_duration < num_broll * 1.5:
        # Video too short, use fewer insert points
        num_broll = max(1, int(usable_duration / 2))
        print(f"   ⚠️ Video short, reduced to {num_broll} B-roll clips")
    
    if num_broll == 0:
        return []
    
    interval = usable_duration / (num_broll + 1)
    insert_points = [padding_start + interval * (i + 1) for i in range(num_broll)]
    
    print(f"   📍 Even distribution: {num_broll} clips across {main_duration:.1f}s video")
    
    return insert_points


def compose_with_broll(main_video: str, broll_clips: List[str], output_path: str,
                       broll_duration: float = 1.8, crossfade: float = 0.15,
                       loop_clip_duration: float = 2.5) -> Optional[str]:
    """Compose main video with B-roll cutaways at loop seams.
    
    Args:
        loop_clip_duration: Duration of base clip that was looped (to calculate seam positions)
    """
    
    print(f"🎬 Composing video with {len(broll_clips)} B-roll clips")
    
    main_duration = get_video_duration(main_video)
    print(f"   Main video: {main_duration:.1f}s, base clip: {loop_clip_duration:.1f}s")
    
    # Calculate loop seam positions from known clip duration
    # Seams occur at: clip_duration, 2*clip_duration, 3*clip_duration, etc.
    seam_positions = []
    seam_time = loop_clip_duration
    while seam_time < main_duration - 1.0:  # Leave 1s at end
        seam_positions.append(seam_time)
        seam_time += loop_clip_duration
    
    print(f"   🔗 Loop seams at: {[f'{p:.1f}s' for p in seam_positions]}")
    
    # Calculate insert points (use seam positions)
    insert_points = find_broll_insert_points(main_duration, seam_positions, len(broll_clips))
    print(f"   📍 Insert points: {[f'{p:.1f}s' for p in insert_points]}")
    
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
            
            # Main segment before B-roll (video only, no audio)
            main_seg = f"{tmpdir}/main_{i}.mp4"
            seg_duration = insert_point - prev_end + crossfade
            
            subprocess.run([
                "ffmpeg", "-y", "-i", main_video,
                "-ss", str(max(0, prev_end - crossfade if i > 0 else prev_end)),
                "-t", str(seg_duration),
                "-c:v", "libx264", "-crf", "18", "-preset", "fast",
                "-an",  # No audio - we'll add original audio at the end
                main_seg
            ], capture_output=True)
            
            if Path(main_seg).exists() and os.path.getsize(main_seg) > 0:
                segments.append(main_seg)
            
            # Prepare B-roll (ensure 9:16 vertical format)
            broll_seg = f"{tmpdir}/broll_{i}.mp4"
            broll_actual = min(broll_duration, get_video_duration(broll_clips[i]))
            
            subprocess.run([
                "ffmpeg", "-y", "-i", broll_clips[i],
                "-t", str(broll_actual),
                "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:-1:-1,fps=30",
                "-c:v", "libx264", "-crf", "18", "-preset", "fast",
                "-an",  # No audio for B-roll
                broll_seg
            ], capture_output=True)
            
            if Path(broll_seg).exists() and os.path.getsize(broll_seg) > 0:
                segments.append(broll_seg)
                # Update prev_end to account for B-roll duration
                prev_end = insert_point + broll_actual
            else:
                prev_end = insert_point
        
        # Final main segment after last B-roll (video only)
        if prev_end < main_duration:
            final_seg = f"{tmpdir}/main_final.mp4"
            subprocess.run([
                "ffmpeg", "-y", "-i", main_video,
                "-ss", str(max(0, prev_end - crossfade)),
                "-c:v", "libx264", "-crf", "18", "-preset", "fast",
                "-an",  # No audio - we'll add original audio at the end
                final_seg
            ], capture_output=True)
            
            if Path(final_seg).exists() and os.path.getsize(final_seg) > 0:
                segments.append(final_seg)
        
        print(f"   Created {len(segments)} segments")
        
        # Create concat file
        concat_file = f"{tmpdir}/concat.txt"
        with open(concat_file, "w") as f:
            for seg in segments:
                if Path(seg).exists():
                    f.write(f"file '{seg}'\n")
        
        # Extract audio from ORIGINAL main video (before any processing)
        audio_file = f"{tmpdir}/audio_original.wav"
        subprocess.run([
            "ffmpeg", "-y", "-i", main_video,
            "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
            audio_file
        ], capture_output=True)
        
        # Concatenate all video segments (video only, no audio)
        video_only = f"{tmpdir}/video_only.mp4"
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", concat_file,
            "-c:v", "libx264", "-crf", "18", "-preset", "fast",
            "-an",  # Strip all audio from concat
            video_only
        ], capture_output=True)
        
        if not Path(video_only).exists():
            print("   ❌ Video concatenation failed")
            return None
        
        new_duration = get_video_duration(video_only)
        audio_duration = get_video_duration(audio_file) if Path(audio_file).exists() else 0
        print(f"   New video duration: {new_duration:.1f}s, Audio: {audio_duration:.1f}s")
        
        # Combine video with ORIGINAL audio (no re-encoding of audio)
        # Use -shortest to handle any duration mismatch
        subprocess.run([
            "ffmpeg", "-y",
            "-i", video_only,
            "-i", audio_file,
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",  # High quality audio encode
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            "-async", "1",  # Fix audio sync issues
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
    parser.add_argument("--duration", type=float, default=4.0, help="B-roll clip duration (seconds)")
    parser.add_argument("--crossfade", type=float, default=0.3, help="Crossfade duration (seconds)")
    parser.add_argument("--num-clips", type=int, default=None, help="Number of B-roll clips to use")
    
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
    
    if args.num_clips:
        broll_clips = broll_clips[:args.num_clips]
    
    print(f"📂 Found {len(broll_clips)} B-roll clips")
    
    compose_with_broll(args.main, broll_clips, args.output, args.duration, args.crossfade)


if __name__ == "__main__":
    main()
