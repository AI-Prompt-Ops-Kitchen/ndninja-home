#!/usr/bin/env python3
"""
generate_videochat_refs.py — Generate webcam-style reference images for video chat format

Uses Nano Banana Pro (Gemini 3 Pro Image) to create reference images of Ninja and Glitch
that look like real video call webcam shots in their respective rooms. These images are
then fed to Kling Avatar v2 for animation.

Usage:
    python3 generate_videochat_refs.py
    python3 generate_videochat_refs.py --character ninja
    python3 generate_videochat_refs.py --character glitch
"""

import argparse
import os
import sys
from pathlib import Path

OUTPUT_DIR = Path.home() / "assets" / "overlays"
REF_DIR = Path.home() / "assets" / "reference"


def generate_webcam_ref(character: str, reference_image: str = None):
    """Generate a webcam-style reference image for a character."""
    from google import genai
    from google.genai import types

    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: Set GOOGLE_API_KEY or GEMINI_API_KEY")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    # Load reference image for character consistency
    contents = []
    if reference_image and Path(reference_image).exists():
        with open(reference_image, "rb") as f:
            ref_data = f.read()
        contents.append(types.Part.from_bytes(data=ref_data, mime_type="image/jpeg"))
        print(f"  Using reference: {reference_image}")

    # Character-specific prompts
    prompts = {
        "ninja": {
            "ref_image": str(Path.home() / "uploads" / "IMG_2411.jpeg"),
            "prompt": """Using this exact character design, create a webcam-style image:

SUBJECT: This same 3D Pixar ninja character — rounded helmet with big expressive round goggles showing
digital eyes, visible nose and mouth (friendly smile), black tactical outfit with cyan LED accent lines.
Cute expressive Pixar face. Sitting at a desk, facing the camera directly like a webcam/video call view.
Shoulders and upper chest visible. Slightly looking at camera with engaged, friendly expression.

SETTING: Dark gaming room background. Subtle blue/cyan LED strip lighting behind the character on
the wall. Out-of-focus gaming monitors with dim screen glow to the sides. Dark desk surface visible
at bottom edge. Moody, cool-toned lighting (5500K). Slight bokeh on background elements.

FRAMING: Webcam/video call composition — character centered, head and shoulders, looking directly
at camera. Like a FaceTime or Zoom call screenshot. Natural webcam angle (slightly above eye level).
Close enough that the character's face fills about 40% of the frame vertically.

STYLE: 3D Pixar/Disney animation. Soft appealing features. The digital goggle eyes should look
engaged and lively. Clean render, no text, no watermarks. Square-ish composition (close to 1:1).
Warm ambient light from the monitor screens contrasting with cool LED accents.""",
        },
        "glitch": {
            "ref_image": str(Path.home() / "assets" / "overlays" / "Glitch_Facetime_Design.png"),
            "prompt": """Using this exact character design, create a webcam-style image:

SUBJECT: This same 3D Pixar cyberpunk girl character — pink/magenta hair, pink-tinted goggles/visor,
futuristic armor with neon pink accents. Sitting at a desk, facing the camera directly like a
webcam/video call view. Shoulders and upper chest visible. Playful, cheerful expression.
Slight head tilt showing personality.

SETTING: Bright-ish hacker den / tech workspace background. Magenta/pink neon accent lighting
on the walls. Visible tech gadgets, circuit boards, or holographic displays out of focus behind her.
Warmer color temperature (4800K) with pink accent tones. Slight bokeh on background.

FRAMING: Webcam/video call composition — character centered, head and shoulders, looking directly
at camera. Like a FaceTime or Zoom call screenshot. Natural webcam angle (slightly above eye level).
Close enough that the character's face fills about 40% of the frame vertically.

STYLE: 3D Pixar/Disney animation. Cute but cool, fun personality showing through. The pink goggles
should look expressive. Clean render, no text, no watermarks. Square-ish composition (close to 1:1).
Neon pink reflections on skin/armor for that cyberpunk feel.""",
        },
    }

    char_config = prompts[character]

    # Use provided reference or default
    if not reference_image:
        reference_image = char_config["ref_image"]
        if Path(reference_image).exists():
            with open(reference_image, "rb") as f:
                ref_data = f.read()
            contents = [types.Part.from_bytes(data=ref_data, mime_type="image/jpeg")]
            print(f"  Using reference: {reference_image}")

    contents.append(char_config["prompt"])

    print(f"  Generating {character} webcam reference...")

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-image-preview",  # Nano Banana Pro 2
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["image", "text"],
                image_config=types.ImageConfig(
                    aspectRatio="1:1",
                ),
            ),
        )

        # Extract image
        for part in response.candidates[0].content.parts:
            if hasattr(part, "inline_data") and part.inline_data:
                OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
                out_path = OUTPUT_DIR / f"videochat_ref_{character}.png"
                with open(out_path, "wb") as f:
                    f.write(part.inline_data.data)
                size = os.path.getsize(out_path)
                print(f"  Saved: {out_path} ({size / 1024:.0f}KB)")
                return str(out_path)

        print("  No image in response")
        return None

    except Exception as e:
        print(f"  Error: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Generate video chat reference images")
    parser.add_argument("--character", choices=["ninja", "glitch"],
                        help="Generate for specific character (default: both)")
    args = parser.parse_args()

    characters = [args.character] if args.character else ["ninja", "glitch"]

    for char in characters:
        print(f"\n{'='*50}")
        print(f"Generating {char.upper()} webcam reference")
        print(f"{'='*50}")
        result = generate_webcam_ref(char)
        if result:
            print(f"  Ready for Kling Avatar: {result}")


if __name__ == "__main__":
    main()
