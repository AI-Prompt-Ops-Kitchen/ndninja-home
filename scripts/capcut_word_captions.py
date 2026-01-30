#!/usr/bin/env python3
"""
capcut_word_captions.py — Generate CapCut drafts with word-by-word animated captions

Uses Whisper for precise word timing + CapCut API for animated text effects.
"""

import json
import subprocess
import requests
from pathlib import Path

CAPCUT_API = "http://127.0.0.1:9000"


def api_call(endpoint: str, data: dict) -> dict:
    """Make API call to CapCut server."""
    try:
        r = requests.post(f"{CAPCUT_API}/{endpoint}", json=data, timeout=60)
        return r.json()
    except Exception as e:
        print(f"   ❌ API error: {e}")
        return {"success": False, "error": str(e)}


def get_word_timestamps(audio_path: str, original_script: str = None) -> list:
    """Get word-level timestamps using Whisper."""
    import whisper
    
    print("   🎙️ Transcribing with Whisper...")
    model = whisper.load_model("tiny")
    result = model.transcribe(audio_path, word_timestamps=True)
    
    words = []
    for segment in result.get("segments", []):
        for word_info in segment.get("words", []):
            words.append({
                "word": word_info["word"].strip(),
                "start": word_info["start"],
                "end": word_info["end"]
            })
    
    # If original script provided, try to match words (handles transcription errors)
    if original_script:
        script_words = original_script.split()
        if len(script_words) == len(words):
            for i, sw in enumerate(script_words):
                words[i]["word"] = sw
    
    return words


def generate_capcut_draft_with_word_captions(
    video_path: str,
    audio_path: str,
    output_name: str = "ninja_draft",
    original_script: str = None,
    font_size: float = 15.0,
    font_color: str = "#FFFFFF",
    highlight_color: str = "#FFD700",  # Gold highlight
    animation: str = "Pop_Up",  # Pop_Up, Karaoke, Typewriter, etc.
    position_y: float = -0.75,  # Bottom of screen
    broll_clips: list = None
):
    """
    Create CapCut draft with word-by-word animated captions.
    
    Args:
        video_path: Main video file
        audio_path: Audio file (for Whisper transcription)
        output_name: Draft name
        original_script: Original script text (for accurate words)
        font_size: Caption font size (8-20 recommended)
        font_color: Main text color
        highlight_color: Active word highlight color
        animation: Text animation type (Pop_Up, Karaoke, Typewriter, etc.)
        position_y: Vertical position (-1 to 1, negative = bottom)
        broll_clips: Optional B-roll video paths
    """
    print("📋 Creating CapCut draft with word-by-word captions...")
    
    # Check server
    try:
        requests.get(f"{CAPCUT_API}/", timeout=3)
    except:
        print("   ❌ CapCut API server not running!")
        return None
    
    # Get word timestamps
    words = get_word_timestamps(audio_path, original_script)
    print(f"   Found {len(words)} words")
    
    if not words:
        print("   ❌ No words transcribed!")
        return None
    
    # Get media durations
    audio_duration = float(subprocess.run([
        "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
        "-of", "csv=p=0", audio_path
    ], capture_output=True, text=True).stdout.strip())
    
    video_duration = float(subprocess.run([
        "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
        "-of", "csv=p=0", video_path
    ], capture_output=True, text=True).stdout.strip())
    
    # Create draft
    result = api_call("create_draft", {"width": 1080, "height": 1920, "name": output_name})
    if not result.get("success"):
        print(f"   ❌ Failed to create draft: {result.get('error')}")
        return None
    
    output = result.get("output", {})
    draft_id = output.get("draft_id") if isinstance(output, dict) else None
    if not draft_id:
        print(f"   ❌ No draft_id in response")
        return None
    
    print(f"   Draft ID: {draft_id}")
    
    # Add video track (loop if needed)
    print("🎥 Adding video track...")
    video_path_abs = str(Path(video_path).resolve())
    num_loops = int(audio_duration / video_duration) + 1
    current_time = 0
    
    for i in range(num_loops):
        segment_dur = min(video_duration, audio_duration - current_time)
        if segment_dur <= 0:
            break
        
        api_call("add_video", {
            "draft_id": draft_id,
            "video_url": f"file://{video_path_abs}",
            "start": 0,
            "end": segment_dur,
            "target_start": current_time,
            "volume": 0,
            "transition": "Fade" if i > 0 else None,
            "transition_duration": 0.3 if i > 0 else 0,
            "track_name": "main_video"
        })
        current_time += segment_dur
    
    # Add B-roll clips if provided
    if broll_clips:
        print(f"🎬 Adding {len(broll_clips)} B-roll clips...")
        interval = audio_duration / (len(broll_clips) + 1)
        for i, broll_path in enumerate(broll_clips):
            insert_time = interval * (i + 1)
            broll_path_abs = str(Path(broll_path).resolve())
            broll_dur = min(4, float(subprocess.run([
                "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                "-of", "csv=p=0", broll_path
            ], capture_output=True, text=True).stdout.strip()))
            
            api_call("add_video", {
                "draft_id": draft_id,
                "video_url": f"file://{broll_path_abs}",
                "start": 0,
                "end": broll_dur,
                "target_start": insert_time,
                "volume": 0,
                "transition": "Fade",
                "transition_duration": 0.3,
                "track_name": f"broll_{i+1}"
            })
    
    # Add audio track
    print("🔊 Adding audio track...")
    audio_path_abs = str(Path(audio_path).resolve())
    api_call("add_audio", {
        "draft_id": draft_id,
        "audio_url": f"file://{audio_path_abs}",
        "start": 0,
        "end": audio_duration,
        "target_start": 0,
        "volume": 1.0,
        "track_name": "voice"
    })
    
    # Add word-by-word captions with animations
    print(f"📝 Adding {len(words)} word captions with {animation} animation...")
    
    for i, word_info in enumerate(words):
        word = word_info["word"]
        start = word_info["start"]
        end = word_info["end"]
        
        # Extend end time slightly for readability
        display_end = min(end + 0.1, words[i+1]["start"] if i+1 < len(words) else audio_duration)
        
        result = api_call("add_text", {
            "draft_id": draft_id,
            "text": word,
            "start": start,
            "end": display_end,
            "font_size": font_size,
            "font_color": font_color,
            "transform_y": position_y,
            "transform_x": 0,
            "track_name": f"word_{i}",
            "intro_animation": animation,
            "intro_duration": min(0.15, (end - start) / 2),  # Quick animation
            "background_color": "#000000",
            "background_alpha": 0.5,
            "border_color": "#000000",
            "border_width": 2.0
        })
        
        if (i + 1) % 10 == 0:
            print(f"   ... {i+1}/{len(words)} words added")
    
    print(f"   ✅ All {len(words)} words added!")
    
    # Save draft
    print("💾 Saving draft...")
    result = api_call("save_draft", {"draft_id": draft_id})
    
    print(f"\n✅ CapCut draft created with word-by-word captions!")
    print(f"   Draft ID: {draft_id}")
    print(f"   Words: {len(words)}")
    print(f"   Animation: {animation}")
    
    return draft_id


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate CapCut draft with word captions")
    parser.add_argument("--video", "-v", required=True, help="Video path")
    parser.add_argument("--audio", "-a", required=True, help="Audio path")
    parser.add_argument("--script", "-s", help="Original script text")
    parser.add_argument("--output", "-o", default="ninja_draft", help="Draft name")
    parser.add_argument("--animation", default="Pop_Up", help="Animation type")
    parser.add_argument("--font-size", type=float, default=15.0, help="Font size")
    
    args = parser.parse_args()
    
    generate_capcut_draft_with_word_captions(
        args.video,
        args.audio,
        args.output,
        args.script,
        font_size=args.font_size,
        animation=args.animation
    )
