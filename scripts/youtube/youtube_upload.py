#!/usr/bin/env python3
"""
youtube_upload.py — Upload videos to YouTube with custom thumbnails

Usage:
    python youtube_upload.py --video video.mp4 --title "Title" --description "Desc"
    python youtube_upload.py --video video.mp4 --thumbnail thumb.png --tags "tech,news"
"""

import argparse
import os
import sys
from pathlib import Path

# Add parent for imports
sys.path.insert(0, str(Path(__file__).parent))
from youtube_auth import get_credentials

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


def upload_video(video_path, title, description="", tags=None, thumbnail_path=None, 
                 privacy="private", category_id="20"):  # 20 = Gaming
    """Upload a video to YouTube."""
    
    print(f"🎬 Uploading to YouTube: {title}")
    
    # Get credentials
    creds = get_credentials()
    if not creds:
        print("❌ No valid credentials")
        return None
    
    # Build YouTube API client
    youtube = build('youtube', 'v3', credentials=creds)
    
    # Video metadata
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags or [],
            'categoryId': category_id
        },
        'status': {
            'privacyStatus': privacy,  # 'private', 'unlisted', 'public'
            'selfDeclaredMadeForKids': False
        }
    }
    
    # Upload video (5MB chunks for reliability on large files)
    print(f"   📤 Uploading video...")
    media = MediaFileUpload(video_path, mimetype='video/mp4', resumable=True,
                            chunksize=5 * 1024 * 1024)

    request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )

    response = None
    retries = 0
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                print(f"   📊 Progress: {int(status.progress() * 100)}%")
            retries = 0
        except Exception as e:
            retries += 1
            if retries > 5:
                raise
            print(f"   ⚠️ Chunk upload error (retry {retries}/5): {e}")
            import time
            time.sleep(2 ** retries)
    
    video_id = response['id']
    print(f"   ✅ Video uploaded: https://youtube.com/watch?v={video_id}")
    
    # Upload thumbnail if provided
    if thumbnail_path and Path(thumbnail_path).exists():
        print(f"   🎨 Uploading thumbnail...")
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path, mimetype='image/png')
            ).execute()
            print(f"   ✅ Thumbnail set!")
        except Exception as e:
            print(f"   ⚠️ Thumbnail failed (may need channel verification): {e}")
    
    return video_id


def main():
    parser = argparse.ArgumentParser(description="Upload video to YouTube")
    parser.add_argument("--video", required=True, help="Video file path")
    parser.add_argument("--title", required=True, help="Video title")
    parser.add_argument("--description", default="", help="Video description")
    parser.add_argument("--tags", default="", help="Comma-separated tags")
    parser.add_argument("--thumbnail", help="Thumbnail image path")
    parser.add_argument("--privacy", default="private", 
                        choices=["private", "unlisted", "public"],
                        help="Privacy status")
    
    args = parser.parse_args()
    
    tags = [t.strip() for t in args.tags.split(",")] if args.tags else []
    
    video_id = upload_video(
        args.video,
        args.title,
        args.description,
        tags,
        args.thumbnail,
        args.privacy
    )
    
    if video_id:
        print(f"\n🎉 Success! Video ID: {video_id}")


if __name__ == "__main__":
    main()
