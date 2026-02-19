#!/usr/bin/env python3
"""
ninja_longform.py — Long-form video assembly pipeline

Assembles a multi-segment video from a script with [SEGMENT] markers.
Avatar segments get Kling lip-sync, B-roll segments get trailer footage overlaid.
All segments are crossfaded together into a single 16:9 landscape video.

Usage:
    python3 scripts/ninja_longform.py --script-file /tmp/feb_games_script.txt \
        --broll-dir output/feb_games/broll \
        --output feb_games_2026
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Add scripts dir to path so we can import from ninja_content
sys.path.insert(0, str(Path(__file__).parent))
from ninja_content import (
    generate_tts,
    generate_kling_avatar_video,
    get_audio_duration,
    ASSETS_DIR,
    OUTPUT_DIR,
    inject_expressive_tags,
)

# Avatar reference image
AVATAR_IMAGE = str(ASSETS_DIR / "reference" / "ninja_helmet_v4_hires.jpg")

# B-roll file mapping: segment label keyword → filename
BROLL_MAP = {
    "NIOH 3": "nioh3.mp4",
    "DRAGON QUEST": "dq7.mp4",
    "MARIO TENNIS": "mario_tennis.mp4",
    "AVOWED": "avowed.mp4",
    "HIGH ON LIFE": "hol2.mp4",
    "RESIDENT EVIL": "re_requiem.mp4",
}


def parse_script(script_path: str) -> list[dict]:
    """Parse a script file into segments.

    Each segment has:
        type: 'avatar' or 'broll'
        label: the segment marker text (e.g. 'GAME 1 - NIOH 3 - BROLL')
        text: the spoken text for the segment
        broll_key: keyword to look up B-roll file (only for broll type)
    """
    text = Path(script_path).read_text()
    segments = []
    # Split on segment markers like [INTRO - AVATAR] or [GAME 1 - NIOH 3 - BROLL]
    parts = re.split(r'\[([^\]]+)\]\n?', text)
    # parts[0] is before first marker (empty), then alternating label, text
    for i in range(1, len(parts), 2):
        label = parts[i].strip()
        spoken = parts[i + 1].strip() if i + 1 < len(parts) else ""
        if not spoken:
            continue

        if "AVATAR" in label:
            segments.append({
                "type": "avatar",
                "label": label,
                "text": spoken,
            })
        elif "BROLL" in label:
            # Find which B-roll file matches
            broll_key = None
            for key in BROLL_MAP:
                if key in label:
                    broll_key = key
                    break
            segments.append({
                "type": "broll",
                "label": label,
                "text": spoken,
                "broll_key": broll_key,
            })
    return segments


def generate_segment_audio(segments: list[dict], work_dir: Path, voice_style: str = "expressive") -> list[dict]:
    """Generate TTS audio for each segment. Returns segments with audio_path and duration added."""
    audio_dir = work_dir / "audio"
    audio_dir.mkdir(exist_ok=True)

    for i, seg in enumerate(segments):
        audio_path = str(audio_dir / f"seg_{i:02d}.mp3")
        print(f"\n--- Segment {i+1}/{len(segments)}: {seg['label']} ---")
        print(f"    Text: {seg['text'][:80]}...")

        result = generate_tts(seg["text"], audio_path, pad_start=0.3, voice_style=voice_style)
        if not result:
            print(f"    FATAL: TTS failed for segment {i}")
            sys.exit(1)

        seg["audio_path"] = audio_path
        seg["duration"] = get_audio_duration(audio_path)
        print(f"    Duration: {seg['duration']:.1f}s")

    return segments


def generate_avatar_clips(segments: list[dict], work_dir: Path, avatar_image: str, kling_model: str = "standard"):
    """Generate Kling Avatar lip-sync clips for avatar segments."""
    avatar_dir = work_dir / "avatar"
    avatar_dir.mkdir(exist_ok=True)

    avatar_segments = [(i, s) for i, s in enumerate(segments) if s["type"] == "avatar"]
    total_avatar_secs = sum(s["duration"] for _, s in avatar_segments)
    cost_per_sec = 0.056 if kling_model == "standard" else 0.115
    est_cost = total_avatar_secs * cost_per_sec

    print(f"\n{'='*60}")
    print(f"AVATAR GENERATION: {len(avatar_segments)} clips, ~{total_avatar_secs:.0f}s total")
    print(f"Estimated cost: ${est_cost:.2f} ({kling_model} model)")
    print(f"{'='*60}")

    for idx, (i, seg) in enumerate(avatar_segments):
        video_path = str(avatar_dir / f"avatar_{i:02d}.mp4")
        print(f"\n  [{idx+1}/{len(avatar_segments)}] {seg['label']} ({seg['duration']:.1f}s)")

        result = generate_kling_avatar_video(
            avatar_image,
            seg["audio_path"],
            video_path,
            model=kling_model,
        )
        if not result:
            print(f"    FATAL: Kling Avatar failed for segment {i}")
            sys.exit(1)

        # Kling output is 1:1 aspect ratio typically - we'll handle scaling in assembly
        seg["video_path"] = video_path

    return segments


def prepare_broll_clips(segments: list[dict], broll_dir: str, work_dir: Path):
    """Prepare B-roll video clips: scale to 1920x1080, trim/loop to match audio duration."""
    broll_work = work_dir / "broll"
    broll_work.mkdir(exist_ok=True)

    for i, seg in enumerate(segments):
        if seg["type"] != "broll":
            continue

        broll_key = seg.get("broll_key")
        if not broll_key or broll_key not in BROLL_MAP:
            print(f"    WARNING: No B-roll mapping for segment {i}: {seg['label']}")
            # Create a black frame fallback
            fallback = str(broll_work / f"broll_{i:02d}.mp4")
            subprocess.run([
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", f"color=c=black:s=1920x1080:d={seg['duration']:.2f}:r=30",
                "-c:v", "libx264", "-crf", "18",
                fallback,
            ], capture_output=True)
            seg["video_path"] = fallback
            continue

        src_file = Path(broll_dir) / BROLL_MAP[broll_key]
        if not src_file.exists():
            print(f"    WARNING: B-roll file not found: {src_file}")
            continue

        output_file = str(broll_work / f"broll_{i:02d}.mp4")
        target_dur = seg["duration"]

        # Get source duration
        probe = subprocess.run([
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "csv=p=0", str(src_file),
        ], capture_output=True, text=True)
        src_dur = float(probe.stdout.strip())

        print(f"    B-roll: {BROLL_MAP[broll_key]} ({src_dur:.1f}s) → {target_dur:.1f}s")

        if src_dur >= target_dur:
            # Trim to duration, ensure 1920x1080, strip audio
            subprocess.run([
                "ffmpeg", "-y",
                "-i", str(src_file),
                "-t", f"{target_dur:.3f}",
                "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
                "-c:v", "libx264", "-crf", "18", "-preset", "fast",
                "-an", output_file,
            ], capture_output=True)
        else:
            # Loop to fill duration
            loops = int(target_dur / src_dur) + 1
            subprocess.run([
                "ffmpeg", "-y",
                "-stream_loop", str(loops),
                "-i", str(src_file),
                "-t", f"{target_dur:.3f}",
                "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
                "-c:v", "libx264", "-crf", "18", "-preset", "fast",
                "-an", output_file,
            ], capture_output=True)

        seg["video_path"] = output_file

    return segments


def scale_avatar_clips(segments: list[dict], work_dir: Path):
    """Scale avatar clips to 1920x1080 (Kling outputs may be different aspect ratios)."""
    scaled_dir = work_dir / "scaled"
    scaled_dir.mkdir(exist_ok=True)

    for i, seg in enumerate(segments):
        if seg["type"] != "avatar":
            continue

        src = seg["video_path"]
        # Check dimensions
        probe = subprocess.run([
            "ffprobe", "-v", "quiet",
            "-show_entries", "stream=width,height",
            "-of", "csv=p=0:s=x", src,
        ], capture_output=True, text=True)
        dims = probe.stdout.strip().split('\n')[0]  # first stream
        w, h = dims.split('x') if 'x' in dims else ("0", "0")

        if w == "1920" and h == "1080":
            continue  # Already correct size

        output = str(scaled_dir / f"avatar_scaled_{i:02d}.mp4")
        print(f"    Scaling avatar segment {i}: {dims} → 1920x1080")

        # Pad to 16:9 with black bars, keeping avatar centered
        subprocess.run([
            "ffmpeg", "-y",
            "-i", src,
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black",
            "-c:v", "libx264", "-crf", "18", "-preset", "fast",
            "-c:a", "copy",
            output,
        ], capture_output=True)
        seg["video_path"] = output

    return segments


def assemble_video(segments: list[dict], work_dir: Path, output_path: str, crossfade: float = 0.5):
    """Assemble all segments into a single video with crossfade transitions."""
    print(f"\n{'='*60}")
    print("ASSEMBLING FINAL VIDEO")
    print(f"{'='*60}")

    # Step 1: For B-roll segments, mux audio onto the video
    muxed_dir = work_dir / "muxed"
    muxed_dir.mkdir(exist_ok=True)

    segment_files = []
    for i, seg in enumerate(segments):
        if seg["type"] == "avatar":
            # Kling avatar already has audio baked in
            segment_files.append(seg["video_path"])
        else:
            # Combine B-roll video + TTS audio
            muxed = str(muxed_dir / f"muxed_{i:02d}.mp4")
            subprocess.run([
                "ffmpeg", "-y",
                "-i", seg["video_path"],
                "-i", seg["audio_path"],
                "-map", "0:v", "-map", "1:a",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                muxed,
            ], capture_output=True)
            segment_files.append(muxed)

    # Step 2: Concatenate with crossfade transitions using ffmpeg xfade
    n = len(segment_files)
    if n == 0:
        print("ERROR: No segments to assemble")
        return None

    if n == 1:
        shutil.copy(segment_files[0], output_path)
        return output_path

    # Get durations for offset calculation
    durations = []
    for f in segment_files:
        probe = subprocess.run([
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "csv=p=0", f,
        ], capture_output=True, text=True)
        durations.append(float(probe.stdout.strip()))

    print(f"    Segments: {n}, Total raw duration: {sum(durations):.1f}s")
    print(f"    Crossfade: {crossfade}s between each segment")

    # Build xfade filter chain
    # For video: [0][1]xfade=offset=O1[v1]; [v1][2]xfade=offset=O2[v2]; ...
    # For audio: [0:a][1:a]acrossfade=d=CF[a1]; [a1][2:a]acrossfade=d=CF[a2]; ...
    inputs = []
    for f in segment_files:
        inputs.extend(["-i", f])

    video_filters = []
    audio_filters = []
    cumulative_offset = 0

    for i in range(n - 1):
        # Video crossfade offset is cumulative duration minus crossfade
        if i == 0:
            cumulative_offset = durations[0] - crossfade
            vin1 = "[0:v]"
            ain1 = "[0:a]"
        else:
            cumulative_offset += durations[i] - crossfade
            vin1 = f"[v{i}]"
            ain1 = f"[a{i}]"

        vin2 = f"[{i+1}:v]"
        ain2 = f"[{i+1}:a]"

        if i == n - 2:
            vout = "[vout]"
            aout = "[aout]"
        else:
            vout = f"[v{i+1}]"
            aout = f"[a{i+1}]"

        video_filters.append(
            f"{vin1}{vin2}xfade=transition=fade:duration={crossfade}:offset={cumulative_offset:.3f}{vout}"
        )
        audio_filters.append(
            f"{ain1}{ain2}acrossfade=d={crossfade}:c1=tri:c2=tri{aout}"
        )

    filter_complex = ";".join(video_filters + audio_filters)

    print(f"    Expected final duration: ~{sum(durations) - crossfade * (n-1):.1f}s")
    print(f"    Running ffmpeg assembly...")

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        print(f"    ffmpeg assembly failed (code {result.returncode})")
        print(f"    stderr: {result.stderr[-500:]}")
        # Fallback: simple concat without crossfade
        print("    Falling back to simple concatenation...")
        return assemble_concat_fallback(segment_files, output_path)

    size = os.path.getsize(output_path) / 1024 / 1024
    duration = get_audio_duration(output_path)
    print(f"    Final video: {output_path}")
    print(f"    Size: {size:.1f}MB, Duration: {duration:.1f}s")

    return output_path


def assemble_concat_fallback(segment_files: list[str], output_path: str) -> str:
    """Fallback: simple concat demuxer (no crossfade)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for seg in segment_files:
            f.write(f"file '{seg}'\n")
        concat_list = f.name

    # Re-encode all to common format first
    reencoded = []
    for i, seg in enumerate(segment_files):
        out = seg + ".re.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-i", seg,
            "-vf", "scale=1920:1080,setsar=1,fps=30",
            "-c:v", "libx264", "-crf", "18", "-preset", "fast",
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
            out,
        ], capture_output=True)
        reencoded.append(out)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for seg in reencoded:
            f.write(f"file '{seg}'\n")
        concat_list = f.name

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_list,
        "-c:v", "libx264", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        output_path,
    ], capture_output=True)

    os.unlink(concat_list)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Ninja Long-form Video Assembly")
    parser.add_argument("--script-file", required=True, help="Script file with [SEGMENT] markers")
    parser.add_argument("--broll-dir", required=True, help="Directory containing B-roll clips")
    parser.add_argument("--output", default="longform_video", help="Output filename prefix")
    parser.add_argument("--kling-model", default="standard", choices=["standard", "pro"])
    parser.add_argument("--crossfade", type=float, default=0.5, help="Crossfade duration in seconds")
    parser.add_argument("--skip-avatar", action="store_true", help="Skip avatar generation (use existing)")
    parser.add_argument("--work-dir", help="Working directory (default: temp)")
    parser.add_argument("--image", default=AVATAR_IMAGE, help="Avatar image path")
    parser.add_argument("--voice-style", default="expressive",
                        choices=["expressive", "natural", "calm"],
                        help="ElevenLabs voice expressiveness: expressive (high energy), natural (balanced), calm (steady)")
    args = parser.parse_args()

    avatar_image = args.image

    print("\n" + "=" * 60)
    print("NINJA LONG-FORM VIDEO PIPELINE")
    print("=" * 60)

    # Step 0: Parse script
    print("\n[STEP 0] Parsing script...")
    segments = parse_script(args.script_file)
    print(f"    Found {len(segments)} segments:")
    for i, s in enumerate(segments):
        print(f"      {i+1}. [{s['type'].upper()}] {s['label']}")

    # Set up working directory
    if args.work_dir:
        work_dir = Path(args.work_dir)
        work_dir.mkdir(parents=True, exist_ok=True)
        cleanup_work = False
    else:
        work_dir = Path(tempfile.mkdtemp(prefix="ninja_longform_"))
        cleanup_work = False  # Keep for debugging
    print(f"    Working dir: {work_dir}")

    # Step 1: Generate TTS for all segments
    print(f"\n[STEP 1] Generating TTS audio for {len(segments)} segments...")
    segments = generate_segment_audio(segments, work_dir, voice_style=args.voice_style)
    total_audio = sum(s["duration"] for s in segments)
    print(f"\n    Total audio duration: {total_audio:.1f}s")

    # Step 2: Generate avatar lip-sync clips
    avatar_count = sum(1 for s in segments if s["type"] == "avatar")
    if avatar_count > 0 and not args.skip_avatar:
        print(f"\n[STEP 2] Generating {avatar_count} avatar lip-sync clips...")
        segments = generate_avatar_clips(segments, work_dir, avatar_image, args.kling_model)
    elif args.skip_avatar:
        print("\n[STEP 2] Skipping avatar generation (--skip-avatar)")
        # Check for existing avatar clips in work dir
        avatar_dir = work_dir / "avatar"
        if avatar_dir.exists():
            for i, seg in enumerate(segments):
                if seg["type"] == "avatar":
                    clip = avatar_dir / f"avatar_{i:02d}.mp4"
                    if clip.exists():
                        seg["video_path"] = str(clip)
                        print(f"    Found existing: {clip}")
    else:
        print("\n[STEP 2] No avatar segments found")

    # Step 3: Prepare B-roll clips
    broll_count = sum(1 for s in segments if s["type"] == "broll")
    if broll_count > 0:
        print(f"\n[STEP 3] Preparing {broll_count} B-roll clips...")
        segments = prepare_broll_clips(segments, args.broll_dir, work_dir)
    else:
        print("\n[STEP 3] No B-roll segments found")

    # Step 4: Scale all clips to 1920x1080
    print("\n[STEP 4] Scaling avatar clips to 1920x1080...")
    segments = scale_avatar_clips(segments, work_dir)

    # Verify all segments have video
    for i, seg in enumerate(segments):
        if "video_path" not in seg:
            print(f"    ERROR: Segment {i} ({seg['label']}) has no video!")
            sys.exit(1)

    # Step 5: Assemble final video
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = str(OUTPUT_DIR / f"{args.output}_{timestamp}.mp4")

    print(f"\n[STEP 5] Assembling final video...")
    result = assemble_video(segments, work_dir, output_path, args.crossfade)

    if result:
        print(f"\n{'='*60}")
        print(f"DONE! Video saved to: {result}")
        print(f"Working directory preserved at: {work_dir}")
        print(f"{'='*60}\n")
    else:
        print("\nERROR: Assembly failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
