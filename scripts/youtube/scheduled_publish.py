#!/usr/bin/env python3
"""
scheduled_publish.py — Standalone YouTube publisher that runs via system cron.
No dependency on Clawdbot sessions or heartbeats.

Usage:
  python3 scheduled_publish.py --schedule publish_schedule.json
  python3 scheduled_publish.py --video X --title Y --thumbnail Z  (one-shot)

Schedule JSON format:
[
  {
    "date": "2026-02-04",
    "time": "09:00",
    "timezone": "America/Chicago",
    "video": "output/ninja_content_20260202_124627.mp4",
    "thumbnail": "output/ninja_content_20260202_124627.thumb.png",
    "title": "Video Title #hashtag #shorts",
    "description": "Description here",
    "tags": "tag1,tag2,tag3",
    "privacy": "public",
    "notify_phone": "+19523005404"
  }
]
"""

import argparse
import json
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
SCHEDULE_FILE = PROJECT_DIR / "config" / "publish_schedule.json"
UPLOAD_SCRIPT = SCRIPT_DIR / "youtube_upload.py"
VENV_PYTHON = PROJECT_DIR / ".venv" / "bin" / "python3"


def load_schedule(path):
    with open(path) as f:
        return json.load(f)


def is_due(entry):
    """Check if a scheduled entry is due (within 5 min window)."""
    tz = ZoneInfo(entry.get("timezone", "America/Chicago"))
    now = datetime.now(tz)
    scheduled = datetime.strptime(f"{entry['date']} {entry['time']}", "%Y-%m-%d %H:%M")
    scheduled = scheduled.replace(tzinfo=tz)
    
    diff = (now - scheduled).total_seconds()
    # Due if we're 0-300 seconds past the scheduled time
    return 0 <= diff <= 300


def publish(entry):
    """Upload a video to YouTube."""
    video = PROJECT_DIR / entry["video"]
    thumb = PROJECT_DIR / entry.get("thumbnail", "")
    
    if not video.exists():
        print(f"❌ Video not found: {video}")
        return False
    
    cmd = [
        str(VENV_PYTHON), str(UPLOAD_SCRIPT),
        "--video", str(video),
        "--title", entry["title"],
        "--description", entry.get("description", ""),
        "--tags", entry.get("tags", ""),
        "--privacy", entry.get("privacy", "public"),
    ]
    
    if thumb and Path(thumb).exists():
        cmd.extend(["--thumbnail", str(thumb)])
    
    print(f"📤 Publishing: {entry['title']}")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_DIR))
    
    if result.returncode == 0:
        print(f"✅ Published!")
        print(result.stdout)
        
        # Extract video URL from output
        video_url = ""
        for line in result.stdout.split("\n"):
            if "youtube.com/watch" in line:
                video_url = line.strip().split()[-1] if line.strip() else ""
                break
        
        # Send WhatsApp notification
        if entry.get("notify_phone"):
            notify(entry["notify_phone"], entry["title"], video_url)
        
        return True
    else:
        print(f"❌ Failed: {result.stderr}")
        return False


def notify(phone, title, url=""):
    """Send WhatsApp notification via clawdbot CLI."""
    msg = f"✅ Auto-published: {title}"
    if url:
        msg += f"\n{url}"
    
    try:
        subprocess.run(
            ["clawdbot", "send", "--to", phone, "--message", msg],
            capture_output=True, timeout=30
        )
    except Exception as e:
        print(f"⚠️ Notification failed: {e}")


def mark_published(schedule_path, entry):
    """Mark an entry as published so it doesn't re-fire."""
    schedule = load_schedule(schedule_path)
    for item in schedule:
        if item["date"] == entry["date"] and item["title"] == entry["title"]:
            item["published"] = True
            item["published_at"] = datetime.now().isoformat()
    
    with open(schedule_path, "w") as f:
        json.dump(schedule, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Scheduled YouTube publisher")
    parser.add_argument("--schedule", default=str(SCHEDULE_FILE), help="Schedule JSON file")
    parser.add_argument("--video", help="One-shot: video path")
    parser.add_argument("--title", help="One-shot: video title")
    parser.add_argument("--description", default="", help="One-shot: description")
    parser.add_argument("--tags", default="", help="One-shot: tags")
    parser.add_argument("--thumbnail", help="One-shot: thumbnail path")
    parser.add_argument("--privacy", default="public", help="One-shot: privacy")
    parser.add_argument("--force", action="store_true", help="Publish now regardless of schedule")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be published")
    
    args = parser.parse_args()
    
    # One-shot mode
    if args.video and args.title:
        entry = {
            "video": args.video,
            "title": args.title,
            "description": args.description,
            "tags": args.tags,
            "thumbnail": args.thumbnail or "",
            "privacy": args.privacy,
            "notify_phone": "+19523005404",
        }
        publish(entry)
        return
    
    # Schedule mode
    schedule_path = Path(args.schedule)
    if not schedule_path.exists():
        print(f"No schedule file: {schedule_path}")
        return
    
    schedule = load_schedule(schedule_path)
    
    for entry in schedule:
        if entry.get("published"):
            continue
        
        if args.force or is_due(entry):
            if args.dry_run:
                print(f"🔜 Would publish: {entry['title']} ({entry['date']} {entry['time']})")
                continue
            
            if publish(entry):
                mark_published(schedule_path, entry)
        else:
            tz = ZoneInfo(entry.get("timezone", "America/Chicago"))
            scheduled = datetime.strptime(f"{entry['date']} {entry['time']}", "%Y-%m-%d %H:%M")
            scheduled = scheduled.replace(tzinfo=tz)
            now = datetime.now(tz)
            diff = scheduled - now
            if diff.total_seconds() > 0:
                hours = diff.total_seconds() / 3600
                print(f"⏳ {entry['title']} — in {hours:.1f}h ({entry['date']} {entry['time']})")


if __name__ == "__main__":
    main()
