#!/usr/bin/env python3
"""Sharingan — YouTube transcript extractor.

Usage:
    python3 extract_transcript.py <youtube_url> [output_dir]

Extracts subtitles, cleans them, and saves metadata + clean transcript.
"""

import re
import sys
import json
import subprocess
from pathlib import Path

def extract(url: str, output_dir: str = "/tmp/sharingan") -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Get metadata
    meta_cmd = [
        "yt-dlp", "--print", "%(title)s\n%(description)s\n%(duration_string)s\n%(upload_date)s\n%(channel)s",
        url
    ]
    meta_result = subprocess.run(meta_cmd, capture_output=True, text=True)
    meta_lines = meta_result.stdout.strip().split("\n")

    title = meta_lines[0] if len(meta_lines) > 0 else "Unknown"
    # Description can be multi-line, duration/date/channel are at the end
    duration = meta_lines[-3] if len(meta_lines) >= 3 else "Unknown"
    upload_date = meta_lines[-2] if len(meta_lines) >= 2 else "Unknown"
    channel = meta_lines[-1] if len(meta_lines) >= 1 else "Unknown"

    safe_title = re.sub(r'[^\w\s-]', '', title)[:60].strip()

    # Download subtitles
    sub_cmd = [
        "yt-dlp", "--write-auto-sub", "--sub-lang", "en",
        "--skip-download", "--sub-format", "vtt",
        "-o", str(out / safe_title),
        url
    ]
    subprocess.run(sub_cmd, capture_output=True, text=True)

    # Find the VTT file — prefer the one matching this video's title
    vtt_files = list(out.glob("*.vtt"))
    if not vtt_files:
        print("ERROR: No subtitle file found", file=sys.stderr)
        return {"error": "No subtitles available"}

    # Match by safe_title prefix to avoid grabbing leftover VTTs from previous runs
    matching = [f for f in vtt_files if f.name.startswith(safe_title)]
    vtt_path = matching[0] if matching else vtt_files[-1]
    if not matching:
        print(f"WARNING: No VTT matched title '{safe_title}', using {vtt_path.name}", file=sys.stderr)

    # Clean VTT to plain text
    with open(vtt_path, "r") as f:
        content = f.read()

    lines = content.split("\n")
    seen = set()
    clean = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:"):
            continue
        if re.match(r"^\d{2}:\d{2}", line) or re.match(r"^\d+$", line):
            continue
        line = re.sub(r"<[^>]+>", "", line)
        if line and line not in seen:
            seen.add(line)
            clean.append(line)

    transcript = " ".join(clean)

    # Save clean transcript
    transcript_path = out / "transcript_clean.txt"
    with open(transcript_path, "w") as f:
        f.write(transcript)

    # Save metadata
    metadata = {
        "title": title,
        "url": url,
        "channel": channel,
        "duration": duration,
        "upload_date": upload_date,
        "word_count": len(transcript.split()),
        "transcript_path": str(transcript_path),
    }

    meta_path = out / "metadata.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Title: {title}")
    print(f"Channel: {channel}")
    print(f"Duration: {duration}")
    print(f"Words: {metadata['word_count']}")
    print(f"Transcript: {transcript_path}")
    print(f"Metadata: {meta_path}")

    return metadata


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <youtube_url> [output_dir]")
        sys.exit(1)

    url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "/tmp/sharingan"
    extract(url, output_dir)
