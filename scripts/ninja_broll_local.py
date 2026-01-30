#!/usr/bin/env python3
"""
ninja_broll_local.py — Generate B-roll locally using RTX 4090

Uses CogVideoX-5B or Stable Video Diffusion for local generation.
Drop-in replacement for ninja_broll_veo.py on GPU machines.

Usage:
    python ninja_broll_local.py --script "Script text" --output broll_clips/
    python ninja_broll_local.py --topics "chip,server,data center" --output broll/
    python ninja_broll_local.py --image reference.jpg --output broll/  # SVD mode
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional

# Try to import video generation libraries
COGVIDEO_AVAILABLE = False
SVD_AVAILABLE = False

try:
    from diffusers import CogVideoXPipeline
    from diffusers.utils import export_to_video
    import torch
    COGVIDEO_AVAILABLE = True
except ImportError:
    pass

try:
    from diffusers import StableVideoDiffusionPipeline
    from diffusers.utils import load_image, export_to_video
    import torch
    SVD_AVAILABLE = True
except ImportError:
    pass


def extract_topics_from_script(script_text: str, max_topics: int = 4) -> List[str]:
    """Extract visual topics from script (same as ninja_broll_veo.py)."""
    import re
    
    # Simple extraction - can be enhanced with LLM
    stop_words = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'hey', 'ninjas', 'ninja', 'just', 'really', 'actually',
    }
    
    # Find multi-word capitalized phrases
    phrases = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b', script_text)
    
    # Find tech terms
    tech_terms = re.findall(r'\b([A-Z][a-zA-Z]*\s*[0-9]+(?:\s*(?:Pro|Max|Ultra))?)\b', script_text)
    
    topics = []
    seen = set()
    for term in phrases + tech_terms:
        term_clean = term.strip()
        term_lower = term_clean.lower()
        if term_lower not in stop_words and term_lower not in seen and len(term_clean) > 2:
            topics.append(term_clean)
            seen.add(term_lower)
    
    return topics[:max_topics] if topics else ["technology", "digital", "innovation", "future"][:max_topics]


def topic_to_prompt(topic: str) -> str:
    """Convert topic to video generation prompt."""
    NO_TEXT = "no text, no logos, no words, photorealistic"
    
    mappings = {
        'chip': f'Macro shot of silicon microchips on circuit board, blue LED lighting, {NO_TEXT}',
        'memory': f'Close-up of RAM modules and memory chips, tech lighting, {NO_TEXT}',
        'server': f'Data center server racks with blinking lights, blue ambient glow, {NO_TEXT}',
        'data center': f'Modern data center corridor, server racks, cool blue lighting, {NO_TEXT}',
        'ai': f'Abstract neural network visualization, flowing data particles, {NO_TEXT}',
        'gpu': f'High-end graphics card with RGB lighting, tech aesthetic, {NO_TEXT}',
        'samsung': f'Semiconductor manufacturing clean room, silicon wafers, {NO_TEXT}',
        'nvidia': f'GPU chip close-up with green ambient lighting, tech aesthetic, {NO_TEXT}',
    }
    
    topic_lower = topic.lower()
    for key, prompt in mappings.items():
        if key in topic_lower:
            return prompt
    
    return f"Cinematic B-roll of {topic}, professional lighting, shallow depth of field, {NO_TEXT}"


class CogVideoGenerator:
    """Generate video using CogVideoX-5B."""
    
    def __init__(self):
        print("🔧 Loading CogVideoX-5B (this may take a minute)...")
        self.pipe = CogVideoXPipeline.from_pretrained(
            "THUDM/CogVideoX-5b",
            torch_dtype=torch.bfloat16
        ).to("cuda")
        
        # Memory optimizations for 24GB
        self.pipe.enable_model_cpu_offload()
        self.pipe.vae.enable_tiling()
        print("✅ CogVideoX ready!")
    
    def generate(self, prompt: str, output_path: str, duration: int = 5) -> Optional[str]:
        """Generate a video clip."""
        print(f"   🎬 Generating: {prompt[:50]}...")
        
        try:
            # CogVideoX generates at 8fps, so duration * 8 + 1 frames
            num_frames = min(49, duration * 8 + 1)  # Max 49 frames
            
            start = time.time()
            video = self.pipe(
                prompt=prompt,
                num_frames=num_frames,
                guidance_scale=6,
                num_inference_steps=50,
            ).frames[0]
            
            export_to_video(video, output_path, fps=8)
            elapsed = time.time() - start
            
            print(f"   ✅ Saved: {output_path} ({elapsed:.1f}s)")
            return output_path
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            return None


class SVDGenerator:
    """Generate video using Stable Video Diffusion (image-to-video)."""
    
    def __init__(self):
        print("🔧 Loading Stable Video Diffusion...")
        self.pipe = StableVideoDiffusionPipeline.from_pretrained(
            "stabilityai/stable-video-diffusion-img2vid-xt",
            torch_dtype=torch.float16,
            variant="fp16"
        ).to("cuda")
        
        self.pipe.enable_model_cpu_offload()
        print("✅ SVD ready!")
    
    def generate(self, image_path: str, output_path: str, duration: int = 4) -> Optional[str]:
        """Generate video from image."""
        print(f"   🎬 Generating from: {image_path}")
        
        try:
            image = load_image(image_path)
            image = image.resize((1024, 576))  # SVD resolution
            
            start = time.time()
            frames = self.pipe(
                image,
                decode_chunk_size=8,
                num_frames=25,  # ~4 seconds at 6fps
            ).frames[0]
            
            export_to_video(frames, output_path, fps=6)
            elapsed = time.time() - start
            
            print(f"   ✅ Saved: {output_path} ({elapsed:.1f}s)")
            return output_path
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            return None


def generate_broll_clips(script_text: str, output_dir: str, num_clips: int = 4,
                         duration: int = 5, model: str = "auto") -> List[Dict]:
    """Generate B-roll clips locally."""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Select model
    if model == "auto":
        if COGVIDEO_AVAILABLE:
            model = "cogvideo"
        elif SVD_AVAILABLE:
            print("⚠️ CogVideoX not available, SVD requires input images")
            return []
        else:
            print("❌ No video generation model available!")
            print("   Run: python local_broll_setup.py --install cogvideo")
            return []
    
    # Extract topics
    topics = extract_topics_from_script(script_text, num_clips)
    print(f"📋 Topics: {topics}")
    
    # Initialize generator
    if model == "cogvideo":
        generator = CogVideoGenerator()
    else:
        print("❌ Unsupported model for text-to-video")
        return []
    
    # Generate clips
    results = []
    for i, topic in enumerate(topics):
        prompt = topic_to_prompt(topic)
        clip_path = str(output_path / f"broll_{i+1}.mp4")
        
        print(f"\n📹 Clip {i+1}/{len(topics)}: {topic}")
        
        if generator.generate(prompt, clip_path, duration):
            results.append({
                "topic": topic,
                "prompt": prompt,
                "path": clip_path,
                "duration": duration,
            })
    
    # Save manifest
    manifest_path = output_path / "broll_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Generated {len(results)} B-roll clips")
    return results


def main():
    parser = argparse.ArgumentParser(description="Generate B-roll locally with GPU")
    parser.add_argument("--script", help="Script text to extract topics from")
    parser.add_argument("--script-file", help="File containing script")
    parser.add_argument("--topics", help="Comma-separated topics")
    parser.add_argument("--output", "-o", required=True, help="Output directory")
    parser.add_argument("--num-clips", "-n", type=int, default=4, help="Number of clips")
    parser.add_argument("--duration", "-d", type=int, default=5, help="Clip duration (seconds)")
    parser.add_argument("--model", choices=["auto", "cogvideo", "svd"], default="auto")
    
    args = parser.parse_args()
    
    # Get script text
    if args.script:
        script_text = args.script
    elif args.script_file:
        with open(args.script_file) as f:
            script_text = f.read()
    elif args.topics:
        script_text = args.topics  # Will be parsed as topics
    else:
        print("❌ Provide --script, --script-file, or --topics")
        return
    
    # Check GPU
    if not COGVIDEO_AVAILABLE and not SVD_AVAILABLE:
        print("❌ No video generation models available!")
        print("   Install with: python local_broll_setup.py --install cogvideo")
        return
    
    generate_broll_clips(script_text, args.output, args.num_clips, args.duration, args.model)


if __name__ == "__main__":
    main()
