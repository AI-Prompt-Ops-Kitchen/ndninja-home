#!/usr/bin/env python3
"""
ninja_thumbnail.py — Generate eye-catching thumbnails using Nano Banana Pro

Usage:
    python ninja_thumbnail.py --topic "Apple's Creator Studio subscriptions"
    python ninja_thumbnail.py --topic "Tesla discontinuing Model S" --style shocked
"""

import argparse
import os
import sys
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = PROJECT_DIR / "output" / "thumbnails"


def generate_thumbnail(topic: str, style: str = "engaging", output_path: str = None, reference_image: str = None):
    """Generate a thumbnail using Nano Banana Pro (Gemini image generation)."""
    
    from google import genai
    from google.genai import types
    from PIL import Image
    import io
    
    # Try AI Studio first (image gen has separate quota from video)
    api_key = os.environ.get('GOOGLE_API_KEY', 'AIzaSyAFQJmUow1dsNqYTXRvEuRVZowzpr8-cXk')
    client = genai.Client(api_key=api_key)
    
    # Default reference image - the Pixar ninja avatar
    if not reference_image:
        reference_image = str(PROJECT_DIR / "assets" / "reference" / "ninja_pixar_avatar.jpg")
    
    # Load reference image if it exists
    ref_image_data = None
    if reference_image and Path(reference_image).exists():
        with open(reference_image, "rb") as f:
            ref_image_data = f.read()
        print(f"   📸 Using reference: {reference_image}")
    
    # Style variations for the ninja character
    style_prompts = {
        "engaging": "looking directly at viewer with interested expression, one hand gesturing toward the topic",
        "shocked": "eyes wide with surprise, hands up in amazement, dramatic reaction",
        "thinking": "hand on chin, contemplative expression, looking slightly upward",
        "pointing": "confidently pointing at the main subject, determined expression",
        "excited": "energetic pose, both hands animated, enthusiastic expression",
    }
    
    ninja_pose = style_prompts.get(style, style_prompts["engaging"])
    
    # Build the thumbnail prompt
    prompt = f"""Create a YouTube thumbnail image with these exact specifications:

SUBJECT: A 3D Pixar-style animated ninja character - cute but cool, expressive large blue eyes, black hood and mask covering lower face, black tactical outfit with gray armor plating and blue LED accents, katana on back. Pixar/Disney animation style with subsurface skin scattering and soft rounded features. {ninja_pose}

COMPOSITION: 
- Character on the right side (1/3 of frame)
- Left 2/3 shows a visual representation of: {topic}
- Bold, eye-catching colors
- High contrast for mobile visibility

STYLE:
- 3D Pixar/Disney animation style (like The Incredibles or Big Hero 6)
- Soft, appealing character design with large expressive eyes
- 16:9 aspect ratio (YouTube thumbnail)
- Clean, uncluttered composition
- Tech/gaming YouTube aesthetic
- Dramatic lighting with blue accent rim lights
- Slightly exaggerated expressions for thumbnail appeal

TEXT: Do NOT include any text in the image - text will be added separately.

Make it scroll-stopping and clickable!"""

    print(f"🎨 Generating thumbnail for: {topic}")
    print(f"   Style: {style}")
    
    try:
        # Build content with reference image if available
        contents = []
        if ref_image_data:
            contents.append(types.Part.from_bytes(data=ref_image_data, mime_type="image/jpeg"))
            contents.append(f"Using this exact ninja character design (same face, outfit, colors), create a thumbnail: {prompt}")
        else:
            contents.append(prompt)
        
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",  # Nano Banana - Gemini image generation
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["image", "text"],
            )
        )
        
        # Extract image from response
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                # Save the image
                OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
                
                if not output_path:
                    # Generate filename from topic + style
                    safe_topic = "".join(c if c.isalnum() else "_" for c in topic[:30])
                    output_path = str(OUTPUT_DIR / f"thumb_{safe_topic}_{style}.png")
                
                with open(output_path, "wb") as f:
                    f.write(part.inline_data.data)
                
                size = os.path.getsize(output_path)
                print(f"   ✅ Thumbnail saved: {output_path} ({size/1024:.0f}KB)")
                return output_path
        
        print("   ❌ No image in response")
        return None
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Generate ninja thumbnails")
    parser.add_argument("--topic", required=True, help="Topic/headline for thumbnail")
    parser.add_argument("--style", default="engaging", 
                        choices=["engaging", "shocked", "thinking", "pointing", "excited"],
                        help="Ninja pose/expression style")
    parser.add_argument("--output", help="Output path for thumbnail")
    parser.add_argument("--reference", help="Custom reference image for the ninja character")
    parser.add_argument("--both", action="store_true", 
                        help="Generate both Pixar avatar AND news anchor thumbnails")
    
    args = parser.parse_args()
    
    if args.both:
        # Generate with default Pixar avatar
        base_output = args.output or f"output/thumbnails/thumb_{args.topic[:20]}_{args.style}"
        pixar_out = base_output.replace('.png', '_pixar.png') if '.png' in str(base_output) else f"{base_output}_pixar.png"
        anchor_out = base_output.replace('.png', '_anchor.png') if '.png' in str(base_output) else f"{base_output}_anchor.png"
        
        print("🎨 Generating BOTH thumbnail variants...")
        generate_thumbnail(args.topic, args.style, pixar_out, None)  # Default Pixar
        generate_thumbnail(args.topic, args.style, anchor_out, 
                          str(Path(__file__).parent.parent / "assets/reference/ninja_news_anchor.jpg"))
    else:
        generate_thumbnail(args.topic, args.style, args.output, args.reference)


if __name__ == "__main__":
    main()
