# MTG Secret Lair Pipeline Backup — v7 (2026-02-03)

## What's Here
- `ninja_mtg_script_v7.txt` — Final approved script
- `ninja_v7_raw.mp3` — ElevenLabs TTS (voice clone pDrEFcc78kuc76ECGkU8)
- `ninja_v7_padded.mp3` — TTS with 0.5s silence padding at start
- `ninja_mtg_v7_kling.mp4` — Raw Kling Avatar v2 output (no captions)
- `ninja_mtg_v7_final.mp4` — Final video with Whisper-synced animated captions
- `ninja_avatar.jpg` — Source image used for Kling Avatar
- `ninja_captions.py` — Caption overlay script
- `ninja_content.py` — Full content pipeline script

## Pipeline Steps (Manual)
1. **TTS:** ElevenLabs → voice clone → raw MP3
2. **Pad audio:** `ffmpeg -i raw.mp3 -af "adelay=500|500" -c:a libmp3lame padded.mp3`
3. **Kling Avatar:** Upload image + padded audio → fal-ai/kling-video/ai-avatar/v2/standard
4. **Captions:** `ninja_captions.py --script X --video Y --output Z --style animated`

## Key Settings
- Voice Clone ID: `pDrEFcc78kuc76ECGkU8`
- ElevenLabs model: `eleven_multilingual_v2`
- Stability: 0.5, Similarity: 0.75
- Kling: v2/standard tier
- Audio padding: 500ms adelay (prevents first words being cut off)
- Caption style: animated (word-by-word Whisper sync)
