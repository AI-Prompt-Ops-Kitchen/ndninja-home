#!/usr/bin/env python3
"""
ninja_synced_captions.py — Word-synced animated captions using Whisper

Creates Instagram Reels-style captions that highlight each word AS it's spoken.
"""

import os
import subprocess
import whisper
from pathlib import Path


def get_word_timestamps(audio_path, model_size="tiny", padding_offset=0.5, original_script=None):
    """Get word-level timestamps from audio using Whisper.
    
    If original_script is provided, use those words instead of Whisper's
    transcription (which can have errors like 'Genie' -> 'G & E').
    """
    print(f"🎙️ Loading Whisper ({model_size})...")
    model = whisper.load_model(model_size)
    
    print("📝 Transcribing for word timestamps...")
    result = model.transcribe(audio_path, word_timestamps=True)
    
    # Extract Whisper's words and timing
    whisper_words = []
    for segment in result["segments"]:
        for word in segment.get("words", []):
            whisper_words.append({
                "word": word["word"].strip(),
                "start": word["start"] + padding_offset,
                "end": word["end"] + padding_offset
            })
    
    # If original script provided, use those words with Whisper's timing
    if original_script:
        script_words = original_script.split()
        
        # If counts match reasonably, replace words but keep timing
        if len(script_words) > 0 and len(whisper_words) > 0:
            # Scale timing to fit script words if counts differ
            if len(script_words) != len(whisper_words):
                print(f"   ⚠️ Word count mismatch: script={len(script_words)}, whisper={len(whisper_words)}")
                # Interpolate timing for script words
                if len(whisper_words) >= 2:
                    total_duration = whisper_words[-1]["end"] - whisper_words[0]["start"]
                    start_time = whisper_words[0]["start"]
                    word_duration = total_duration / len(script_words)
                    
                    words = []
                    for i, word in enumerate(script_words):
                        words.append({
                            "word": word,
                            "start": start_time + (i * word_duration),
                            "end": start_time + ((i + 1) * word_duration)
                        })
                    print(f"   ✅ Using script words with interpolated timing")
                    return words
            else:
                # Counts match - use script words with Whisper timing
                words = []
                for i, script_word in enumerate(script_words):
                    words.append({
                        "word": script_word,
                        "start": whisper_words[i]["start"],
                        "end": whisper_words[i]["end"]
                    })
                print(f"   ✅ Using script words with Whisper timing")
                return words
    
    return whisper_words


def format_ass_time(seconds):
    """Format seconds as ASS timestamp."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int((seconds % 1) * 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"


def create_synced_ass(words, output_path, width=1080, height=1920):
    """Create ASS captions with word-by-word sync."""
    
    # ASS header
    ass_content = f"""[Script Info]
Title: Synced Ninja Captions
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
PlayResX: {width}
PlayResY: {height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,72,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,4,2,2,40,40,60,1
Style: Highlight,Arial Black,80,&H0000FFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,110,110,0,0,1,5,2,2,40,40,60,1
Style: Emphasis,Arial Black,85,&H0000D4FF,&H000000FF,&H00000000,&H80000000,1,0,0,0,115,115,0,0,1,5,3,2,40,40,60,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    # Emphasis words (appear larger/colored)
    emphasis_words = {'ai', 'ninja', 'ninjas', 'breaking', 'huge', 'insane', 
                      'meta', 'google', 'apple', 'openai', 'army', 'production', 
                      'productions', 'million', 'billion'}
    
    # Group words into display chunks (3-5 words that fit on screen)
    chunks = []
    current_chunk = []
    current_length = 0
    max_chars = 25  # Max characters per line before wrapping
    
    for word_info in words:
        word = word_info["word"]
        if current_length + len(word) > max_chars and current_chunk:
            chunks.append(current_chunk)
            current_chunk = []
            current_length = 0
        current_chunk.append(word_info)
        current_length += len(word) + 1
    
    if current_chunk:
        chunks.append(current_chunk)
    
    # Generate ASS events for each chunk
    for chunk in chunks:
        if not chunk:
            continue
            
        chunk_start = chunk[0]["start"]
        chunk_end = chunk[-1]["end"] + 0.1  # Small buffer
        
        start_str = format_ass_time(chunk_start)
        end_str = format_ass_time(chunk_end)
        
        # Build animated text with word-by-word highlighting
        text_parts = []
        for i, word_info in enumerate(chunk):
            word = word_info["word"]
            word_start = word_info["start"] - chunk_start  # Relative to chunk start
            word_end = word_info["end"] - chunk_start
            
            # Convert to milliseconds for ASS animation
            start_ms = int(word_start * 1000)
            end_ms = int(word_end * 1000)
            
            is_emphasis = word.lower().strip('.,!?') in emphasis_words
            
            if is_emphasis:
                # Emphasis word: orange/yellow, bigger, with pop
                text_parts.append(
                    f"{{\\t({start_ms},{start_ms+100},\\fscx115\\fscy115\\c&H00D4FF&)}}"
                    f"{{\\t({end_ms},{end_ms+100},\\fscx100\\fscy100\\c&HFFFFFF&)}}"
                    f"{word} "
                )
            else:
                # Normal word: cyan highlight then white
                text_parts.append(
                    f"{{\\t({start_ms},{start_ms+50},\\c&H00FFFF&\\fscx105\\fscy105)}}"
                    f"{{\\t({end_ms},{end_ms+50},\\c&HFFFFFF&\\fscx100\\fscy100)}}"
                    f"{word} "
                )
        
        animated_text = "".join(text_parts).strip()
        
        # Add pop-in effect for the whole chunk
        pop_in = "{\\fscx0\\fscy0\\t(0,100,\\fscx105\\fscy105)}{\\t(100,150,\\fscx100\\fscy100)}"
        
        ass_content += f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{pop_in}{animated_text}\n"
    
    with open(output_path, 'w') as f:
        f.write(ass_content)
    
    print(f"✅ Synced captions: {output_path}")
    return output_path


def burn_synced_captions(video_path, audio_path, output_path, model_size="tiny", original_script=None):
    """Full workflow: transcribe audio, create synced ASS, burn into video.
    
    If original_script is provided, uses those words instead of Whisper's
    transcription to avoid errors like 'Genie' -> 'G & E'.
    """
    
    # Get word timestamps (use original script words if provided)
    words = get_word_timestamps(audio_path, model_size, original_script=original_script)
    print(f"   Found {len(words)} words")
    
    # Create ASS file
    ass_path = "/tmp/synced_captions.ass"
    create_synced_ass(words, ass_path)
    
    # Burn into video
    print("🎬 Burning synced captions...")
    ass_escaped = ass_path.replace(':', '\\:')
    
    subprocess.run([
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"ass={ass_escaped}",
        "-c:a", "copy",
        output_path
    ], capture_output=True)
    
    if os.path.exists(output_path):
        print(f"✅ Output: {output_path}")
        return output_path
    return None


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", "-v", required=True)
    parser.add_argument("--audio", "-a", required=True)
    parser.add_argument("--output", "-o", required=True)
    parser.add_argument("--model", "-m", default="tiny", choices=["tiny", "base", "small"])
    args = parser.parse_args()
    
    burn_synced_captions(args.video, args.audio, args.output, args.model)
