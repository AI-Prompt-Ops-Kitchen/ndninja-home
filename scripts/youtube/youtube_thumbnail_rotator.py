#!/usr/bin/env python3
"""
youtube_thumbnail_rotator.py — Rotate thumbnails on YouTube videos for A/B testing

Tracks uploaded videos and rotates between thumbnail variants every N hours.

Usage:
    # Register a video with multiple thumbnails
    python youtube_thumbnail_rotator.py --register VIDEO_ID --thumbnails thumb1.png thumb2.png
    
    # Run rotation check (call from cron)
    python youtube_thumbnail_rotator.py --rotate
    
    # List tracked videos
    python youtube_thumbnail_rotator.py --list
    
    # Force rotate a specific video
    python youtube_thumbnail_rotator.py --force VIDEO_ID
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))
from youtube_auth import get_credentials

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# State file for tracking videos and rotation status
STATE_FILE = Path(__file__).parent.parent.parent / "data" / "youtube_thumbnail_state.json"
DEFAULT_ROTATION_HOURS = 48


def load_state():
    """Load rotation state from file."""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"videos": {}, "rotation_hours": DEFAULT_ROTATION_HOURS}


def save_state(state):
    """Save rotation state to file."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


def register_video(video_id: str, thumbnails: list, title: str = None):
    """Register a video for thumbnail rotation."""
    state = load_state()
    
    # Verify thumbnails exist
    valid_thumbnails = []
    for thumb in thumbnails:
        if Path(thumb).exists():
            valid_thumbnails.append(str(Path(thumb).absolute()))
        else:
            print(f"   ⚠️ Thumbnail not found: {thumb}")
    
    if len(valid_thumbnails) < 2:
        print("❌ Need at least 2 valid thumbnails for rotation")
        return False
    
    state["videos"][video_id] = {
        "title": title or video_id,
        "thumbnails": valid_thumbnails,
        "current_index": 0,
        "registered_at": datetime.now().isoformat(),
        "last_rotated": datetime.now().isoformat(),
        "rotation_count": 0,
        "enabled": True
    }
    
    save_state(state)
    print(f"✅ Registered video {video_id} with {len(valid_thumbnails)} thumbnails")
    print(f"   Will rotate every {state['rotation_hours']} hours")
    return True


def set_thumbnail(video_id: str, thumbnail_path: str):
    """Set thumbnail for a YouTube video."""
    creds = get_credentials()
    if not creds:
        print("❌ No valid YouTube credentials")
        return False
    
    youtube = build('youtube', 'v3', credentials=creds)
    
    try:
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_path, mimetype='image/png')
        ).execute()
        return True
    except Exception as e:
        print(f"❌ Failed to set thumbnail: {e}")
        return False


def rotate_thumbnails(force_video_id: str = None):
    """Check all videos and rotate thumbnails if needed."""
    state = load_state()
    rotation_hours = state.get("rotation_hours", DEFAULT_ROTATION_HOURS)
    
    rotated_count = 0
    
    for video_id, video in state["videos"].items():
        if not video.get("enabled", True):
            continue
        
        # Check if this specific video should be forced
        if force_video_id and video_id != force_video_id:
            continue
        
        # Check if rotation is due
        last_rotated = datetime.fromisoformat(video["last_rotated"])
        hours_since = (datetime.now() - last_rotated).total_seconds() / 3600
        
        if hours_since < rotation_hours and not force_video_id:
            print(f"⏭️ {video['title'][:30]}: {rotation_hours - hours_since:.1f}h until next rotation")
            continue
        
        # Get next thumbnail
        thumbnails = video["thumbnails"]
        current_index = video["current_index"]
        next_index = (current_index + 1) % len(thumbnails)
        next_thumbnail = thumbnails[next_index]
        
        print(f"🔄 Rotating {video['title'][:30]}...")
        print(f"   Thumbnail {current_index + 1} → {next_index + 1} of {len(thumbnails)}")
        
        if set_thumbnail(video_id, next_thumbnail):
            video["current_index"] = next_index
            video["last_rotated"] = datetime.now().isoformat()
            video["rotation_count"] = video.get("rotation_count", 0) + 1
            rotated_count += 1
            print(f"   ✅ Rotated! (#{video['rotation_count']} total)")
        else:
            print(f"   ❌ Failed to rotate")
    
    save_state(state)
    return rotated_count


def list_videos():
    """List all tracked videos."""
    state = load_state()
    
    if not state["videos"]:
        print("No videos registered for rotation")
        return
    
    print(f"📋 Tracked Videos (rotating every {state['rotation_hours']}h)")
    print("=" * 60)
    
    for video_id, video in state["videos"].items():
        last_rotated = datetime.fromisoformat(video["last_rotated"])
        hours_ago = (datetime.now() - last_rotated).total_seconds() / 3600
        status = "✅" if video.get("enabled", True) else "⏸️"
        
        print(f"\n{status} {video['title'][:40]}")
        print(f"   ID: {video_id}")
        print(f"   Thumbnails: {len(video['thumbnails'])} variants")
        print(f"   Current: #{video['current_index'] + 1}")
        print(f"   Last rotated: {hours_ago:.1f}h ago")
        print(f"   Total rotations: {video.get('rotation_count', 0)}")


def set_rotation_interval(hours: int):
    """Set the rotation interval in hours."""
    state = load_state()
    state["rotation_hours"] = hours
    save_state(state)
    print(f"✅ Rotation interval set to {hours} hours")


def main():
    parser = argparse.ArgumentParser(description="YouTube thumbnail rotation for A/B testing")
    parser.add_argument("--register", metavar="VIDEO_ID", help="Register a video for rotation")
    parser.add_argument("--thumbnails", nargs="+", help="Thumbnail files for rotation")
    parser.add_argument("--title", help="Video title (for display)")
    parser.add_argument("--rotate", action="store_true", help="Run rotation check")
    parser.add_argument("--force", metavar="VIDEO_ID", help="Force rotate a specific video")
    parser.add_argument("--list", action="store_true", help="List tracked videos")
    parser.add_argument("--interval", type=int, help="Set rotation interval in hours")
    
    args = parser.parse_args()
    
    if args.interval:
        set_rotation_interval(args.interval)
    elif args.register:
        if not args.thumbnails:
            print("❌ --thumbnails required with --register")
            sys.exit(1)
        register_video(args.register, args.thumbnails, args.title)
    elif args.rotate:
        rotated = rotate_thumbnails()
        print(f"\n🔄 Rotated {rotated} video(s)")
    elif args.force:
        rotate_thumbnails(force_video_id=args.force)
    elif args.list:
        list_videos()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
