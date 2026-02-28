#!/usr/bin/env python3
"""
ninja_thumbnail.py — Generate eye-catching thumbnails using Nano Banana 2
Uses JSON structured prompting for consistent output.

Usage:
    python ninja_thumbnail.py --topic "Apple's Creator Studio subscriptions"
    python ninja_thumbnail.py --topic "Tesla discontinuing Model S" --style shocked
    python ninja_thumbnail.py --topic "PS Plus March 2026" --style excited --save-prompt
"""

import argparse
import json
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
        # Gaming — specific services/platforms (check BEFORE generic gaming)
        (["ps plus", "playstation plus", "ps+"],
         "Show a PlayStation 5 console and 3-4 floating game box art covers arranged like a fan. NO cars."),
        (["state of play"],
         "Show a large screen/monitor displaying game trailers with a 'STATE OF PLAY' banner"),
        (["genshin impact", "genshin"],
         "Show Genshin Impact game art — fantasy characters, elemental magic effects, Mondstadt/Liyue scenery"),
        (["wuthering waves", "wuwa"],
         "Show Wuthering Waves game art — sci-fi combat, resonators, glowing energy effects"),
        (["arknights"],
         "Show Arknights game art — tactical RPG units, Rhodes Island operators, dark sci-fi aesthetic"),
        (["gacha", "banner", "pulls", "summon"],
         "Show glowing gacha/summon portal with sparkle effects and character silhouettes emerging"),
        (["fortnite"],
         "Show Fortnite-style colorful battle royale scene with building and action"),
        # Gaming — generic
        (["gaming", "game", "xbox", "playstation", "nintendo", "console", "esports"],
         "Include a 3D game controller and gaming setup as visual anchors. NO cars."),
        (["steam", "valve", "steam deck"],
         "Include a Steam logo icon and gaming PC/Steam Deck hardware"),
        (["switch 2", "nintendo switch"],
         "Show a Nintendo Switch 2 console mockup with Joy-Cons"),
        # AI / Tech companies
        (["github", "copilot", "coding", "developer", "code"],
         "Include a glowing code editor screen or floating code brackets"),
        (["anthropic", "claude", "chatgpt", "openai", "ai chatbot"],
         "Include AI chat bubble icons or a robot assistant silhouette"),
        (["apple", "iphone", "ipad", "mac"],
         "Include a stylized apple silhouette and sleek device outlines"),
        (["google", "alphabet"],
         "Include colorful Google-style dots or a search bar icon"),
        (["microsoft", "office", "windows"],
         "Include a Microsoft Office grid icon or Windows-style frames"),
        (["tesla", "ev", "electric vehicle", "self-driving"],
         "Include a sleek electric car silhouette with glowing headlights"),
        # Security / Hacking
        (["hack", "security", "vulnerability", "exploit", "breach", "cyber", "malware", "patch"],
         "Include a glowing skull icon or lock/shield with crack"),
        # Space
        (["nasa", "space", "rocket", "moon", "mars", "artemis", "spacex"],
         "Include a rocket ship, planet, or astronaut helmet icon"),
        # Money / Business
        (["price", "cost", "expensive", "revenue", "billion", "million", "money"],
         "Include floating dollar signs or price tags"),
        # Social / Legal
        (["lawsuit", "court", "judge", "sec", "legal"],
         "Include a gavel or scales of justice"),
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
    
    # Use the topic itself as the headline base — extract the punchiest 3-5 words.
    # Only use generic fallbacks for truly unrecognizable topics.
    filler_words = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'this', 'that', 'with',
        'for', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'of', 'has', 'have',
        'been', 'just', 'about', 'from', 'its', 'their', 'our', 'my', 'your',
    }
    words = [w for w in topic.split() if w.lower() not in filler_words][:5]
    if words:
        return ' '.join(words).upper() + '!'

    return "BREAKING NEWS!"


def _build_json_prompt(topic: str, style: str, headline: str, topic_icons: str) -> dict:
    """Build a JSON structured prompt for NB2. Returns the prompt dict."""

    # Style → expression + pose mapping
    style_map = {
        "engaging": {
            "expression": "curious/interested digital LED goggle eyes, one hand gesturing toward the topic",
            "pose": "looking directly at viewer, slight lean forward",
        },
        "shocked": {
            "expression": "wide shocked digital LED goggle eyes, mouth agape behind mask",
            "pose": "hands up in amazement, dramatic lean back",
        },
        "thinking": {
            "expression": "contemplative squinting digital LED goggle eyes",
            "pose": "hand on chin, looking slightly upward",
        },
        "pointing": {
            "expression": "determined digital LED goggle eyes",
            "pose": "confidently pointing at the main subject with one arm extended",
        },
        "excited": {
            "expression": "excited upward-curved digital LED goggle eyes, happy glow",
            "pose": "energetic pose, both hands animated, slight jump",
        },
    }

    s = style_map.get(style, style_map["engaging"])

    return {
        "prompt": (
            f"3D Pixar-style animated ninja desk presenter character with DIGITAL GOGGLES/VISOR "
            f"(glowing cyan LED eyes visible through goggles — no human eyes), black hood, "
            f"visible friendly smile below goggles (no face mask), black tactical armor "
            f"with cyan/blue LED accent lines, sitting at a professional streaming desk. "
            f"A premium Rode podcaster microphone on a Rode PSA1 boom arm mount, "
            f"positioned near the character's mouth from the side, like a real YouTube creator setup. "
            f"{s['expression']}. {s['pose']}. "
            f"Character on the right third of frame. Left two-thirds shows a visual "
            f"representation of: {topic}. {topic_icons}. "
            f'Bold headline text: "{headline}" positioned prominently in top or left area, '
            f"white or bright yellow with black outline for readability. "
            f"Small ninja star branding in corner."
        ),
        "negative_prompt": (
            "realistic human eyes, face mask covering mouth, full face covering, "
            "cyberpunk neon city, matrix code, green digital rain, "
            "blurry text, watermark, misspelled text, extra fingers, deformed hands, "
            "low resolution, jpeg artifacts, cluttered background"
        ),
        "style": "3D Pixar/Disney animation (like The Incredibles or Big Hero 6)",
        "composition": {
            "layout": "Character right third, topic visual left two-thirds, headline top area",
            "camera_angle": "Slightly low angle for heroic framing",
            "framing": "Medium shot, waist up for character",
            "lens": "35mm slight wide-angle for energy and depth",
        },
        "lighting": {
            "type": "Dramatic studio with blue accent rim lights",
            "direction": "Three-point: key left, fill right, rim back",
            "consistency": "High contrast for mobile thumbnail visibility",
        },
        "text_elements": {
            "headline": headline,
            "font_style": "Bold sans-serif (Impact/Bebas Neue aesthetic)",
            "color": "White or bright yellow with black outline/shadow",
            "branding": "NEURODIVERGENT NINJA ninja star logo, corner, subtle",
        },
        "resolution": "2K",
        "aspect_ratio": "9:16",
    }


def generate_thumbnail(
    topic: str,
    style: str = "engaging",
    output_path: str = None,
    reference_image: str = None,
    save_prompt: bool = False,
):
    """Generate a thumbnail using Nano Banana 2 with JSON structured prompting."""

    from google import genai
    from google.genai import types

    api_key = os.environ.get("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key)

    # Default reference image
    if not reference_image:
        reference_image = str(
            PROJECT_DIR / "assets" / "reference" / "ninja_desk_presenter.jpeg"
        )

    # Load reference image if it exists
    ref_image_data = None
    if reference_image and Path(reference_image).exists():
        with open(reference_image, "rb") as f:
            ref_image_data = f.read()
        print(f"   Using reference: {reference_image}")

    topic_icons = _detect_topic_icons(topic)
    headline = _extract_headline(topic)

    # Build JSON structured prompt
    json_prompt = _build_json_prompt(topic, style, headline, topic_icons)

    # The actual prompt sent to NB2: JSON structure as a string
    prompt_text = (
        "Generate an image following this exact JSON specification:\n\n"
        + json.dumps(json_prompt, indent=2)
    )

    print(f"Generating thumbnail for: {topic}")
    print(f"   Style: {style} | Headline: {headline}")

    try:
        contents = []
        if ref_image_data:
            contents.append(
                types.Part.from_bytes(data=ref_image_data, mime_type="image/jpeg")
            )
            contents.append(
                "Using this exact ninja character design (same face, outfit, colors), "
                + prompt_text
            )
        else:
            contents.append(prompt_text)

        response = client.models.generate_content(
            model="gemini-3.1-flash-image-preview",
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["image", "text"],
                image_config=types.ImageConfig(aspectRatio="9:16"),
            ),
        )

        # Extract image from response
        for part in response.candidates[0].content.parts:
            if hasattr(part, "inline_data") and part.inline_data:
                OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

                if not output_path:
                    safe_topic = "".join(
                        c if c.isalnum() else "_" for c in topic[:30]
                    )
                    output_path = str(
                        OUTPUT_DIR / f"thumb_{safe_topic}_{style}.png"
                    )

                with open(output_path, "wb") as f:
                    f.write(part.inline_data.data)

                size = os.path.getsize(output_path)
                print(f"   Thumbnail saved: {output_path} ({size / 1024:.0f}KB)")

                # Optionally save the JSON prompt alongside for reproducibility
                if save_prompt:
                    prompt_path = output_path.replace(".png", "_prompt.json")
                    with open(prompt_path, "w") as f:
                        json.dump(json_prompt, f, indent=2)
                    print(f"   Prompt saved: {prompt_path}")

                return output_path

        print("   No image in response")
        return None

    except Exception as e:
        print(f"   Error: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Generate ninja thumbnails (JSON prompting)")
    parser.add_argument("--topic", required=True, help="Topic/headline for thumbnail")
    parser.add_argument("--style", default="engaging",
                        choices=["engaging", "shocked", "thinking", "pointing", "excited"],
                        help="Ninja pose/expression style")
    parser.add_argument("--output", help="Output path for thumbnail")
    parser.add_argument("--reference", help="Custom reference image for the ninja character")
    parser.add_argument("--save-prompt", action="store_true",
                        help="Save JSON prompt alongside thumbnail for reproducibility")
    parser.add_argument("--show-prompt", action="store_true",
                        help="Print the JSON prompt to stdout without generating")
    parser.add_argument("--both", action="store_true",
                        help="Generate both Pixar avatar AND news anchor thumbnails")

    args = parser.parse_args()

    if args.show_prompt:
        topic_icons = _detect_topic_icons(args.topic)
        headline = _extract_headline(args.topic)
        prompt = _build_json_prompt(args.topic, args.style, headline, topic_icons)
        print(json.dumps(prompt, indent=2))
        return

    if args.both:
        base_output = args.output or f"output/thumbnails/thumb_{args.topic[:20]}_{args.style}"
        pixar_out = base_output.replace('.png', '_pixar.png') if '.png' in str(base_output) else f"{base_output}_pixar.png"
        anchor_out = base_output.replace('.png', '_anchor.png') if '.png' in str(base_output) else f"{base_output}_anchor.png"

        print("Generating BOTH thumbnail variants...")
        generate_thumbnail(args.topic, args.style, pixar_out, None, args.save_prompt)
        generate_thumbnail(args.topic, args.style, anchor_out,
                          str(Path(__file__).parent.parent / "assets/reference/ninja_news_anchor.jpg"),
                          args.save_prompt)
    else:
        generate_thumbnail(args.topic, args.style, args.output, args.reference, args.save_prompt)


if __name__ == "__main__":
    main()
