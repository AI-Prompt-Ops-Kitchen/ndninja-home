#!/usr/bin/env python3
"""
ninja_captions.py — Create Instagram Reels-style animated captions

Generates ASS (Advanced SubStation Alpha) subtitles with:
- Word-by-word highlighting
- Pop-in animation effects  
- Emphasis styling for key words
- Modern social media aesthetic
"""

import argparse
import re
import os
import subprocess
from pathlib import Path


def get_audio_duration(audio_path):
    """Get duration of audio file."""
    result = subprocess.run([
        "ffprobe", "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "csv=p=0", audio_path
    ], capture_output=True, text=True)
    return float(result.stdout.strip())


def create_ass_header(width=1080, height=1920):
    """Create ASS file header with styles."""
    return f"""[Script Info]
Title: Ninja Captions
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: {width}
PlayResY: {height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,72,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,4,2,2,40,40,60,1
Style: Highlight,Arial Black,80,&H0000FFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,105,105,0,0,1,4,2,2,40,40,60,1
Style: Emphasis,Arial Black,85,&H0000D4FF,&H000000FF,&H00000000,&H80000000,1,0,0,0,110,110,0,0,1,5,3,2,40,40,60,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def format_ass_time(seconds):
    """Format seconds as ASS timestamp (H:MM:SS.cc)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int((seconds % 1) * 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"


def split_into_chunks(text, words_per_chunk=4):
    """Split text into display chunks."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), words_per_chunk):
        chunk = " ".join(words[i:i+words_per_chunk])
        chunks.append(chunk)
    return chunks


def identify_emphasis_words(text):
    """Identify words that should be emphasized."""
    # Words that often deserve emphasis in tech news
    emphasis_patterns = [
        r'\b(breaking|huge|insane|crazy|wild|massive|major)\b',
        r'\b(AI|GPT|Meta|Google|Apple|OpenAI|Microsoft)\b',
        r'\b(million|billion|trillion)\b',
        r'\b(free|paid|cost|price|charge)\b',
        r'\b(banned|blocked|censored|removed)\b',
        r'\b(first|new|latest|just)\b',
        r'\b(warning|alert|urgent)\b',
    ]
    
    emphasis_words = set()
    for pattern in emphasis_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        emphasis_words.update(w.lower() for w in matches)
    
    return emphasis_words


def create_animated_line(text, start_time, end_time, emphasis_words):
    """Create an ASS dialogue line with word-by-word animation."""
    words = text.split()
    duration = end_time - start_time
    word_duration = duration / len(words) if words else duration
    
    # Build the animated text
    animated_parts = []
    
    for i, word in enumerate(words):
        word_start = i * word_duration
        word_end = (i + 1) * word_duration
        
        # Check if this word should be emphasized
        is_emphasis = word.lower().strip('.,!?') in emphasis_words
        
        if is_emphasis:
            # Emphasis word: yellow/orange, slightly larger, with pop effect
            animated_parts.append(
                f"{{\\t({int(word_start*1000)},{int(word_start*1000)+100},\\fscx110\\fscy110\\c&H00D4FF&)}}"
                f"{{\\t({int(word_end*1000)-100},{int(word_end*1000)},\\fscx100\\fscy100\\c&HFFFFFF&)}}"
                f"{word} "
            )
        else:
            # Normal word: subtle highlight then fade
            animated_parts.append(
                f"{{\\t({int(word_start*1000)},{int(word_start*1000)+80},\\c&H00FFFF&)}}"
                f"{{\\t({int(word_start*1000)+80},{int(word_end*1000)},\\c&HFFFFFF&)}}"
                f"{word} "
            )
    
    return "".join(animated_parts).strip()


def create_pop_in_effect(text, delay_ms=0):
    """Add pop-in animation effect to text."""
    # Scale from 0 to 100% with overshoot
    return (
        f"{{\\fscx0\\fscy0\\t({delay_ms},{delay_ms+150},\\fscx110\\fscy110)}}"
        f"{{\\t({delay_ms+150},{delay_ms+200},\\fscx100\\fscy100)}}"
        f"{text}"
    )


def generate_ass_captions(script_text, duration, output_path, style="animated"):
    """Generate ASS caption file from script text."""
    
    # Split into chunks
    chunks = split_into_chunks(script_text, words_per_chunk=5)
    
    # Calculate timing
    time_per_chunk = duration / len(chunks)
    
    # Identify emphasis words
    emphasis_words = identify_emphasis_words(script_text)
    
    # Build ASS content
    ass_content = create_ass_header()
    
    for i, chunk in enumerate(chunks):
        start_time = i * time_per_chunk
        end_time = (i + 1) * time_per_chunk
        
        start_str = format_ass_time(start_time)
        end_str = format_ass_time(end_time)
        
        if style == "animated":
            # Word-by-word highlight animation
            text = create_animated_line(chunk, start_time, end_time, emphasis_words)
            text = create_pop_in_effect(text, delay_ms=0)
        elif style == "pop":
            # Simple pop-in
            text = create_pop_in_effect(chunk)
        else:
            # Plain
            text = chunk
        
        ass_content += f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text}\n"
    
    # Write file
    with open(output_path, 'w') as f:
        f.write(ass_content)
    
    return output_path


def burn_ass_captions(video_path, ass_path, output_path):
    """Burn ASS captions into video."""
    # Need to escape the path for ffmpeg filter
    ass_escaped = str(ass_path).replace('\\', '/').replace(':', '\\:')
    
    subprocess.run([
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"ass={ass_escaped}",
        "-c:a", "copy",
        output_path
    ], capture_output=True)
    
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generate Instagram-style animated captions")
    parser.add_argument("--script", "-s", required=True, help="Script text or file")
    parser.add_argument("--audio", "-a", help="Audio file (for timing)")
    parser.add_argument("--duration", "-d", type=float, help="Duration in seconds")
    parser.add_argument("--video", "-v", help="Video to burn captions into")
    parser.add_argument("--output", "-o", required=True, help="Output file")
    parser.add_argument("--style", choices=["animated", "pop", "plain"], default="animated")
    
    args = parser.parse_args()
    
    # Get script text
    if os.path.exists(args.script):
        script_text = Path(args.script).read_text().strip()
    else:
        script_text = args.script
    
    # Get duration
    if args.duration:
        duration = args.duration
    elif args.audio:
        duration = get_audio_duration(args.audio)
    elif args.video:
        result = subprocess.run([
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "csv=p=0", args.video
        ], capture_output=True, text=True)
        duration = float(result.stdout.strip())
    else:
        # Estimate from word count (~2.5 words/second)
        duration = len(script_text.split()) / 2.5
    
    print(f"📝 Script: {len(script_text.split())} words")
    print(f"⏱️ Duration: {duration:.1f}s")
    print(f"🎨 Style: {args.style}")
    
    # Generate ASS file
    ass_path = args.output if args.output.endswith('.ass') else args.output + '.ass'
    generate_ass_captions(script_text, duration, ass_path, args.style)
    print(f"✅ ASS captions: {ass_path}")
    
    # Burn into video if provided
    if args.video:
        if args.output.endswith('.ass'):
            video_output = args.output.replace('.ass', '_captioned.mp4')
        else:
            video_output = args.output if args.output.endswith('.mp4') else args.output + '.mp4'
        
        burn_ass_captions(args.video, ass_path, video_output)
        print(f"✅ Captioned video: {video_output}")


if __name__ == "__main__":
    main()
