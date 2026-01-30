# 🥷 Ninja Content Pipeline Scripts

## Main Pipeline

### `ninja_content.py` — Full Automated Pipeline
The main entry point. Discovers news, generates scripts, creates videos with TTS, captions, and thumbnails.

```bash
# Full auto mode
python ninja_content.py --auto --no-music --thumbnail

# Discover stories and pick one
python ninja_content.py --discover
python ninja_content.py --pick 3 --no-music --thumbnail

# Custom script
python ninja_content.py --script "Your script text" --no-music --thumbnail

# Publish to YouTube
python ninja_content.py --auto --no-music --thumbnail --publish youtube --privacy unlisted
```

**Options:**
- `--auto` — Full auto: fetch news, pick top story, generate everything
- `--discover` — Show available stories
- `--pick N` — Pick story number N
- `--script "text"` — Use custom script
- `--script-file file.txt` — Load script from file
- `--no-music` — Skip background music (recommended)
- `--thumbnail` — Generate matching thumbnail
- `--thumb-style` — Style: engaging, shocked, thinking, pointing, excited
- `--publish youtube` — Auto-upload to YouTube
- `--privacy` — Video privacy: private, unlisted, public

---

## Supporting Scripts

### `ninja_scriptgen.py` — Script Generator
Fetches trending tech/gaming news and generates short-form video scripts.

```bash
python ninja_scriptgen.py --discover          # Show stories
python ninja_scriptgen.py --auto              # Auto-pick and generate
python ninja_scriptgen.py --topic "Custom topic"
```

### `ninja_thumbnail.py` — Thumbnail Generator
Creates YouTube thumbnails using Nano Banana Pro (Gemini image gen).

```bash
python ninja_thumbnail.py --topic "Topic" --style shocked
```

### `ninja_multiclip.py` — Multi-Clip Video Generator
Generates multiple Veo clips with varied prompts. **Note: Single clip mode is preferred.**

```bash
python ninja_multiclip.py --image ref.jpg --output out.mp4 --clips 4 --vertex
```

---

## Legacy/Specialized Scripts

### `ninja_pipeline.py` — Original Ditto Pipeline
Uses Ditto TalkingHead on RTX 4090 for lip-sync. Replaced by Veo for masked avatars.

### `ninja_background.py` — Static Background Compositor
Composites avatar over static backgrounds using rembg.

### `ninja_video_background.py` — Animated Background Compositor
Composites avatar over animated video backgrounds.

### `ninja_upscale.py` — Video Upscaler
Upscales video from 288×512 to 1080×1920.

### `ninja_captions.py` / `ninja_synced_captions.py` — Caption Burners
Burns animated captions into video using Whisper transcription.

### `ninja_music.py` — Background Music
Adds royalty-free background music to videos.

---

## YouTube Integration

### `youtube/youtube_auth.py` — OAuth Setup
First-time authentication for YouTube uploads.

### `youtube/youtube_upload.py` — Video Uploader
Uploads videos with custom thumbnails to YouTube.

---

## Configuration

| Setting | Location |
|---------|----------|
| Voice Clone ID | `pDrEFcc78kuc76ECGkU8` |
| Reference Image | `assets/reference/ninja_concept.jpg` |
| Pixar Avatar | `assets/reference/ninja_pixar_avatar.jpg` |
| Vertex AI Project | `gen-lang-client-0601509945` |
| Google ADC | `~/.config/gcloud/application_default_credentials.json` |
