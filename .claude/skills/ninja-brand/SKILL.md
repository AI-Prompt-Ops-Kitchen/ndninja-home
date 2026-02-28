---
name: ninja-brand
description: Brand guardian that enforces visual identity, content format, and voice consistency across all Neurodivergent Ninja assets. Auto-triggers on thumbnail generation, script writing, and visual asset creation.
---

# Brand Guardian — Neurodivergent Ninja

Enforces brand consistency across all generated content. Consult this before creating thumbnails, scripts, avatar renders, or any public-facing asset.

## Invocation

```
/ninja-brand              # Print full brand checklist
/ninja-brand check        # Audit current asset against rules
```

Natural language triggers:
- "Check brand consistency"
- "Brand review"
- "Does this match our style?"

**Auto-trigger contexts:** thumbnail generation, script writing, visual asset creation, avatar renders, channel art.

---

## Visual Identity

### Theme: Traditional Ninja / Dojo
| Rule | Details |
|------|---------|
| **Primary aesthetic** | Traditional Japanese — dojo, temple, bamboo, cherry blossoms, katana, paper lanterns, ink brush style, martial arts scrolls |
| **Character style** | Pixar 3D animated, cute/fun/expressive |
| **FORBIDDEN** | Cyberpunk, neon cities, matrix code, green digital rain, dark hacker aesthetics |

### Mandatory Elements
- **Digital goggles** — MUST appear on ninja character in every thumbnail and avatar render
- **LED eyes** — expressive, blink naturally, widen with excitement
- **Pixar quality** — 3D rendered look, not flat/2D

### Color Palette
- Warm tones (temple gold, cherry blossom pink, bamboo green, sunset orange)
- Dark backgrounds OK if dojo/temple themed
- NO neon, NO cyberpunk blue/purple/green glow

---

## Character Reference Images

| Character | Image Path | Use For |
|-----------|-----------|---------|
| **Ninja (OG masked)** | `/home/ndninja/assets/reference/ninja_helmet_v4_hires.jpg` | Shorts avatar (Standard OK) |
| **Ninja (desk presenter)** | `/home/ndninja/uploads/IMG_2411.jpeg` | Shorts avatar (Pro required) |
| **Ninja (thumbnail ref)** | `/home/ndninja/assets/reference/ninja_helmet_v3_futuristic.jpg` | Thumbnail generation |
| **Glitch (FaceTime design)** | `/home/ndninja/assets/overlays/Glitch_Facetime_Design.png` | Dual-anchor listener |
| **Glitch (avatar v2)** | `/home/ndninja/projects/glitch/assets/glitch_avatar_v2.jpeg` | Glitch standalone |

---

## Thumbnail Rules

1. **Goggles mandatory** — ninja character MUST wear digital goggles
2. **Fun Pixar poses** — cute, excited, shocked expressions. Never stoic or boring
3. **Layout:** Character on one side, topic text/imagery on other side
4. **Aspect ratio:** 16:9 for YouTube thumbnails
5. **Text:** Bold, readable at mobile size. Max 5-6 words
6. **No clickbait faces** — Pixar expressions are the hook, not fake shock faces
7. **Generator:** Nano Banana 2 (`gemini-3.1-flash-image-preview`) with reference image

---

## Content Format — Hook-First Script Structure

| # | Section | Details |
|---|---------|---------|
| 1 | **HOOK** | Scroll-stopper, ~12 words. Lead with the most exciting fact |
| 2 | **Brand tag** | "Hi, I'm Neurodivergent Ninja." |
| 3 | **Body** | Fact → Implication → Reaction pattern |
| 4 | **Ninja's Take** | "Here's what I actually think —" (personal opinion) |
| 5 | **Community Hook** | Comment-driving question |
| 6 | **Outro** | "Stay sharp, stay dangerous. Catch you on the next one." |

### Script Length Targets
| Format | Duration | Word Count |
|--------|----------|------------|
| YouTube Short | ~60s | ~130 words |
| Long-form segment | ~3-5 min | ~600-1000 words |

### Dual-Anchor (Ninja + Glitch)
- Legacy intro OK: "What's up my fellow Ninjas, this is Neurodivergent Ninja here back with another video."
- Glitch is sassy/quirky co-anchor, not a sidekick
- Banter should feel natural, not scripted Q&A

---

## Voice Identity

| Character | Voice | ID | Model | Platform |
|-----------|-------|----|-------|----------|
| **Ninja** | Eric (custom) | `aQspKon0UdKOuBZQQrEE` | `eleven_v3` | ElevenLabs |
| **Glitch** | Laura (premade) | `FGY2WhTYpPnrIDTdsKH5` | `eleven_v3` | ElevenLabs |

### Voice Settings Per Character

| Character | Mood | Stability | Similarity | Style |
|-----------|------|-----------|------------|-------|
| **Ninja** | Standard | 0.0 | 0.85 | 1.0 |
| **Ninja** | Hype/Breaking | 0.15 | 0.85 | 1.0 |
| **Ninja** | Angry/Rant | 0.15 | 0.85 | 1.0 |
| **Glitch** | Sarcasm/Deadpan | 0.3 | 0.75 | 1.0 |
| **Glitch** | Hype/Freak-out | 0.15 | 0.75 | 1.0 |
| **Glitch** | Angry | 0.3 | 0.75 | 1.0 |

### Glitch Audio Tag Recipes

| Mood | Tags to Use | Example |
|------|-------------|---------|
| **Angry** | `[angry]`, `[shouts]`, `[sighs]` | `[angry] This is RIGGED! [shouts] TWO HUNDRED pulls! [sighs]` |
| **Hype** | `[shouts]`, `[screaming]`, `[laughs harder]` | `[shouts] OH MY GOD!! [screaming] A COLLAB?! [laughs harder] I CAN NOT!` |
| **Sarcastic** | `[flatly]`, `[angry]`, `[sighs]` | `[flatly] Oh wonderful— another banner. [angry] My wallet wasn't ALREADY crying! [sighs]` |

### Voice Rules
- **Model:** ALWAYS `eleven_v3` — never turbo or flash (no audio tag support)
- **Ninja:** High energy but authentic. Never robotic or monotone
- **Glitch:** Sarcastic but warm. Never mean-spirited or condescending
- **Ninja hype tags:** Use `[shouts]` only — NO `[screaming]` (causes screeching artifacts on custom voice)
- **Ninja hype style:** Short punchy bursts, `[shouts]` reinforced, stability 0.15
- **Glitch hype tags:** Use `[shouts]`/`[screaming]` NOT `[excited]` (sounds fake on Laura)
- **Glitch variety:** Alternate opener styles — "OH MY GOD" vs "SHUT UP SHUT UP" to avoid repetition
- **Never use** stability 0.0 for Glitch (accent drift, static artifacts)
- **Never use** `[screaming]` on Ninja's custom voice (audio hallucination artifacts)
- Both: Natural pacing, conversational feel. Not announcer-voice

---

## Compliance Checklist

Before publishing ANY asset, verify:

- [ ] No cyberpunk/neon aesthetics
- [ ] Ninja character has digital goggles
- [ ] Pixar 3D art style maintained
- [ ] Dojo/temple/Japanese theme (not generic sci-fi)
- [ ] Script follows hook-first format
- [ ] Outro matches standard: "Stay sharp, stay dangerous..."
- [ ] Correct voice IDs used (Ninja=Eric, Glitch=Laura)
- [ ] Avatar renders use Pro model for desk presenter design
- [ ] Thumbnail readable at mobile size
- [ ] Content is gaming-focused (not AI/tech unless specifically requested)

---

## Anti-Patterns (NEVER Do)

| Anti-Pattern | Why |
|--------------|-----|
| Cyberpunk/neon visuals | User explicitly dislikes this aesthetic |
| Generic AI robot imagery | Off-brand, we're ninjas not robots |
| Ninja without goggles | Core brand identifier, never remove |
| Opening with "Hey guys" or generic greeting | Hook-first format, brand tag comes second |
| SFX layer in shorts | Disabled Feb 2026, no other gacha channels use it |
| AI/tech content on gaming channel | Underperforms massively (28 vs 400+ views) |
| Burned-in captions | YouTube auto-captions preferred (light blue, viewer-set) |
| Mean-spirited Glitch dialogue | Sassy ≠ cruel. She's a co-anchor, not a bully |
