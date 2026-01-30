#!/usr/bin/env python3
"""
capcut_compose.py — Compose ninja content videos using CapCut HTTP API

Takes the outputs from the ninja content pipeline and creates a professional
CapCut draft with smooth transitions and proper looping.

Usage:
    python capcut_compose.py \
        --video main_video.mp4 \
        --audio voice.mp3 \
        --broll broll1.mp4 broll2.mp4 broll3.mp4 \
        --captions captions.srt \
        --output ninja_draft
        
Requires: CapCut API server running on localhost:9001
    cd /home/ndninja/projects/capcut-api && source venv/bin/activate && python capcut_server.py
"""

import argparse
import json
import os
import subprocess
import sys
import time
import requests
from pathlib import Path

# CapCut API server
CAPCUT_API_URL = "http://127.0.0.1:9000"


def get_media_duration(path: str) -> float:
    """Get duration of media file in seconds."""
    result = subprocess.run([
        "ffprobe", "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "csv=p=0", path
    ], capture_output=True, text=True)
    return float(result.stdout.strip())


def api_call(endpoint: str, data: dict) -> dict:
    """Make API call to CapCut server."""
    url = f"{CAPCUT_API_URL}/{endpoint}"
    try:
        response = requests.post(url, json=data, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ API error ({endpoint}): {e}")
        return {"success": False, "error": str(e)}


def check_server():
    """Check if CapCut API server is running."""
    try:
        response = requests.get(f"{CAPCUT_API_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def start_server():
    """Start CapCut API server in background."""
    print("🚀 Starting CapCut API server...")
    server_cmd = "cd /home/ndninja/projects/capcut-api && source venv/bin/activate && python capcut_server.py"
    process = subprocess.Popen(
        server_cmd,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(3)  # Wait for server to start
    return process


def calculate_broll_insert_points(main_duration: float, num_broll: int) -> list:
    """Calculate evenly spaced B-roll insert points."""
    if num_broll == 0:
        return []
    interval = main_duration / (num_broll + 1)
    return [interval * (i + 1) for i in range(num_broll)]


def compose_ninja_video(
    main_video: str,
    audio_path: str,
    broll_clips: list = None,
    captions_srt: str = None,
    output_name: str = "ninja_draft",
    loop_main: bool = True
):
    """
    Compose a ninja content video using CapCut API.
    
    Args:
        main_video: Path to main ninja avatar video
        audio_path: Path to TTS audio
        broll_clips: List of B-roll video paths
        captions_srt: Path to SRT caption file
        output_name: Name for the output draft
        loop_main: Whether to loop main video to match audio
    """
    print("🎬 CapCut Compose: Starting...")
    
    # Check/start server
    if not check_server():
        server_process = start_server()
        if not check_server():
            print("❌ Could not start CapCut API server")
            return None
    
    # Get durations
    audio_duration = get_media_duration(audio_path)
    main_duration = get_media_duration(main_video)
    
    print(f"   Audio duration: {audio_duration:.1f}s")
    print(f"   Main video duration: {main_duration:.1f}s")
    
    # Resolve absolute paths
    main_video = str(Path(main_video).resolve())
    audio_path = str(Path(audio_path).resolve())
    
    # Create draft (9:16 vertical for shorts/reels)
    print("📋 Creating CapCut draft...")
    result = api_call("create_draft", {
        "width": 1080,
        "height": 1920,
        "name": output_name
    })
    
    if not result.get("success"):
        print(f"❌ Failed to create draft: {result.get('error')}")
        return None
    
    draft_id = result.get("draft_id")
    print(f"   Draft ID: {draft_id}")
    
    # Calculate how many loops needed for main video
    if loop_main and main_duration < audio_duration:
        num_loops = int(audio_duration / main_duration) + 1
        print(f"   Main video will loop {num_loops} times")
    else:
        num_loops = 1
    
    # Add main video track (with looping via multiple segments)
    print("🎥 Adding main video track...")
    current_time = 0
    for i in range(num_loops):
        segment_duration = min(main_duration, audio_duration - current_time)
        if segment_duration <= 0:
            break
        
        # Add transition on loop points (not first segment)
        transition = "Fade" if i > 0 else None
        
        result = api_call("add_video", {
            "draft_id": draft_id,
            "video_url": f"file://{main_video}",
            "start": 0,
            "end": segment_duration,
            "target_start": current_time,
            "width": 1080,
            "height": 1920,
            "volume": 0,  # Mute original video audio
            "transition": transition,
            "transition_duration": 0.5 if transition else 0,
            "track_name": "main_video"
        })
        
        if result.get("success"):
            print(f"   ✅ Segment {i+1}: 0-{segment_duration:.1f}s at {current_time:.1f}s")
        else:
            print(f"   ⚠️ Segment {i+1} warning: {result.get('error', 'unknown')}")
        
        current_time += segment_duration
    
    # Add B-roll clips at insert points
    if broll_clips:
        print(f"🎬 Adding {len(broll_clips)} B-roll clips...")
        insert_points = calculate_broll_insert_points(audio_duration, len(broll_clips))
        
        for i, (broll_path, insert_time) in enumerate(zip(broll_clips, insert_points)):
            broll_path = str(Path(broll_path).resolve())
            broll_duration = min(get_media_duration(broll_path), 4)  # Max 4s per B-roll
            
            result = api_call("add_video", {
                "draft_id": draft_id,
                "video_url": f"file://{broll_path}",
                "start": 0,
                "end": broll_duration,
                "target_start": insert_time,
                "width": 1080,
                "height": 1920,
                "volume": 0,
                "transition": "Fade",
                "transition_duration": 0.3,
                "track_name": f"broll_{i+1}"
            })
            
            if result.get("success"):
                print(f"   ✅ B-roll {i+1} at {insert_time:.1f}s ({broll_duration:.1f}s)")
            else:
                print(f"   ⚠️ B-roll {i+1}: {result.get('error', 'unknown')}")
    
    # Add audio track
    print("🔊 Adding audio track...")
    result = api_call("add_audio", {
        "draft_id": draft_id,
        "audio_url": f"file://{audio_path}",
        "start": 0,
        "end": audio_duration,
        "target_start": 0,
        "volume": 1.0,
        "track_name": "voice"
    })
    
    if result.get("success"):
        print("   ✅ Audio added")
    else:
        print(f"   ⚠️ Audio: {result.get('error', 'unknown')}")
    
    # Add captions if provided
    if captions_srt and Path(captions_srt).exists():
        print("📝 Adding captions...")
        captions_srt = str(Path(captions_srt).resolve())
        result = api_call("add_subtitle", {
            "draft_id": draft_id,
            "subtitle_url": f"file://{captions_srt}",
            "font_size": 42,
            "font_color": "#FFFFFF"
        })
        
        if result.get("success"):
            print("   ✅ Captions added")
        else:
            print(f"   ⚠️ Captions: {result.get('error', 'unknown')}")
    
    # Save draft
    print("💾 Saving draft...")
    result = api_call("save_draft", {
        "draft_id": draft_id
    })
    
    draft_path = result.get("draft_path", f"dfd_{draft_id}")
    
    print(f"\n✅ Draft saved!")
    print(f"   Draft ID: {draft_id}")
    print(f"   Path: {draft_path}")
    print(f"   Duration: {audio_duration:.1f}s")
    print(f"\n📂 To open in CapCut:")
    print(f"   Copy {draft_path} to your CapCut drafts folder")
    
    return {
        "draft_id": draft_id,
        "draft_path": draft_path,
        "duration": audio_duration,
        "success": True
    }


def main():
    parser = argparse.ArgumentParser(description="Compose ninja videos with CapCut")
    parser.add_argument("--video", "-v", required=True, help="Main video path")
    parser.add_argument("--audio", "-a", required=True, help="Audio path")
    parser.add_argument("--broll", "-b", nargs="*", help="B-roll video paths")
    parser.add_argument("--captions", "-c", help="Captions SRT path")
    parser.add_argument("--output", "-o", default="ninja_draft", help="Output draft name")
    parser.add_argument("--no-loop", action="store_true", help="Don't loop main video")
    
    args = parser.parse_args()
    
    result = compose_ninja_video(
        main_video=args.video,
        audio_path=args.audio,
        broll_clips=args.broll,
        captions_srt=args.captions,
        output_name=args.output,
        loop_main=not args.no_loop
    )
    
    if result:
        print(json.dumps(result, indent=2))
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
