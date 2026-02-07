#!/usr/bin/env python3
"""
ninja_multiclip.py — Generate multiple varied clips for more natural looping

Generates 3-4 different 8-second clips with varied movements and stitches them together.
Results in ~30 seconds of unique footage that only needs to loop once for 60s videos.
"""

import os
import sys
import time
import tempfile
import subprocess
import requests
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from google import genai
from google.genai import types


def get_api_key():
    return os.environ.get('GOOGLE_API_KEY', '')


def get_client(use_vertex=False):
    """Get genai client - either AI Studio (API key) or Vertex AI."""
    if use_vertex:
        # Use Vertex AI with gcloud auth
        project = os.environ.get('GOOGLE_CLOUD_PROJECT', 'gen-lang-client-0601509945')
        location = os.environ.get('GOOGLE_CLOUD_LOCATION', 'us-central1')
        print(f"   🔧 Using Vertex AI (project={project}, location={location})")
        return genai.Client(vertexai=True, project=project, location=location)
    else:
        # Use AI Studio with API key
        print(f"   🔧 Using AI Studio (API key)")
        return genai.Client(api_key=get_api_key())


def generate_clip(client, prompt, reference_image, output_path, duration=8):
    """Generate a single video clip."""
    
    # Load reference image
    with open(reference_image, "rb") as f:
        image_bytes = f.read()
    image = types.Image(image_bytes=image_bytes, mime_type="image/jpeg")
    
    op = client.models.generate_videos(
        model="veo-3.1-generate-preview",
        prompt=prompt,
        image=image,
        config=types.GenerateVideosConfig(
            aspect_ratio="9:16",
            duration_seconds=duration,
        ),
    )
    
    while not op.done:
        time.sleep(10)
        op = client.operations.get(op)
    
    if op.result and op.result.generated_videos:
        video = op.result.generated_videos[0]
        
        # Try to get video data - handle both AI Studio and Vertex AI responses
        try:
            # First try: video might have raw data
            if hasattr(video, 'video') and video.video:
                if hasattr(video.video, 'video_bytes') and video.video.video_bytes:
                    with open(output_path, "wb") as f:
                        f.write(video.video.video_bytes)
                    return output_path
                elif hasattr(video.video, 'uri') and video.video.uri:
                    file_uri = video.video.uri.replace(":download?alt=media", "")
                    # For AI Studio, use API key
                    response = requests.get(
                        f"{file_uri}:download",
                        params={"key": get_api_key(), "alt": "media"},
                        stream=True
                    )
                    if response.status_code == 200:
                        with open(output_path, "wb") as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        return output_path
            
            # Debug: print what we got
            print(f"      Debug: video object = {video}")
            print(f"      Debug: video.video = {getattr(video, 'video', 'N/A')}")
            if hasattr(video, 'video') and video.video:
                print(f"      Debug: video.video attrs = {dir(video.video)}")
        except Exception as e:
            print(f"      ❌ Download error: {e}")
    
    return None


def generate_multiclip(reference_image, output_path, num_clips=4, use_vertex=False):
    """Generate multiple varied clips and stitch them together."""
    
    client = get_client(use_vertex=use_vertex)
    
    # Load base prompt from file if available, otherwise use default
    base_prompt = """Medium shot of a tech news commentator seated at a modern studio desk. The host wears a black tactical outfit with gray armor plating and blue accents, black ninja mask covering lower face with striking blue eyes visible. Camera angle: Medium waist-up shot at eye level, showing hands on desk surface and upper body. Studio environment: Contemporary minimalist tech studio, blue accent lighting, soft-focus digital screens in background. Lighting: Soft professional broadcast lighting, subtle blue rim lighting. Style: Photorealistic, cinematic, 4K tech media production quality."""
    
    prompt_file = Path(__file__).parent.parent / "assets/prompts/ninja_commentator_v1.txt"
    if prompt_file.exists():
        content = prompt_file.read_text()
        # Extract just the prompt part (before the ---)
        if "---" in content:
            base_prompt = content.split("---")[0].strip()
            # Remove comment lines
            base_prompt = "\n".join(line for line in base_prompt.split("\n") if not line.strip().startswith("#"))
    
    # Different movement variations while keeping the core look
    prompt_variations = [
        f"""{base_prompt}
        Movement: Relaxed professional posture, hands resting calmly on desk, natural head movements and eye contact with camera, subtle engaged expression. Smooth animation, camera locked.""",
        
        f"""{base_prompt}
        Movement: Leaning slightly forward showing engagement, natural hand gestures on desk surface for emphasis, head movements maintaining eye contact. Smooth animation, camera locked.""",
        
        f"""{base_prompt}
        Movement: Occasional glance to side as if referencing off-screen monitor, then back to camera, subtle nods, one hand gesture rising from desk. Smooth animation, camera locked.""",
        
        f"""{base_prompt}
        Movement: Conversational energy with both hands gesturing above desk surface, expressive eyes, slight body movement showing enthusiasm. Smooth animation, camera locked.""",
    ]
    
    print(f"🎬 Generating {num_clips} varied clips...")
    
    # Save clips to output/clips/ so we can inspect them
    clips_dir = Path(output_path).parent / "clips"
    clips_dir.mkdir(exist_ok=True)
    
    # Use persistent directory instead of temp
    clip_paths = []
    
    for i in range(num_clips):
        prompt = prompt_variations[i % len(prompt_variations)]
        clip_path = str(clips_dir / f"clip_{i+1}.mp4")
        
        print(f"\n   📹 Clip {i+1}/{num_clips}...")
        print(f"      Prompt variation: {i % len(prompt_variations) + 1}")
        result = generate_clip(client, prompt, reference_image, clip_path)
        
        if result:
            clip_paths.append(clip_path)
            size = os.path.getsize(clip_path)
            print(f"      ✅ Generated ({size/1024:.0f}KB)")
        else:
            print(f"      ❌ Failed")
    
    if not clip_paths:
        print("❌ No clips generated")
        return None
    
    # Create concat file in clips dir (use just filenames, not full paths)
    concat_file = str(clips_dir / "concat.txt")
    with open(concat_file, "w") as f:
        for path in clip_paths:
            # Use just the filename since ffmpeg runs from clips dir
            f.write(f"file '{Path(path).name}'\n")
    
    # Concatenate clips using filter_complex (handles keyframes better, no slide artifacts)
    print(f"\n🔗 Stitching {len(clip_paths)} clips together (stripping AI audio)...")
    
    # Build filter_complex command for seamless concat
    inputs = []
    filter_parts = []
    for i, path in enumerate(clip_paths):
        inputs.extend(["-i", path])
        filter_parts.append(f"[{i}:v]")
    
    filter_complex = f"{''.join(filter_parts)}concat=n={len(clip_paths)}:v=1:a=0[outv]"
    
    subprocess.run([
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "medium",
        "-pix_fmt", "yuv420p",
        output_path
    ], capture_output=True)
    
    if os.path.exists(output_path):
        # Get final duration
        result = subprocess.run([
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "csv=p=0", output_path
        ], capture_output=True, text=True)
        duration = float(result.stdout.strip())
        size = os.path.getsize(output_path)
        
        print(f"\n✅ Multi-clip video ready!")
        print(f"   Duration: {duration:.1f}s")
        print(f"   Size: {size/1024:.0f}KB")
        print(f"   Output: {output_path}")
        print(f"   Individual clips saved to: {clips_dir}/")
        
        return output_path
    
    return None


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate multi-clip ninja video")
    parser.add_argument("--image", "-i", required=True, help="Reference image")
    parser.add_argument("--output", "-o", required=True, help="Output video path")
    parser.add_argument("--clips", "-n", type=int, default=4, help="Number of clips (default: 4)")
    parser.add_argument("--vertex", "-v", action="store_true", help="Use Vertex AI instead of AI Studio (higher rate limits)")
    
    args = parser.parse_args()
    
    generate_multiclip(args.image, args.output, args.clips, use_vertex=args.vertex)


if __name__ == "__main__":
    main()
