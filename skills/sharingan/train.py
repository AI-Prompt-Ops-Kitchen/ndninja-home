#!/usr/bin/env python3
"""Sharingan — Training Dojo (Podcast Generator).

Usage:
    python3 train.py <scroll-name> [options]

Generates a Sensei/Student conversation podcast from a Sharingan scroll
using Podcastfy. Perfect for passive learning — listen while walking,
driving, or cooking.

Examples:
    python3 train.py spline-3d-web                      # Full podcast (edge TTS)
    python3 train.py spline-3d-web --transcript-only     # Preview conversation text
    python3 train.py spline-3d-web --tts elevenlabs      # Premium voices
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

SCROLL_DIR = Path.home() / ".sharingan" / "scrolls"
TRAINING_DIR = Path.home() / ".sharingan" / "training"

# Mastery level → teaching depth guidance
LEVEL_GUIDANCE = {
    "1-tomoe": "introductory level — cover the basics, define terms, keep it accessible. Assume the student is brand new.",
    "2-tomoe": "intermediate level — the student knows the basics. Focus on practical workflows, gotchas, and when to use what.",
    "3-tomoe": "advanced deep-dive — get into edge cases, architecture decisions, performance implications, and expert tips.",
    "mangekyo": "cross-domain mastery — connect this topic to related domains. Explore how concepts transfer and combine.",
}


def list_scrolls():
    """Print available scrolls and exit."""
    scrolls = sorted(SCROLL_DIR.glob("*.md"))
    if not scrolls:
        print("No scrolls found. Use /sharingan to learn a topic first.")
        return
    print("Available scrolls:")
    for s in scrolls:
        print(f"  - {s.stem}")


def parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from scroll markdown."""
    match = re.match(r"^---\n(.+?)\n---", content, re.DOTALL)
    if not match:
        return {}
    fm = {}
    for line in match.group(1).split("\n"):
        line = line.strip()
        if ":" in line and not line.startswith("-"):
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip().strip('"').strip("'")
    return fm


def build_prompt(scroll_content: str, frontmatter: dict) -> str:
    """Build the instructional wrapper for the LLM conversation generator."""
    level = frontmatter.get("level", "1-tomoe")
    domain = frontmatter.get("domain", "Technology")
    name = frontmatter.get("name", "unknown")
    depth = LEVEL_GUIDANCE.get(level, LEVEL_GUIDANCE["1-tomoe"])

    return f"""You are generating a training conversation between two characters:

**Sensei** — An experienced developer/teacher who deeply understands {name} ({domain}).
Speaks clearly and directly. Uses analogies and real-world examples. Never condescending.

**Student** — A curious developer who is eager to learn. Asks sharp questions, wants
to understand the "why" not just the "how". Sometimes challenges assumptions.

Teaching calibration: {depth}

IMPORTANT GUIDELINES:
- Spend 30-40% of the conversation on limitations, gaps, gotchas, and "what could go wrong"
- Include at least 2 "what would you do if..." practical scenarios
- If the source material flags something as uncertain or single-source, the Sensei should
  say "I've only seen this from one source, so take it with a grain of salt"
- End with 2-3 concrete next steps the student should take
- Keep it conversational and engaging — this is audio, not a textbook

SOURCE MATERIAL (from Sharingan scroll "{name}"):

{scroll_content}"""


def generate(scroll_name: str, tts: str, transcript_only: bool, llm_model: str):
    """Generate podcast from a scroll."""
    scroll_path = SCROLL_DIR / f"{scroll_name}.md"
    if not scroll_path.exists():
        print(f"Scroll '{scroll_name}' not found.")
        list_scrolls()
        sys.exit(1)

    scroll_content = scroll_path.read_text()
    frontmatter = parse_frontmatter(scroll_content)
    level = frontmatter.get("level", "1-tomoe")
    domain = frontmatter.get("domain", "Unknown")

    print(f"Scroll: {scroll_name}")
    print(f"Level:  {level}")
    print(f"Domain: {domain}")
    print(f"TTS:    {tts}")
    print(f"LLM:    {llm_model}")
    print()

    # Build instructional prompt
    prompt_text = build_prompt(scroll_content, frontmatter)

    # Prepare output directory
    out_dir = TRAINING_DIR / scroll_name
    out_dir.mkdir(parents=True, exist_ok=True)

    # Conversation config — Sensei/Student theme
    conversation_config = {
        "conversation_style": ["educational", "engaging", "practical"],
        "roles_person1": "Sensei (experienced teacher)",
        "roles_person2": "Student (curious developer)",
        "dialogue_structure": [
            "Introduction and context",
            "Core concepts and mental model",
            "Practical workflows",
            "Gotchas and limitations",
            "Practical scenarios",
            "Next steps and summary",
        ],
        "podcast_name": "Sharingan Training Dojo",
        "podcast_tagline": "Learn by listening",
        "output_language": "English",
        "engagement_techniques": [
            "analogies",
            "practical scenarios",
            "real-world examples",
            "what-if questions",
        ],
        "creativity": 0.7,
        "text_to_speech": {
            "default_tts_model": tts,
            "output_directories": {
                "transcripts": str(out_dir),
                "audio": str(out_dir),
            },
            "edge": {
                "default_voices": {
                    "question": "en-US-EricNeural",
                    "answer": "en-US-JennyNeural",
                },
            },
            "elevenlabs": {
                "default_voices": {
                    "question": "Chris",
                    "answer": "Jessica",
                },
                "model": "eleven_multilingual_v2",
            },
            "audio_format": "mp3",
            "temp_audio_dir": str(out_dir / "tmp"),
            "ending_message": "Train hard, ninja.",
        },
    }

    # Import podcastfy (delayed to keep --help fast)
    print("Generating conversation..." if transcript_only else "Generating podcast...")

    try:
        from podcastfy.client import generate_podcast

        result = generate_podcast(
            text=prompt_text,
            tts_model=tts,
            transcript_only=transcript_only,
            conversation_config=conversation_config,
            llm_model_name=llm_model,
            api_key_label="ANTHROPIC_API_KEY",
        )
    except Exception as e:
        err = str(e).lower()
        if "authentication" in err or "api_key" in err or "401" in err:
            print(f"\nAuth error: Your LLM API key is invalid or missing.", file=sys.stderr)
            print(f"Set ANTHROPIC_API_KEY (or use --llm to pick a different provider).", file=sys.stderr)
            print(f"  e.g.: export ANTHROPIC_API_KEY='sk-ant-...'", file=sys.stderr)
            print(f"  e.g.: --llm openai/gpt-4o (needs OPENAI_API_KEY)", file=sys.stderr)
            sys.exit(1)
        raise

    # Save metadata
    metadata = {
        "scroll": scroll_name,
        "level": level,
        "domain": domain,
        "tts_model": tts,
        "llm_model": llm_model,
        "transcript_only": transcript_only,
        "generated_at": datetime.now().isoformat(),
        "output": result,
    }
    meta_path = out_dir / "metadata.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    # Copy/rename output if it's an audio file outside our dir
    if result and not transcript_only and Path(result).exists():
        final_path = out_dir / "podcast.mp3"
        if Path(result) != final_path:
            import shutil
            shutil.copy2(result, final_path)
            result = str(final_path)
        print(f"\nPodcast: {result}")
    elif transcript_only:
        # Find transcript file in output dir
        transcripts = list(out_dir.glob("*.txt"))
        if transcripts:
            final_transcript = out_dir / "transcript.txt"
            if transcripts[0] != final_transcript:
                transcripts[0].rename(final_transcript)
            print(f"\nTranscript: {final_transcript}")
        elif result:
            # Result might be the transcript text itself
            transcript_path = out_dir / "transcript.txt"
            transcript_path.write_text(result)
            print(f"\nTranscript: {transcript_path}")

    print(f"Metadata: {meta_path}")
    print("\nTraining complete.")


def main():
    parser = argparse.ArgumentParser(
        description="Sharingan Training Dojo — Generate podcasts from scrolls",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  python3 train.py spline-3d-web\n"
               "  python3 train.py spline-3d-web --transcript-only\n"
               "  python3 train.py spline-3d-web --tts elevenlabs\n",
    )
    parser.add_argument(
        "scroll",
        nargs="?",
        help="Name of the scroll to train from (e.g., spline-3d-web)",
    )
    parser.add_argument(
        "--tts",
        default="edge",
        choices=["edge", "elevenlabs", "openai", "gemini"],
        help="TTS engine (default: edge — free, no API key needed)",
    )
    parser.add_argument(
        "--transcript-only",
        action="store_true",
        help="Generate conversation text only, skip audio",
    )
    parser.add_argument(
        "--llm",
        default="anthropic/claude-sonnet-4-6",
        help="LLM model for conversation generation (default: anthropic/claude-sonnet-4-6)",
    )

    args = parser.parse_args()

    if not args.scroll:
        parser.print_help()
        print()
        list_scrolls()
        sys.exit(0)

    generate(args.scroll, args.tts, args.transcript_only, args.llm)


if __name__ == "__main__":
    main()
