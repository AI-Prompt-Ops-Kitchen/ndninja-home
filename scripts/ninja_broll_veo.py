#!/usr/bin/env python3
"""
ninja_broll_veo.py — Generate Veo video B-roll for ninja content

Generates short (5s) topical video clips using Veo 3.1 for use as cutaway B-roll.

Usage:
    python ninja_broll_veo.py --script "Script text" --output broll_clips/
    python ninja_broll_veo.py --topics "smartphone,coding,AI" --output broll_clips/
    python ninja_broll_veo.py --topics "Apple logo,developer typing" --count 3
"""

import argparse
import json
import os
import re
import sys
import time
import tempfile
from pathlib import Path
from typing import List, Dict, Optional

from google import genai
from google.genai import types

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = PROJECT_DIR / "output" / "broll"


def get_client():
    """Get Vertex AI client (better rate limits than AI Studio)."""
    project = os.environ.get('GOOGLE_CLOUD_PROJECT', 'gen-lang-client-0601509945')
    location = os.environ.get('GOOGLE_CLOUD_LOCATION', 'us-central1')
    print(f"🔧 Using Vertex AI (project={project}, location={location})")
    return genai.Client(vertexai=True, project=project, location=location)


def extract_topics_from_script(script_text: str, max_topics: int = 3) -> List[str]:
    """Extract key visual topics from script using LLM for intelligent extraction."""
    
    print(f"   🧠 Using LLM to extract {max_topics} visual topics...")
    
    try:
        # Use Gemini Flash for fast, cheap topic extraction
        client = get_client()
        
        prompt = f"""Extract exactly {max_topics} visual topics from this script that would make good B-roll footage.

Rules:
- Focus on CONCRETE, VISUAL concepts (things a camera can film)
- Prefer: technology, objects, places, actions, phenomena
- Avoid: abstract concepts, emotions, generic words like "innovation" or "future"
- Each topic should be 1-4 words, specific enough for video generation
- Return ONLY the topics, one per line, no numbering or bullets

Script:
{script_text}

Visual topics:"""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=100,
            )
        )
        
        # Parse response - one topic per line
        topics = []
        for line in response.text.strip().split('\n'):
            topic = line.strip().strip('-').strip('•').strip('*').strip()
            # Skip empty lines and numbered items
            topic = re.sub(r'^\d+[\.\)]\s*', '', topic)
            if topic and len(topic) >= 2 and len(topic) <= 50:
                topics.append(topic)
        
        if topics:
            print(f"   ✅ Extracted: {topics[:max_topics]}")
            return topics[:max_topics]
        
    except Exception as e:
        print(f"   ⚠️ LLM extraction failed: {e}, falling back to regex")
    
    # Fallback to simple regex extraction
    return _extract_topics_regex(script_text, max_topics)


def _extract_topics_regex(script_text: str, max_topics: int = 3) -> List[str]:
    """Fallback regex-based topic extraction."""
    
    stop_words = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'can', 'need', 'to', 'of', 'in',
        'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through',
        'this', 'that', 'these', 'those', 'what', 'which', 'who', 'it',
        'they', 'them', 'we', 'us', 'you', 'he', 'she', 'i', 'me', 'my',
        'about', 'get', 'got', 'like', 'think', 'know', 'want', 'make',
        'hey', 'ninjas', 'ninja', 'follow', 'daily', 'briefing', 'hot', 'take',
        'just', 'really', 'actually', 'basically', 'literally', 'pretty',
        'new', 'some', 'wild', 'insane', 'excited', 'everything', 'global',
        'almost', 'every', 'change', 'already', 'announced', 'features'
    }
    
    # Find multi-word capitalized phrases first (more specific)
    multi_word = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b', script_text)
    
    # Find tech terms with numbers
    tech_terms = re.findall(r'\b([A-Z][a-zA-Z]*\s*[0-9]+(?:\s*(?:Pro|Max|Ultra|Plus))?)\b', script_text)
    
    # Combine and filter
    all_topics = []
    seen = set()
    for topic in multi_word + tech_terms:
        topic_clean = topic.strip()
        topic_lower = topic_clean.lower()
        
        if topic_lower in stop_words or len(topic_clean) < 3:
            continue
        if topic_lower in seen:
            continue
        
        seen.add(topic_lower)
        all_topics.append(topic_clean)
    
    all_topics.sort(key=len, reverse=True)
    return all_topics[:max_topics]


def topic_to_broll_prompt(topic: str) -> str:
    """Convert a topic into a cinematic B-roll prompt. Avoids text/logos."""
    
    # IMPORTANT: All prompts must include "no text, no logos, no writing"
    NO_TEXT = "no text, no logos, no writing, no words on screen"
    
    # Map common topics to visual prompts
    visual_mappings = {
        'apple': f'Cinematic close-up of sleek consumer electronics on minimalist desk, soft lighting, shallow depth of field, {NO_TEXT}',
        'iphone': f'Smooth tracking shot of modern smartphone on desk, screen glowing softly, modern office environment, {NO_TEXT}',
        'ipad': f'Dramatic reveal of tablet being used for creative work, stylus drawing abstract art, {NO_TEXT}',
        'macbook': f'Elegant laptop in use, abstract colorful display, warm ambient lighting, {NO_TEXT}',
        'ai': f'Futuristic visualization of neural networks and data flowing, blue tech aesthetic, abstract glowing particles, {NO_TEXT}',
        'artificial intelligence': f'Abstract visualization of AI processing, glowing nodes and connections, digital brain, {NO_TEXT}',
        'code': f'Close-up of abstract code patterns on screen, soft keyboard clacking, developer workspace, {NO_TEXT}',
        'coding': f'Hands typing on mechanical keyboard, screen reflecting in glasses, focused developer, {NO_TEXT}',
        'developer': f'Developer workspace with multiple monitors, abstract code patterns, coffee nearby, {NO_TEXT}',
        'google': f'Clean modern tech workspace, bright natural lighting, minimalist design, {NO_TEXT}',
        'microsoft': f'Professional office environment with modern devices, natural lighting, {NO_TEXT}',
        'smartphone': f'Cinematic shot of smartphone being used, soft glow from screen, modern lifestyle, {NO_TEXT}',
        'social media': f'Hands scrolling on phone, engagement visualized as soft glowing particles, {NO_TEXT}',
        'youtube': f'Creator studio setup with ring light, camera, soft ambient lighting, {NO_TEXT}',
        'video': f'Professional video editing timeline abstract view, color grading in progress, {NO_TEXT}',
        'music': f'Audio waveforms visualizing abstractly, headphones, mixing console with soft lighting, {NO_TEXT}',
        'gaming': f'RGB gaming setup, controller in hands, dynamic colorful lighting, {NO_TEXT}',
        'security': f'Abstract lock icons and shields, encrypted data visualization, cyber aesthetic, {NO_TEXT}',
        'privacy': f'Abstract visualization of data protection, glowing shields and barriers, {NO_TEXT}',
        'money': f'Stock charts abstract visualization, financial data as flowing particles, {NO_TEXT}',
        'business': f'Modern corporate office, professionals in meeting, glass walls, natural lighting, {NO_TEXT}',
        'samsung': f'Close-up of memory chips and semiconductors on circuit board, blue tech lighting, {NO_TEXT}',
        'nvidia': f'High-tech GPU with glowing circuits, data center servers, green ambient glow, {NO_TEXT}',
        'chip': f'Macro shot of semiconductor wafer, microchips in production, clean room aesthetic, {NO_TEXT}',
        'memory': f'Close-up of RAM modules and memory chips, circuit board traces, blue tech lighting, {NO_TEXT}',
        'hbm': f'Stacked memory chips visualization, high-bandwidth data flowing, futuristic tech, {NO_TEXT}',
        'data center': f'Server racks with blinking lights, cooling systems, blue ambient lighting, {NO_TEXT}',
        'power plant': f'Industrial facility with cooling towers, steam rising, sunset lighting, {NO_TEXT}',
        'energy': f'Power grid visualization, electricity flowing through lines, dramatic lighting, {NO_TEXT}',
    }
    
    # Check for keyword matches
    topic_lower = topic.lower()
    for key, prompt in visual_mappings.items():
        if key in topic_lower:
            return prompt
    
    # Default: generate a generic cinematic shot avoiding text
    return f"Cinematic B-roll footage of {topic}, professional lighting, shallow depth of field, smooth camera movement, high production value, {NO_TEXT}"


def generate_veo_broll(client, prompt: str, output_path: str, duration: int = 5) -> Optional[str]:
    """Generate a single B-roll video clip using Veo 3.1."""
    
    print(f"   🎬 Generating: {prompt[:60]}...")
    
    try:
        op = client.models.generate_videos(
            model="veo-3.1-generate-preview",
            prompt=prompt,
            config=types.GenerateVideosConfig(
                aspect_ratio="9:16",
                duration_seconds=duration,
            ),
        )
        
        # Poll for completion
        while not op.done:
            print("   ⏳ Waiting for Veo...")
            time.sleep(10)
            op = client.operations.get(op)
        
        if not op.result:
            print(f"   ❌ No result: {op}")
            if hasattr(op, 'error') and op.error:
                print(f"   ❌ Error: {op.error}")
            return None
            
        if not op.result.generated_videos:
            print(f"   ❌ No videos in result: {op.result}")
            return None
        
        video = op.result.generated_videos[0]
        
        # Handle response - video bytes should be directly available
        if hasattr(video, 'video') and video.video:
            if hasattr(video.video, 'video_bytes') and video.video.video_bytes:
                # Direct bytes available
                with open(output_path, 'wb') as f:
                    f.write(video.video.video_bytes)
                print(f"   ✅ Saved: {output_path}")
                return output_path
            elif hasattr(video.video, 'uri') and video.video.uri:
                # Fallback: Download from GCS URI
                import requests
                from google.auth import default
                from google.auth.transport.requests import Request
                
                uri = video.video.uri
                print(f"   📥 Downloading from: {uri[:50]}...")
                
                creds, _ = default()
                creds.refresh(Request())
                
                response = requests.get(uri, headers={
                    'Authorization': f'Bearer {creds.token}'
                })
                
                if response.status_code == 200:
                    with open(output_path, 'wb') as f:
                        f.write(response.content)
                    print(f"   ✅ Saved: {output_path}")
                    return output_path
                else:
                    print(f"   ❌ Download failed: {response.status_code}")
                    return None
            else:
                print(f"   ❌ No video_bytes or URI in response")
                return None
                    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None
    
    return None


def generate_broll_set(topics: List[str], output_dir: Path, duration: int = 5) -> List[Dict]:
    """Generate B-roll clips for a list of topics."""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    client = get_client()
    
    results = []
    for i, topic in enumerate(topics):
        print(f"\n📹 B-roll {i+1}/{len(topics)}: {topic}")
        
        prompt = topic_to_broll_prompt(topic)
        output_path = output_dir / f"broll_{i+1}.mp4"
        
        video_path = generate_veo_broll(client, prompt, str(output_path), duration)
        
        if video_path:
            results.append({
                'topic': topic,
                'prompt': prompt,
                'path': video_path,
                'duration': duration,
                'index': i
            })
        
        # Rate limit buffer between clips
        if i < len(topics) - 1:
            print("   ⏸️  Rate limit pause (30s)...")
            time.sleep(30)
    
    # Save manifest
    manifest_path = output_dir / "broll_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n📋 Manifest saved: {manifest_path}")
    
    return results


def generate_broll_clips(script_text: str, output_dir: str, num_clips: int = 4,
                         duration: int = 6, style: str = "cinematic") -> List[Dict]:
    """
    Generate B-roll clips from script text. 
    Interface matches ninja_broll.py for drop-in replacement.
    
    Returns list of dicts with 'path', 'topic', 'duration' keys.
    """
    print(f"🎬 Generating {num_clips} Veo B-roll clips...")
    
    # Extract topics from script
    topics = extract_topics_from_script(script_text, num_clips)
    
    if not topics:
        print("   ⚠️ No topics extracted, using defaults")
        topics = ["technology", "workspace", "innovation"][:num_clips]
    
    print(f"   Topics: {topics}")
    
    # Generate clips
    output_path = Path(output_dir)
    results = generate_broll_set(topics[:num_clips], output_path, duration)
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Generate Veo video B-roll")
    parser.add_argument('--script', type=str, help='Script text to extract topics from')
    parser.add_argument('--script-file', type=str, help='Path to script file')
    parser.add_argument('--topics', type=str, help='Comma-separated list of topics')
    parser.add_argument('--output', type=str, default=str(OUTPUT_DIR), help='Output directory')
    parser.add_argument('--count', type=int, default=3, help='Number of B-roll clips to generate')
    parser.add_argument('--duration', type=int, default=6, choices=[4, 6, 8], help='Duration of each clip (4, 6, or 8 seconds)')
    
    args = parser.parse_args()
    
    # Get topics
    if args.topics:
        topics = [t.strip() for t in args.topics.split(',')]
    elif args.script:
        topics = extract_topics_from_script(args.script, args.count)
    elif args.script_file:
        with open(args.script_file) as f:
            topics = extract_topics_from_script(f.read(), args.count)
    else:
        print("❌ Must provide --script, --script-file, or --topics")
        sys.exit(1)
    
    if not topics:
        print("❌ No topics found/provided")
        sys.exit(1)
    
    print(f"🎯 Topics: {topics}")
    
    output_dir = Path(args.output)
    results = generate_broll_set(topics[:args.count], output_dir, args.duration)
    
    print(f"\n✅ Generated {len(results)} B-roll clips")
    for r in results:
        print(f"   • {r['topic']}: {r['path']}")


if __name__ == '__main__':
    main()
