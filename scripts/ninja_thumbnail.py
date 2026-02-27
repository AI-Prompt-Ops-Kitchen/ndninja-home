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


def _detect_topic_icons(topic: str) -> str:
    """Auto-detect relevant visual icons/elements based on topic keywords."""
    topic_lower = topic.lower()
    
    icon_rules = [
        # Gaming
        (["gaming", "game", "steam", "xbox", "playstation", "nintendo", "console", "esports"],
         "Include prominent 3D game controller, gaming headset, or console icons as visual anchors"),
        (["valve", "steam machine", "steam deck"],
         "Include a stylized Steam logo icon and gaming PC/console hardware as visual elements"),
        # AI / Tech companies
        (["github", "copilot", "coding", "developer", "code"],
         "Include a glowing code editor screen, GitHub-style octocat silhouette, or floating code brackets as visual elements"),
        (["anthropic", "claude", "chatgpt", "openai", "ai chatbot", "ad-free"],
         "Include AI chat bubble icons, a robot assistant silhouette, and ad/no-ad symbols as visual elements"),
        (["apple", "iphone", "ipad", "mac"],
         "Include a stylized apple silhouette, sleek device outlines as visual elements"),
        (["google", "alphabet"],
         "Include colorful Google-style dots or a search bar icon as visual elements"),
        (["microsoft", "office", "windows"],
         "Include a Microsoft Office grid icon or Windows-style window frames as visual elements"),
        (["tesla", "ev", "electric vehicle", "self-driving"],
         "Include a sleek electric car silhouette with glowing headlights as a visual element"),
        # Security / Hacking
        (["hack", "security", "vulnerability", "exploit", "breach", "cyber", "malware", "patch"],
         "Include a glowing skull icon, lock/shield with crack, or matrix-style falling code as visual threat indicators"),
        (["russia", "russian", "fancy bear", "apt28"],
         "Include a menacing bear silhouette with red glowing eyes and a hacker hood as visual threat elements"),
        # Space
        (["nasa", "space", "rocket", "moon", "mars", "artemis", "spacex"],
         "Include a rocket ship, planet, or astronaut helmet icon as visual elements"),
        # Money / Business
        (["price", "cost", "expensive", "revenue", "billion", "million", "money"],
         "Include floating dollar signs, price tags, or rising/falling chart arrows as visual elements"),
        (["ram", "memory", "chip", "semiconductor", "shortage"],
         "Include glowing RAM sticks, circuit board patterns, or microchip icons as visual elements"),
        # Social / Legal
        (["lawsuit", "court", "judge", "sec", "legal"],
         "Include a gavel, scales of justice, or courtroom silhouette as visual elements"),
        (["super bowl", "ad", "commercial", "advertising"],
         "Include a TV screen icon, megaphone, or spotlight/stadium lights as visual elements"),
        # MTG / Card Games
        (["magic the gathering", "mtg", "secret lair", "trading card"],
         "Include glowing magic cards, mana symbols, or card pack icons as visual elements"),
    ]
    
    matched_icons = []
    for keywords, icon_desc in icon_rules:
        if any(kw in topic_lower for kw in keywords):
            matched_icons.append(icon_desc)
    
    if matched_icons:
        return "IMPORTANT VISUAL ICONS: " + " | ".join(matched_icons[:2])  # Max 2 to avoid clutter
    else:
        return "Include a relevant symbolic icon or visual element that immediately communicates the topic at a glance"


def _extract_headline(topic: str) -> str:
    """Extract a short, punchy headline (3-5 words) from the topic for thumbnail text."""
    topic_lower = topic.lower()
    
    # Common headline patterns based on keywords
    headline_rules = [
        # Version announcements
        (["linux 7", "linux kernel 7"], "LINUX 7.0 IS HERE!"),
        (["linux 6.19"], "LINUX 6.19 DROPS!"),
        (["ios 18", "ios 19"], "NEW iOS UPDATE!"),
        (["android 15", "android 16"], "ANDROID UPDATE!"),
        (["windows 12"], "WINDOWS 12?!"),
        # Gaming
        (["playstation", "ps5", "ps6"], "PLAYSTATION NEWS!"),
        (["xbox", "microsoft gaming"], "XBOX NEWS!"),
        (["nintendo", "switch 2"], "NINTENDO NEWS!"),
        (["state of play"], "STATE OF PLAY!"),
        (["steam", "valve"], "STEAM NEWS!"),
        # AI
        (["chatgpt", "openai"], "CHATGPT UPDATE!"),
        (["claude", "anthropic"], "CLAUDE NEWS!"),
        (["gemini", "google ai"], "GOOGLE AI NEWS!"),
        (["copilot"], "COPILOT UPDATE!"),
        # Companies
        (["apple", "iphone", "mac"], "APPLE NEWS!"),
        (["tesla", "elon"], "TESLA NEWS!"),
        (["google"], "GOOGLE NEWS!"),
        (["microsoft"], "MICROSOFT NEWS!"),
        (["meta", "facebook"], "META NEWS!"),
        (["amazon", "aws"], "AMAZON NEWS!"),
        # Security
        (["hack", "breach", "vulnerability", "exploit"], "SECURITY ALERT!"),
        (["malware", "virus", "ransomware"], "MALWARE WARNING!"),
        # Business
        (["billion", "acquisition", "bought", "sold"], "BIG MONEY MOVE!"),
        (["layoff", "fired", "cut"], "LAYOFFS!"),
        (["lawsuit", "sued", "court"], "LEGAL DRAMA!"),
    ]
    
    for keywords, headline in headline_rules:
        if any(kw in topic_lower for kw in keywords):
            return headline
    
    # Fallback: Create headline from first few significant words
    # Remove common filler words and take first 3-4 words
    filler_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'this', 'that', 'with', 'for', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'of'}
    words = [w for w in topic.split() if w.lower() not in filler_words][:4]
    if words:
        return ' '.join(words).upper() + '!'
    
    return "BREAKING NEWS!"


def generate_thumbnail(topic: str, style: str = "engaging", output_path: str = None, reference_image: str = None):
    """Generate a thumbnail using Nano Banana Pro (Gemini image generation)."""
    
    from google import genai
    from google.genai import types
    from PIL import Image
    import io
    
    # Try AI Studio first (image gen has separate quota from video)
    api_key = os.environ.get('GOOGLE_API_KEY')
    client = genai.Client(api_key=api_key)
    
    # Default reference image - the futuristic newsroom ninja
    if not reference_image:
        reference_image = str(PROJECT_DIR / "assets" / "reference" / "ninja_helmet_v3_futuristic.jpg")
    
    # Load reference image if it exists
    ref_image_data = None
    if reference_image and Path(reference_image).exists():
        with open(reference_image, "rb") as f:
            ref_image_data = f.read()
        print(f"   📸 Using reference: {reference_image}")
    
    # Style variations for the ninja character
    # NOTE: Digital goggles with LED eyes are REQUIRED — expressions come from the goggle eyes
    style_prompts = {
        "engaging": "looking directly at viewer, digital goggle eyes showing curious/interested expression, one hand gesturing toward the topic",
        "shocked": "digital goggle eyes wide with shock/surprise expression, hands up in amazement, dramatic reaction",
        "thinking": "hand on chin, digital goggle eyes showing contemplative/squinting expression, looking slightly upward",
        "pointing": "confidently pointing at the main subject, digital goggle eyes showing determined expression",
        "excited": "energetic pose, both hands animated, digital goggle eyes showing excited/happy expression with upward curved LED eyes",
    }
    
    ninja_pose = style_prompts.get(style, style_prompts["engaging"])
    
    # Auto-detect topic icons/visual elements from keywords
    topic_icons = _detect_topic_icons(topic)
    
    # Extract a short punchy headline (3-5 words max) from the topic
    # This will be displayed prominently on the thumbnail
    headline = _extract_headline(topic)
    
    # Build the thumbnail prompt
    prompt = f"""Create a YouTube thumbnail image with these exact specifications:

SUBJECT: A 3D Pixar-style animated ninja character - cute but cool, wearing DIGITAL GOGGLES/VISOR over eyes with glowing LED digital eyes visible through the goggles (the goggles ARE the character's eyes - no human eyes visible), black hood and mask covering lower face, black tactical outfit with gray armor plating and blue LED accents, katana on back. Pixar/Disney animation style with soft rounded features. {ninja_pose}

CRITICAL: The ninja MUST wear digital goggles/visor - this is the character's signature look. The goggle lenses show expressive digital/LED eyes that convey emotion. No human eyes - only digital goggle eyes.

COMPOSITION:
- Character on the right side (1/3 of frame)
- Left 2/3 shows a visual representation of: {topic}
- {topic_icons}
- Bold, eye-catching colors
- High contrast for mobile visibility

STYLE:
- 3D Pixar/Disney animation style (like The Incredibles or Big Hero 6)
- Soft, appealing character design with expressive digital goggle eyes
- 9:16 vertical aspect ratio (YouTube Shorts thumbnail)
- Clean, uncluttered composition
- Tech/gaming YouTube aesthetic
- Dramatic lighting with blue accent rim lights
- Slightly exaggerated expressions for thumbnail appeal

TEXT ELEMENTS (IMPORTANT - include these in the image):
- Large, bold headline text: "{headline}" - positioned prominently (top or left area), white or bright yellow text with black outline/shadow for readability
- Small "NEURODIVERGENT NINJA" or ninja star logo/branding in corner (subtle but visible)
- Text should be short, punchy, and scroll-stopping
- Use bold sans-serif font style (like Impact or Bebas Neue aesthetic)

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
            model="gemini-3.1-flash-image-preview",  # Nano Banana Pro 2 — Pro quality at Flash speed
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["image", "text"],
                image_config=types.ImageConfig(
                    aspectRatio="9:16",
                ),
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
