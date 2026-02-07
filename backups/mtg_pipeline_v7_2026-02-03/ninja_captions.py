#!/usr/bin/env python3
"""
ninja_captions.py — Create Instagram Reels-style animated captions

Generates ASS (Advanced SubStation Alpha) subtitles with:
- Word-by-word highlighting using Whisper timestamps
- Pop-in animation effects  
- Emphasis styling for key words
- Modern social media aesthetic
"""

import argparse
import json
import os
import re
import subprocess
import tempfile
import urllib.request
from pathlib import Path


def get_openai_key():
    """Get OpenAI API key from environment or .env files."""
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        return key
    
    env_files = [
        "/home/ndninja/n8n/.env",
        "/home/ndninja/projects/content-automation/.env",
    ]
    for env_file in env_files:
        if os.path.exists(env_file):
            with open(env_file) as f:
                for line in f:
                    if line.startswith("OPENAI_API_KEY="):
                        return line.strip().split("=", 1)[1].strip('"').strip("'")
    return None


def extract_audio_from_video(video_path, output_path=None):
    """Extract audio from video file."""
    if output_path is None:
        output_path = tempfile.mktemp(suffix=".wav")
    
    subprocess.run([
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        output_path
    ], capture_output=True)
    
    return output_path


def transcribe_with_whisper(audio_path):
    """Transcribe audio using OpenAI Whisper API with word-level timestamps."""
    api_key = get_openai_key()
    if not api_key:
        raise RuntimeError("OpenAI API key not found")
    
    # Read audio file
    with open(audio_path, "rb") as f:
        audio_data = f.read()
    
    # Build multipart form data
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="audio.wav"\r\n'
        f"Content-Type: audio/wav\r\n\r\n"
    ).encode() + audio_data + (
        f"\r\n--{boundary}\r\n"
        f'Content-Disposition: form-data; name="model"\r\n\r\n'
        f"whisper-1\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="response_format"\r\n\r\n'
        f"verbose_json\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="timestamp_granularities[]"\r\n\r\n'
        f"word\r\n"
        f"--{boundary}--\r\n"
    ).encode()
    
    req = urllib.request.Request(
        "https://api.openai.com/v1/audio/transcriptions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read().decode())
    
    return result


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


def identify_emphasis_words(text):
    """Identify words that should be emphasized."""
    emphasis_patterns = [
        r'\b(breaking|huge|insane|crazy|wild|massive|major)\b',
        r'\b(AI|GPT|Meta|Google|Apple|OpenAI|Microsoft|Magic|Wizards)\b',
        r'\b(million|billion|trillion)\b',
        r'\b(free|paid|cost|price|charge)\b',
        r'\b(banned|blocked|censored|removed)\b',
        r'\b(first|new|latest|just)\b',
        r'\b(warning|alert|urgent)\b',
        r'\b(hot take|my hot take)\b',
    ]
    
    emphasis_words = set()
    for pattern in emphasis_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        emphasis_words.update(w.lower() for w in matches)
    
    return emphasis_words


def create_animated_chunk(words_with_times, chunk_start, chunk_end, emphasis_words):
    """Create an ASS dialogue line with word-by-word animation using real timestamps."""
    animated_parts = []
    
    for word_info in words_with_times:
        word = word_info["word"]
        word_start = word_info["start"] - chunk_start  # Relative to chunk
        word_end = word_info["end"] - chunk_start
        
        # Clamp to chunk bounds
        word_start = max(0, word_start)
        word_end = min(chunk_end - chunk_start, word_end)
        
        is_emphasis = word.lower().strip('.,!?') in emphasis_words
        
        if is_emphasis:
            animated_parts.append(
                f"{{\\t({int(word_start*1000)},{int(word_start*1000)+100},\\fscx110\\fscy110\\c&H00D4FF&)}}"
                f"{{\\t({int(word_end*1000)-100},{int(word_end*1000)},\\fscx100\\fscy100\\c&HFFFFFF&)}}"
                f"{word} "
            )
        else:
            animated_parts.append(
                f"{{\\t({int(word_start*1000)},{int(word_start*1000)+80},\\c&H00FFFF&)}}"
                f"{{\\t({int(word_start*1000)+80},{int(word_end*1000)},\\c&HFFFFFF&)}}"
                f"{word} "
            )
    
    return "".join(animated_parts).strip()


def create_pop_in_effect(text, delay_ms=0):
    """Add pop-in animation effect to text."""
    return (
        f"{{\\fscx0\\fscy0\\t({delay_ms},{delay_ms+150},\\fscx110\\fscy110)}}"
        f"{{\\t({delay_ms+150},{delay_ms+200},\\fscx100\\fscy100)}}"
        f"{text}"
    )


def generate_ass_from_whisper(whisper_result, output_path, style="animated", words_per_chunk=4):
    """Generate ASS caption file from Whisper word-level timestamps."""
    
    words = whisper_result.get("words", [])
    if not words:
        raise ValueError("No word-level timestamps in Whisper result")
    
    full_text = " ".join(w["word"] for w in words)
    emphasis_words = identify_emphasis_words(full_text)
    
    ass_content = create_ass_header()
    
    # Group words into chunks
    chunks = []
    for i in range(0, len(words), words_per_chunk):
        chunk_words = words[i:i+words_per_chunk]
        if chunk_words:
            chunks.append(chunk_words)
    
    for chunk_words in chunks:
        chunk_start = chunk_words[0]["start"]
        chunk_end = chunk_words[-1]["end"]
        
        start_str = format_ass_time(chunk_start)
        end_str = format_ass_time(chunk_end)
        
        if style == "animated":
            text = create_animated_chunk(chunk_words, chunk_start, chunk_end, emphasis_words)
            text = create_pop_in_effect(text, delay_ms=0)
        elif style == "pop":
            chunk_text = " ".join(w["word"] for w in chunk_words)
            text = create_pop_in_effect(chunk_text)
        else:
            text = " ".join(w["word"] for w in chunk_words)
        
        ass_content += f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text}\n"
    
    with open(output_path, 'w') as f:
        f.write(ass_content)
    
    return output_path


def generate_ass_estimated(script_text, duration, output_path, style="animated"):
    """Generate ASS caption file using estimated timing (fallback)."""
    
    words = script_text.split()
    time_per_word = duration / len(words)
    
    emphasis_words = identify_emphasis_words(script_text)
    
    ass_content = create_ass_header()
    
    words_per_chunk = 4
    for i in range(0, len(words), words_per_chunk):
        chunk_words = words[i:i+words_per_chunk]
        chunk_start = i * time_per_word
        chunk_end = min((i + words_per_chunk) * time_per_word, duration)
        
        start_str = format_ass_time(chunk_start)
        end_str = format_ass_time(chunk_end)
        
        chunk_text = " ".join(chunk_words)
        
        if style == "animated":
            text = create_pop_in_effect(chunk_text)
        elif style == "pop":
            text = create_pop_in_effect(chunk_text)
        else:
            text = chunk_text
        
        ass_content += f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text}\n"
    
    with open(output_path, 'w') as f:
        f.write(ass_content)
    
    return output_path


def burn_ass_captions(video_path, ass_path, output_path):
    """Burn ASS captions into video."""
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
    parser.add_argument("--audio", "-a", help="Audio file (for Whisper timing)")
    parser.add_argument("--duration", "-d", type=float, help="Duration in seconds (fallback)")
    parser.add_argument("--video", "-v", help="Video to burn captions into")
    parser.add_argument("--output", "-o", required=True, help="Output file")
    parser.add_argument("--style", choices=["animated", "pop", "plain"], default="animated")
    parser.add_argument("--no-whisper", action="store_true", help="Skip Whisper, use estimated timing")
    
    args = parser.parse_args()
    
    # Get script text
    if os.path.exists(args.script):
        script_text = Path(args.script).read_text().strip()
    else:
        script_text = args.script
    
    # Get duration from video if available
    duration = args.duration
    if not duration and args.video:
        result = subprocess.run([
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "csv=p=0", args.video
        ], capture_output=True, text=True)
        duration = float(result.stdout.strip())
    
    print(f"📝 Script: {len(script_text.split())} words")
    print(f"⏱️ Duration: {duration:.1f}s")
    print(f"🎨 Style: {args.style}")
    
    # Determine ASS output path
    ass_path = args.output if args.output.endswith('.ass') else args.output + '.ass'
    
    # Try to use Whisper for accurate timestamps
    whisper_result = None
    if not args.no_whisper:
        try:
            # Extract audio from video if needed
            if args.video:
                print("🎤 Extracting audio from video...")
                audio_path = extract_audio_from_video(args.video)
            elif args.audio:
                audio_path = args.audio
            else:
                audio_path = None
            
            if audio_path:
                print("🔊 Transcribing with Whisper (word-level timestamps)...")
                whisper_result = transcribe_with_whisper(audio_path)
                print(f"   ✅ Got {len(whisper_result.get('words', []))} word timestamps")
                
                # Clean up temp audio
                if args.video and audio_path != args.audio:
                    os.unlink(audio_path)
        except Exception as e:
            print(f"   ⚠️ Whisper failed: {e}")
            print("   Falling back to estimated timing...")
    
    # Generate captions
    if whisper_result and whisper_result.get("words"):
        generate_ass_from_whisper(whisper_result, ass_path, args.style)
    else:
        if not duration:
            duration = len(script_text.split()) / 2.5  # Estimate
        generate_ass_estimated(script_text, duration, ass_path, args.style)
    
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
