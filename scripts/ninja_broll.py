#!/usr/bin/env python3
"""
ninja_broll.py — Generate topic-relevant B-roll for ninja content

Hybrid approach:
1. Ken Burns images (Nano Banana Pro) — logos, concepts, UI
2. Stock footage (Pexels API) — real-world scenes
3. Veo video clips (optional) — dynamic/futuristic

Usage:
    python ninja_broll.py --script "Script text" --output broll_clips/
    python ninja_broll.py --topics "Apple,Final Cut Pro,iPad" --output broll_clips/
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import requests
from pathlib import Path
from typing import List, Dict, Optional

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = PROJECT_DIR / "output" / "broll"

# API Keys
PEXELS_API_KEY = os.environ.get('PEXELS_API_KEY', '')


def extract_topics_from_script(script_text: str) -> List[str]:
    """Extract key topics/entities from script using simple NLP."""
    
    # Common words to ignore
    stop_words = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
        'ought', 'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
        'from', 'as', 'into', 'through', 'during', 'before', 'after', 'above',
        'below', 'between', 'under', 'again', 'further', 'then', 'once', 'here',
        'there', 'when', 'where', 'why', 'how', 'all', 'each', 'few', 'more',
        'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
        'same', 'so', 'than', 'too', 'very', 'just', 'and', 'but', 'if', 'or',
        'because', 'until', 'while', 'this', 'that', 'these', 'those', 'what',
        'which', 'who', 'whom', 'its', 'it', 'they', 'them', 'their', 'we',
        'us', 'our', 'you', 'your', 'he', 'him', 'his', 'she', 'her', 'i', 'me',
        'my', 'about', 'get', 'got', 'getting', 'going', 'go', 'like', 'think',
        'know', 'want', 'take', 'make', 'see', 'look', 'come', 'say', 'said',
        'hey', 'ninjas', 'ninja', 'follow', 'daily', 'briefing', 'hot', 'take'
    }
    
    # Find capitalized phrases (likely proper nouns/names)
    proper_nouns = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', script_text)
    
    # Find quoted terms
    quoted = re.findall(r'"([^"]+)"', script_text)
    
    # Find tech-related terms (often have specific patterns)
    tech_terms = re.findall(r'\b([A-Z][a-zA-Z]*(?:\s*[0-9]+)?(?:\s*(?:Pro|Max|Ultra|Plus|Air))?)\b', script_text)
    
    # Combine and filter
    all_topics = set()
    for topic in proper_nouns + quoted + tech_terms:
        topic_clean = topic.strip()
        topic_lower = topic_clean.lower()
        
        # Skip stop words and short terms
        if topic_lower in stop_words or len(topic_clean) < 3:
            continue
        
        # Skip common sentence starters
        if topic_lower in ['here', 'this', 'that', 'what', 'why', 'how', 'well', 'now']:
            continue
            
        all_topics.add(topic_clean)
    
    # Sort by length (longer = more specific = better)
    topics = sorted(list(all_topics), key=len, reverse=True)
    
    # Return top 5 most specific topics
    return topics[:5]


def generate_kenburns_image(topic: str, output_path: str, style: str = "tech") -> Optional[str]:
    """Generate an image for Ken Burns effect using Nano Banana Pro."""
    
    from google import genai
    from google.genai import types
    
    api_key = os.environ.get('GOOGLE_API_KEY', '')
    client = genai.Client(api_key=api_key)
    
    style_prompts = {
        "tech": "Modern, clean, professional tech aesthetic with blue accent lighting",
        "news": "Professional broadcast news style, dramatic lighting",
        "cinematic": "Cinematic, dramatic, movie-quality visuals",
    }
    
    style_desc = style_prompts.get(style, style_prompts["tech"])
    
    prompt = f"""Create a visually stunning B-roll image for a tech news video about: {topic}

Requirements:
- 16:9 aspect ratio (1920x1080)
- {style_desc}
- NO text or words in the image
- High detail, suitable for slow zoom/pan (Ken Burns effect)
- Professional, broadcast quality
- Should work as background footage for narration

Make it visually interesting with depth and detail for smooth camera movement."""

    print(f"   🎨 Generating image: {topic}")
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_modalities=["image", "text"],
            )
        )
        
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(part.inline_data.data)
                print(f"      ✅ Saved: {output_path}")
                return output_path
        
        print(f"      ❌ No image generated")
        return None
        
    except Exception as e:
        print(f"      ❌ Error: {e}")
        return None


def fetch_pexels_video(query: str, output_path: str, duration: int = 5) -> Optional[str]:
    """Fetch a stock video from Pexels API."""
    
    if not PEXELS_API_KEY:
        print(f"   ⚠️ No Pexels API key, skipping stock footage")
        return None
    
    print(f"   🎬 Searching Pexels: {query}")
    
    try:
        response = requests.get(
            "https://api.pexels.com/videos/search",
            headers={"Authorization": PEXELS_API_KEY},
            params={
                "query": query,
                "per_page": 5,
                "orientation": "landscape",
            }
        )
        
        if response.status_code != 200:
            print(f"      ❌ Pexels API error: {response.status_code}")
            return None
        
        data = response.json()
        if not data.get("videos"):
            print(f"      ❌ No videos found")
            return None
        
        # Find a video with appropriate duration
        for video in data["videos"]:
            if video["duration"] >= duration:
                # Get HD quality file
                video_files = video.get("video_files", [])
                hd_file = None
                for vf in video_files:
                    if vf.get("quality") == "hd" and vf.get("width", 0) >= 1280:
                        hd_file = vf
                        break
                
                if not hd_file and video_files:
                    hd_file = video_files[0]
                
                if hd_file:
                    # Download video
                    video_url = hd_file["link"]
                    print(f"      📥 Downloading: {video_url[:50]}...")
                    
                    vid_response = requests.get(video_url, stream=True)
                    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, "wb") as f:
                        for chunk in vid_response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    print(f"      ✅ Saved: {output_path}")
                    return output_path
        
        print(f"      ❌ No suitable video found")
        return None
        
    except Exception as e:
        print(f"      ❌ Error: {e}")
        return None


def apply_kenburns_effect(image_path: str, output_path: str, duration: float = 5.0, 
                          effect: str = "zoom_in") -> Optional[str]:
    """Apply Ken Burns (pan/zoom) effect to an image using FFmpeg."""
    
    print(f"   🎥 Applying Ken Burns ({effect})...")
    
    # Different Ken Burns effects
    effects = {
        "zoom_in": "scale=8000:-1,zoompan=z='min(zoom+0.0015,1.5)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps=30",
        "zoom_out": "scale=8000:-1,zoompan=z='if(lte(zoom,1.0),1.5,max(1.001,zoom-0.0015))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps=30",
        "pan_left": "scale=8000:-1,zoompan=z='1.2':x='if(lte(on,1),0,x+2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps=30",
        "pan_right": "scale=8000:-1,zoompan=z='1.2':x='if(lte(on,1),iw,x-2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps=30",
    }
    
    frames = int(duration * 30)  # 30 fps
    filter_str = effects.get(effect, effects["zoom_in"]).format(frames=frames)
    
    try:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run([
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", image_path,
            "-vf", filter_str,
            "-t", str(duration),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "18",
            output_path
        ], capture_output=True, text=True)
        
        if result.returncode == 0 and Path(output_path).exists():
            print(f"      ✅ Created: {output_path}")
            return output_path
        else:
            print(f"      ❌ FFmpeg error: {result.stderr[:200]}")
            return None
            
    except Exception as e:
        print(f"      ❌ Error: {e}")
        return None


def generate_broll_clips(script_text: str, output_dir: str, num_clips: int = 3,
                         clip_duration: float = 5.0, use_pexels: bool = True) -> List[Dict]:
    """Generate B-roll clips for a script."""
    
    print("🎬 Generating B-roll clips")
    print("=" * 50)
    
    # Extract topics
    topics = extract_topics_from_script(script_text)
    print(f"\n📋 Extracted topics: {topics}")
    
    if not topics:
        print("❌ No topics extracted from script")
        return []
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    clips = []
    effects = ["zoom_in", "zoom_out", "pan_left", "pan_right"]
    
    for i, topic in enumerate(topics[:num_clips]):
        print(f"\n📹 Clip {i+1}/{num_clips}: {topic}")
        
        clip_info = {
            "topic": topic,
            "index": i,
            "duration": clip_duration,
        }
        
        # Try Pexels first if enabled
        pexels_path = output_path / f"broll_{i+1}_stock.mp4"
        if use_pexels and PEXELS_API_KEY:
            stock_video = fetch_pexels_video(topic, str(pexels_path), int(clip_duration))
            if stock_video:
                # Trim to exact duration
                trimmed_path = output_path / f"broll_{i+1}.mp4"
                subprocess.run([
                    "ffmpeg", "-y", "-i", stock_video,
                    "-t", str(clip_duration),
                    "-c:v", "libx264", "-crf", "18",
                    "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:-1:-1",
                    str(trimmed_path)
                ], capture_output=True)
                clip_info["path"] = str(trimmed_path)
                clip_info["source"] = "pexels"
                clips.append(clip_info)
                continue
        
        # Fall back to generated image + Ken Burns
        image_path = output_path / f"broll_{i+1}.png"
        if generate_kenburns_image(topic, str(image_path)):
            video_path = output_path / f"broll_{i+1}.mp4"
            effect = effects[i % len(effects)]
            if apply_kenburns_effect(str(image_path), str(video_path), clip_duration, effect):
                clip_info["path"] = str(video_path)
                clip_info["source"] = "kenburns"
                clip_info["effect"] = effect
                clips.append(clip_info)
    
    print(f"\n✅ Generated {len(clips)} B-roll clips")
    return clips


def main():
    parser = argparse.ArgumentParser(description="Generate B-roll clips")
    parser.add_argument("--script", help="Script text to extract topics from")
    parser.add_argument("--script-file", help="Script file to read")
    parser.add_argument("--topics", help="Comma-separated topics (instead of extracting)")
    parser.add_argument("--output", default=str(OUTPUT_DIR), help="Output directory")
    parser.add_argument("--clips", type=int, default=3, help="Number of clips to generate")
    parser.add_argument("--duration", type=float, default=5.0, help="Clip duration in seconds")
    parser.add_argument("--no-pexels", action="store_true", help="Don't use Pexels stock footage")
    
    args = parser.parse_args()
    
    # Get script text
    if args.script:
        script_text = args.script
    elif args.script_file:
        script_text = Path(args.script_file).read_text()
    elif args.topics:
        script_text = args.topics  # Will be parsed as topics
    else:
        print("❌ Provide --script, --script-file, or --topics")
        return
    
    clips = generate_broll_clips(
        script_text,
        args.output,
        args.clips,
        args.duration,
        use_pexels=not args.no_pexels
    )
    
    if clips:
        # Save manifest
        manifest_path = Path(args.output) / "broll_manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(clips, f, indent=2)
        print(f"\n📄 Manifest saved: {manifest_path}")


if __name__ == "__main__":
    main()
