# News Update Pipeline

**Related to:** Ninja Content Pipeline (shares voice clone, tech stack)

## Visual Style Reference
- **Reference image:** `assets/reference/ninja_news_anchor.jpg`
- **Style:** 3D animated character (Pixar/cartoon style)
- **Character:** Ninja at news desk
  - Black hood + face mask (only blue eyes visible)
  - Black tactical armor with blue accent lighting
  - Katana on back
  - Fingerless gloves
- **Setting:** Modern tech news studio
  - Blue circuit board patterns on walls
  - "LIVE" indicator (red)
  - "BREAKING TECH NEWS" lower third
  - Blue neon/LED accent lighting throughout
- **Vibe:** Professional but playful tech news presenter

## Status
- [x] Reference image saved (`ninja_news_anchor.jpg`)
- [x] Veo prompt updated for news anchor style (head still, eyes on camera)
- [ ] Add "BREAKING TECH NEWS" lower-third overlay
- [ ] Add "LIVE" badge overlay
- [ ] Create `--news` flag for easy mode switching

## Veo Prompt (working)
```
Animate this 3D Pixar-style ninja character at the tech news desk.
Subtle idle animation - blinking expressive blue eyes, minimal natural hand gestures on desk.
Character keeps head perfectly still, eyes locked on camera at all times, no head turning.
Professional news anchor posture, facing directly forward throughout entire clip.
Keep exact character design and studio background. Smooth Pixar-quality animation.
Camera locked in static medium shot position. No camera movement.
```

## Test Results
- v1: Head turned, blob artifact visible — ❌
- v2: Head still, eyes locked — ✅
- v3: Whisper word-sync captions restored — ✅

## Notes
- Uses same tech stack as main content pipeline
- Command: `ninja_content.py --image assets/reference/ninja_news_anchor.jpg --no-music`
