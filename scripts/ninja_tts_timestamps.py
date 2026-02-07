#!/usr/bin/env python3
"""
ElevenLabs TTS with word-level timestamps for perfect caption sync.
"""

import os
import base64
import requests
from pathlib import Path
from typing import List, Tuple

def load_elevenlabs_key():
    """Load ElevenLabs API key from env file."""
    env_file = Path('/home/ndninja/projects/content-automation/.env')
    with open(env_file) as f:
        for line in f:
            if line.startswith('ELEVENLABS_API_KEY='):
                return line.strip().split('=', 1)[1].strip('"\'')
    raise ValueError("ELEVENLABS_API_KEY not found")

def generate_tts_with_timestamps(
    text: str,
    output_audio: str,
    voice_id: str = 'pDrEFcc78kuc76ECGkU8',
    model_id: str = 'eleven_multilingual_v2',
    stability: float = 0.65,
    similarity_boost: float = 0.75,
    style: float = 0.4
) -> List[Tuple[str, float, float]]:
    """
    Generate TTS audio with word-level timestamps.
    
    Returns:
        List of (word, start_time, end_time) tuples
    """
    key = load_elevenlabs_key()
    
    print(f"🎙️ Generating TTS with timestamps...")
    
    resp = requests.post(
        f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps',
        headers={'xi-api-key': key, 'Content-Type': 'application/json'},
        json={
            'text': text,
            'model_id': model_id,
            'voice_settings': {
                'stability': stability,
                'similarity_boost': similarity_boost,
                'style': style
            }
        }
    )
    
    if resp.status_code != 200:
        raise Exception(f"ElevenLabs API error: {resp.text}")
    
    data = resp.json()
    
    # Save audio
    audio_bytes = base64.b64decode(data['audio_base64'])
    with open(output_audio, 'wb') as f:
        f.write(audio_bytes)
    print(f"   ✅ Audio saved: {output_audio} ({len(audio_bytes)//1024}KB)")
    
    # Extract word timestamps from character timestamps
    alignment = data['alignment']
    chars = alignment['characters']
    starts = alignment['character_start_times_seconds']
    ends = alignment['character_end_times_seconds']
    
    words = []
    current_word = ""
    word_start = None
    word_end = None
    
    for i, char in enumerate(chars):
        if char in ' \n\t':
            if current_word:
                words.append((current_word, word_start, word_end))
                current_word = ""
                word_start = None
        else:
            if word_start is None:
                word_start = starts[i]
            word_end = ends[i]
            current_word += char
    
    # Don't forget the last word
    if current_word:
        words.append((current_word, word_start, word_end))
    
    print(f"   ✅ Extracted {len(words)} word timestamps")
    
    return words

def generate_ass_from_timestamps(
    words: List[Tuple[str, float, float]],
    output_ass: str,
    words_per_group: int = 3,
    font_name: str = "Bangers",
    font_size: int = 42
):
    """Generate ASS subtitle file from word timestamps."""
    
    def format_time(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h}:{m:02d}:{s:05.2f}"
    
    # ASS header
    ass_content = f"""[Script Info]
Title: Ninja Captions
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,3,2,2,40,40,200,1
Style: Highlight,{font_name},{font_size},&H0000FFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,3,2,2,40,40,200,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    # Group words and create events
    i = 0
    while i < len(words):
        group = words[i:i + words_per_group]
        
        group_start = group[0][1]
        group_end = group[-1][2]
        
        # Build text with highlight for each word
        for j, (word, w_start, w_end) in enumerate(group):
            # Create event for this word highlighted
            text_parts = []
            for k, (w, _, _) in enumerate(group):
                clean_word = w.rstrip('.,!?;:')
                punct = w[len(clean_word):]
                if k == j:
                    text_parts.append(f"{{\\c&H00FFFF&}}{clean_word}{{\\c&HFFFFFF&}}{punct}")
                else:
                    text_parts.append(w)
            
            text = " ".join(text_parts)
            ass_content += f"Dialogue: 0,{format_time(w_start)},{format_time(w_end)},Default,,0,0,0,,{text}\n"
        
        i += words_per_group
    
    with open(output_ass, 'w') as f:
        f.write(ass_content)
    
    print(f"   ✅ ASS captions saved: {output_ass}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: ninja_tts_timestamps.py <text_file> <output_audio> [output_ass]")
        sys.exit(1)
    
    text = open(sys.argv[1]).read().strip()
    audio_out = sys.argv[2]
    ass_out = sys.argv[3] if len(sys.argv) > 3 else None
    
    words = generate_tts_with_timestamps(text, audio_out)
    
    if ass_out:
        generate_ass_from_timestamps(words, ass_out)
