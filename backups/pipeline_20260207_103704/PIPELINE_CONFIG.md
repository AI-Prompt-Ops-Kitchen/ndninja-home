# Ninja Content Pipeline - WORKING CONFIGURATION
## Backed up: 2026-02-07 10:37 EST

This is the VERIFIED WORKING configuration after 2 days of troubleshooting.

---

## 🎯 CRITICAL REQUIREMENTS

### Image Resolution
- **MINIMUM:** 1024x1792 (9:16 aspect ratio)
- **RECOMMENDED:** 1568x2720 (current working image)
- **⚠️ WhatsApp compresses images!** Enable HD mode or send as Document

### Working Reference Image
- **File:** `ninja_helmet_v4_hires.jpg`
- **Resolution:** 1568 x 2720
- **Size:** 337KB

---

## 🎙️ Voice Configuration

| Setting | Value |
|---------|-------|
| Voice ID | `aQspKon0UdKOuBZQQrEE` |
| Voice Name | Neurodivergent Ninja Remix |
| Model | `eleven_v3` |
| Stability | 0.5 |
| Similarity Boost | 0.75 |
| Style | 0.4 |

---

## 🎬 Avatar Generation

| Setting | Value |
|---------|-------|
| Service | fal.ai |
| Endpoint | `fal-ai/kling-video/ai-avatar/v2/standard` |
| Cost | ~$0.056/second |
| Prompt | "Professional tech news presenter with natural gestures and enthusiastic body language." |

---

## 📝 Standard Scripts

### Intro
```
What's up my fellow ninjas!? This is Neurodivergent Ninja here and I'm back with another quick update video.
```

### Outro
```
Thanks for watching my video! Please like, follow and subscribe to help this channel grow! This is Neurodivergent Ninja signing off. I'll see you in my next video!
```

---

## ⚠️ KNOWN ISSUES & SOLUTIONS

### Chinese/Foreign Text Appearing in Videos
**Cause:** Low resolution input images
**Solution:** Always use images at least 1024x1792. WhatsApp compresses images - use HD mode or send as Document.

### Mouth Showing Through Mask
**Cause:** Original ninja mask design
**Solution:** Use full helmet design (no visible face)

---

## 📁 Key Files

- `assets/reference/ninja_helmet_v4_hires.jpg` - Working reference image
- `scripts/ninja_scriptgen.py` - Script generation with intro/outro
- `scripts/ninja_thumbnail.py` - Thumbnail generation

---

## 🔧 Pipeline Steps

1. Write script (include standard intro/outro)
2. Generate TTS with ElevenLabs (Remix voice + eleven_v3)
3. Upload HIGH-RES image + audio to fal.ai
4. Generate Kling Avatar v2 Standard
5. Compress output with ffmpeg (crf 26)
6. Upload to YouTube/Instagram (no burned-in captions - use platform auto-captions)

---

*Do not modify this backup. Create a new backup before making changes.*
