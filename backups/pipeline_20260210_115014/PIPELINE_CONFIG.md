# Ninja Content Pipeline Configuration
*Last updated: 2026-02-10*

## Current Settings

### Video Generation
- **Reference Image:** `assets/reference/ninja_helmet_v4_hires.jpg` (1568x2720)
- **Voice ID:** `aQspKon0UdKOuBZQQrEE` (Neurodivergent Ninja Remix)
- **TTS Model:** `eleven_v3`
- **Avatar:** Kling Avatar v2 Standard via fal.ai
- **Captions:** DISABLED by default (use `--captions` to enable)
- **Music:** Disabled by default (use without `--no-music` to enable)

### Thumbnail Generation
- **Topic headline text:** Auto-generated from topic keywords
- **Branding:** Neurodivergent Ninja logo/text included
- **Style:** Pixar/Disney 3D animation aesthetic
- **Reference:** `assets/reference/ninja_helmet_v3_futuristic.jpg`

### Standard Intro
```
What's up my fellow ninjas!? This is Neurodivergent Ninja here and I'm back with another quick update video.
```

### Standard Outro
```
Thanks for watching my video! Please like, follow and subscribe to help this channel grow! This is Neurodivergent Ninja signing off. I'll see you in my next video!
```

## Command Reference

```bash
# Standard video (no captions, with thumbnail)
ninja_content.py --script-file script.txt --no-music --thumbnail

# With captions (if needed)
ninja_content.py --script-file script.txt --no-music --thumbnail --captions

# Full auto mode
ninja_content.py --auto --no-music --thumbnail
```

## Backup Location
`backups/pipeline_20260210_115014/`

## Key Files
- `scripts/ninja_content.py` - Main pipeline script
- `scripts/ninja_thumbnail.py` - Thumbnail generation
- `assets/reference/ninja_helmet_v4_hires.jpg` - Character reference image
