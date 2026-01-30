# Ninja Content Pipeline — Project State

## Overview
Automated content creation pipeline for Neurodivergent Ninja YouTube/social media.

## Current Status: ✅ WORKING
Last updated: 2026-01-29

## Tech Stack
| Component | Technology | Notes |
|-----------|------------|-------|
| Video | Veo 3.1 via Vertex AI | `gen-lang-client-0601509945` |
| Voice | ElevenLabs | Clone ID: `pDrEFcc78kuc76ECGkU8` |
| Thumbnails | Nano Banana Pro | `gemini-2.5-flash-image` |
| Captions | FFmpeg + whisper | Burned into video |
| Auth | Google ADC | `~/.config/gcloud/application_default_credentials.json` |

## Key Files
- Main script: `scripts/ninja_content.py`
- Thumbnail: `scripts/ninja_thumbnail.py`
- B-roll generator: `scripts/ninja_broll.py`
- B-roll compositor: `scripts/ninja_broll_compositor.py`
- Multiclip: `scripts/ninja_multiclip.py`
- YouTube: `scripts/youtube/youtube_upload.py`
- Reference image: `assets/reference/ninja_concept.jpg` (photorealistic)
- Pixar avatar: `assets/reference/ninja_pixar_avatar.jpg` (for thumbnails)
- Prompt: `assets/prompts/ninja_commentator_v1.txt`

## Pipeline Command
```bash
# Full auto with thumbnail
ninja_content.py --auto --no-music --thumbnail --thumb-style shocked

# With B-roll cutaways (hides loop points!)
ninja_content.py --auto --no-music --thumbnail --broll

# Pick a story
ninja_content.py --discover
ninja_content.py --pick N --no-music --thumbnail

# Publish to YouTube (requires OAuth setup)
ninja_content.py --pick N --no-music --thumbnail --publish youtube --privacy unlisted
```

## Configuration Decisions
- **Single clip mode** (not multiclip) — better quality, cheaper
- **Hard loop** (no crossfade) — less obvious than crossfade
- **No background music** by default
- **Pixar-style** avatar for thumbnails

## Pending
- [ ] YouTube OAuth setup (need user to auth in browser)
- [ ] Instagram automation (harder, needs Meta Business API or browser automation)

## Don't Forget
- Nano Banana Pro is Google's image gen, NOT Imagen
- User's voice clone ID: `pDrEFcc78kuc76ECGkU8`
- Use Vertex AI for Veo (AI Studio rate limits)
