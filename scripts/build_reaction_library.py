#!/usr/bin/env python3
"""Build a library of reusable avatar reaction clips for meme Shorts.

Generates short TTS audio for each reaction type, then sends to
fal.ai Kling Avatar v2 (Standard) to produce lip-synced reaction clips.

Usage:
    python3 build_reaction_library.py [--character ninja|glitch|both] [--dry-run]
"""

import os
import sys
import time
import json
import argparse
import subprocess
from pathlib import Path

OUTPUT_DIR = Path("/home/ndninja/assets/reactions")

# Character reference images
CHARACTERS = {
    "ninja": {
        "image": "/home/ndninja/uploads/IMG_2411.jpeg",  # New desk presenter design
        "voice": "Eric",  # Ninja's TTS voice
        "prompt_base": "Static camera, stable framing. Animated ninja character at desk. Expressive eyes that blink and emote, natural head movements.",
    },
    "glitch": {
        "image": "/home/ndninja/uploads/Glitch_Neutral_Background.png",
        "voice": "Laura",  # Glitch's locked voice
        "prompt_base": "Static camera, stable framing. Animated female hacker character at desk with pink lighting. Expressive eyes that blink and emote, natural head movements.",
    },
}

# Reaction definitions: short exclamations that drive expression
REACTIONS = {
    "shocked": {
        "ninja_text": "Oh my GOD! No way! No WAY!",
        "glitch_text": "Wait WHAT?! Are you serious right now?!",
        "prompt_suffix": "Shocked expression, wide eyes, mouth open in disbelief, eyebrows raised high.",
        "negative": "calm, neutral, smiling",
    },
    "hype": {
        "ninja_text": "LET'S GOOO! This is INSANE! Let's GO!",
        "glitch_text": "OH YEAH! This is SO good! I'm HYPED!",
        "prompt_suffix": "Extremely excited, pumped up, big smile, energetic head movements, celebrating.",
        "negative": "calm, sad, neutral expression",
    },
    "crying_laughing": {
        "ninja_text": "Hahahaha! I can't! I literally cannot! Hahaha!",
        "glitch_text": "I'm DEAD! Hahaha! I can't breathe! Hahaha!",
        "prompt_suffix": "Laughing uncontrollably, squinting eyes from laughter, shaking with laughter.",
        "negative": "serious, angry, sad",
    },
    "angry": {
        "ninja_text": "Are you KIDDING me?! This is ridiculous! Absolutely ridiculous!",
        "glitch_text": "Oh HELL no! I am NOT okay with this! Ugh!",
        "prompt_suffix": "Angry expression, furrowed brows, intense stare, frustrated head shaking.",
        "negative": "happy, smiling, calm",
    },
    "smug": {
        "ninja_text": "Called it. I literally called it. You're welcome.",
        "glitch_text": "Mmhmm. Just as I predicted. Told you so.",
        "prompt_suffix": "Smug confident expression, slight smirk, one eyebrow raised, knowing look.",
        "negative": "surprised, shocked, angry",
    },
    "mind_blown": {
        "ninja_text": "Broooo... this changes EVERYTHING. Everything!",
        "glitch_text": "Hold on... hold ON. Do you realize what this means?!",
        "prompt_suffix": "Mind blown expression, slowly widening eyes, head pulling back in realization.",
        "negative": "bored, neutral, calm",
    },
    "sad": {
        "ninja_text": "Man... that actually hurts. That really hurts.",
        "glitch_text": "I'm not gonna cry... I'm NOT gonna cry...",
        "prompt_suffix": "Sad expression, slightly drooping eyes, small frown, looking down momentarily.",
        "negative": "happy, excited, laughing",
    },
    "confused": {
        "ninja_text": "Wait... what? I don't... what? Huh?",
        "glitch_text": "Um... excuse me? Can someone explain? What is happening?",
        "prompt_suffix": "Confused expression, tilted head, squinting eyes, furrowed brow, looking around.",
        "negative": "confident, certain, smiling",
    },
    "excited_reveal": {
        "ninja_text": "Oh oh oh! HERE it comes! HERE IT COMES! YES!",
        "glitch_text": "It's happening! IT'S HAPPENING! Oh my god YES!",
        "prompt_suffix": "Building excitement, leaning forward, eyes getting wider, huge grin forming.",
        "negative": "bored, looking away, calm",
    },
    "cringe": {
        "ninja_text": "Ohhh... oh no... no no no no...",
        "glitch_text": "Yikes... oh yikes... I can't watch this...",
        "prompt_suffix": "Cringing, eyes squinting, teeth clenched, head turning slightly away.",
        "negative": "happy, confident, relaxed",
    },
    "wholesome": {
        "ninja_text": "Aww... that's actually really sweet. That's beautiful.",
        "glitch_text": "Okay that's adorable. My heart... my heart can't take it.",
        "prompt_suffix": "Warm genuine smile, soft eyes, slight head tilt, touched expression.",
        "negative": "angry, shocked, scared",
    },
    "spit_take": {
        "ninja_text": "PFFT! Haha! Wait WHAT?! Hahaha!",
        "glitch_text": "I just— PFFT! Haha! I was NOT ready for that!",
        "prompt_suffix": "Sudden burst of surprised laughter, head jerking back, eyes wide then squinting from laughing.",
        "negative": "calm, serious, neutral",
    },
}


def generate_tts(text: str, voice: str, output_path: str) -> bool:
    """Generate short TTS audio using edge-tts (free, fast)."""
    try:
        cmd = [
            "edge-tts",
            "--voice", f"en-US-{voice}Online" if voice == "Eric" else f"en-GB-{voice}Neural",
            "--text", text,
            "--write-media", output_path,
            "--rate", "+15%",  # Slightly faster for energy
        ]
        # Use ElevenLabs voices mapping for edge-tts compatible voices
        voice_map = {
            "Eric": "en-US-GuyNeural",
            "Laura": "en-GB-SoniaNeural",  # Closest to Laura's sassy energy
        }
        cmd = [
            "edge-tts",
            "--voice", voice_map.get(voice, "en-US-GuyNeural"),
            "--text", text,
            "--write-media", output_path,
            "--rate", "+15%",
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except Exception as e:
        print(f"   edge-tts failed: {e}, trying ElevenLabs...")
        return generate_tts_elevenlabs(text, voice, output_path)


def generate_tts_elevenlabs(text: str, voice: str, output_path: str) -> bool:
    """Fallback: Generate TTS via ElevenLabs API."""
    try:
        # Use the existing ninja pipeline's TTS
        sys.path.insert(0, "/home/ndninja/scripts")
        from ninja_content import generate_tts as ninja_tts
        return ninja_tts(text, output_path, voice_style="expressive") is not None
    except Exception as e:
        print(f"   ElevenLabs TTS also failed: {e}")
        return False


def generate_kling_clip(image_path: str, audio_path: str, output_path: str,
                        prompt: str, negative_prompt: str) -> bool:
    """Generate a reaction clip via fal.ai Kling Avatar v2 Standard."""
    try:
        import fal_client

        # Ensure FAL_KEY is set
        fal_key = os.environ.get("FAL_KEY") or os.environ.get("FAL_AI_API_KEY")
        if not fal_key:
            print("   No fal.ai API key found")
            return False
        os.environ["FAL_KEY"] = fal_key

        # Upload assets
        with open(image_path, "rb") as f:
            image_url = fal_client.upload(f.read(), "image/jpeg")
        with open(audio_path, "rb") as f:
            audio_url = fal_client.upload(f.read(), "audio/mpeg")

        print(f"   Generating clip (Standard, ~2-4 min)...")
        start = time.time()

        # Submit async then poll with timeout (avoid indefinite hang)
        handle = fal_client.submit(
            "fal-ai/kling-video/ai-avatar/v2/standard",
            arguments={
                "image_url": image_url,
                "audio_url": audio_url,
                "prompt": prompt,
                "negative_prompt": negative_prompt,
            },
        )

        # Poll status with 5 min timeout
        deadline = time.time() + 300
        result = None
        while time.time() < deadline:
            st = handle.status(with_logs=True)
            st_name = type(st).__name__
            if hasattr(st, "logs") and st.logs:
                for log in st.logs:
                    msg = log.get("message", str(log)) if isinstance(log, dict) else str(log)
                    print(f"   [fal] {msg}")
            if isinstance(st, fal_client.Completed):
                result = handle.get()
                break
            time.sleep(10)

        if result is None:
            print(f"   TIMEOUT after 5 min — cancelling")
            try:
                handle.cancel()
            except Exception:
                pass
            return False

        elapsed = time.time() - start
        video_url = result.get("video", {}).get("url")
        if not video_url:
            print(f"   No video URL in response")
            return False

        # Download
        import requests
        r = requests.get(video_url)
        with open(output_path, "wb") as f:
            f.write(r.content)

        duration = result.get("duration", "?")
        print(f"   Done in {elapsed:.0f}s (clip: {duration}s)")
        return True

    except Exception as e:
        print(f"   Kling generation failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Build reaction clip library")
    parser.add_argument("--character", choices=["ninja", "glitch", "both"], default="both")
    parser.add_argument("--reactions", nargs="+", help="Specific reactions to generate (default: all)")
    parser.add_argument("--dry-run", action="store_true", help="Only generate TTS, skip Kling")
    parser.add_argument("--tts-only", action="store_true", help="Only generate TTS audio")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    characters = ["ninja", "glitch"] if args.character == "both" else [args.character]
    reactions = args.reactions or list(REACTIONS.keys())

    total = len(characters) * len(reactions)
    print(f"=== Reaction Clip Library Builder ===")
    print(f"Characters: {', '.join(characters)}")
    print(f"Reactions: {len(reactions)}")
    print(f"Total clips to generate: {total}")
    print(f"Estimated cost: ~${total * 0.40:.2f} (Kling Standard)")
    print(f"Output: {OUTPUT_DIR}")
    print()

    results = {"success": [], "failed": [], "skipped": []}

    for char_name in characters:
        char = CHARACTERS[char_name]
        print(f"\n{'='*50}")
        print(f"Character: {char_name.upper()}")
        print(f"{'='*50}")

        for reaction_name in reactions:
            reaction = REACTIONS[reaction_name]
            clip_id = f"{char_name}_{reaction_name}"
            audio_path = OUTPUT_DIR / f"{clip_id}_audio.mp3"
            video_path = OUTPUT_DIR / f"{clip_id}.mp4"

            # Skip if already generated
            if video_path.exists() and not args.tts_only:
                print(f"\n[SKIP] {clip_id} — already exists")
                results["skipped"].append(clip_id)
                continue

            print(f"\n[{clip_id}]")

            # Step 1: Generate TTS
            text_key = f"{char_name}_text"
            text = reaction.get(text_key, reaction.get("ninja_text"))
            print(f"   TTS: \"{text[:60]}...\"")

            if not audio_path.exists():
                if not generate_tts(text, char["voice"], str(audio_path)):
                    print(f"   FAILED: TTS generation")
                    results["failed"].append(clip_id)
                    continue
                print(f"   Audio: {audio_path}")
            else:
                print(f"   Audio: {audio_path} (cached)")

            if args.dry_run or args.tts_only:
                print(f"   [DRY RUN] Would generate Kling clip")
                results["skipped"].append(clip_id)
                continue

            # Step 2: Generate Kling clip
            prompt = f"{char['prompt_base']} {reaction['prompt_suffix']}"
            negative = reaction.get("negative", "")

            if generate_kling_clip(
                char["image"], str(audio_path), str(video_path),
                prompt=prompt, negative_prompt=negative
            ):
                results["success"].append(clip_id)
            else:
                results["failed"].append(clip_id)

    # Summary
    print(f"\n{'='*50}")
    print(f"SUMMARY")
    print(f"{'='*50}")
    print(f"Success: {len(results['success'])}")
    print(f"Failed:  {len(results['failed'])}")
    print(f"Skipped: {len(results['skipped'])}")

    if results["success"]:
        print(f"\nGenerated clips:")
        for clip in results["success"]:
            path = OUTPUT_DIR / f"{clip}.mp4"
            size = path.stat().st_size / 1024 if path.exists() else 0
            print(f"  {clip}.mp4 ({size:.0f}KB)")

    if results["failed"]:
        print(f"\nFailed clips (retry with --reactions {' '.join(r.split('_',1)[1] for r in results['failed'])}):")
        for clip in results["failed"]:
            print(f"  {clip}")

    # Save manifest
    manifest = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "clips": {},
    }
    for clip_id in results["success"] + results["skipped"]:
        video_path = OUTPUT_DIR / f"{clip_id}.mp4"
        if video_path.exists():
            char_name, reaction_name = clip_id.split("_", 1)
            manifest["clips"][clip_id] = {
                "character": char_name,
                "reaction": reaction_name,
                "path": str(video_path),
                "prompt_suffix": REACTIONS.get(reaction_name, {}).get("prompt_suffix", ""),
            }

    manifest_path = OUTPUT_DIR / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nManifest: {manifest_path}")


if __name__ == "__main__":
    main()
