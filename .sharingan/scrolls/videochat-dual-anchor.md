---
name: videochat-dual-anchor
domain: Content/Video Production
level: 3-tomoe
description: FaceTime-style vertical stack format for dual AI avatar YouTube Shorts. Solves ghost mouthing with 60Hz sine tone trick. Eliminates compositing seams entirely.
sources:
  - type: experimentation
    title: "4-iteration ghost mouthing elimination (Feb 24, 2026)"
    url: "file:///home/ndninja/scripts/test_videochat_render.py"
    date: "2026-02-24"
    confidence: high
  - type: experimentation
    title: "Shadow Council analysis — A-tier rating"
    url: "file:///home/ndninja/output/shadow_council_videochat.md"
    date: "2026-02-24"
    confidence: high
  - type: codebase
    title: "Production dual-anchor script"
    url: "file:///home/ndninja/scripts/ninja_dual_anchor.py"
    date: "2026-02-24"
    confidence: high
  - type: codebase
    title: "Video chat overlay generator"
    url: "file:///home/ndninja/scripts/generate_videochat_overlay.py"
    date: "2026-02-24"
    confidence: high
  - type: codebase
    title: "Webcam reference image generator"
    url: "file:///home/ndninja/scripts/generate_videochat_refs.py"
    date: "2026-02-24"
    confidence: high
last_updated: 2026-02-24
sources_count: 5
can_do_from_cli: true
---

# Video Chat Dual-Anchor Format

## Mental Model

Instead of compositing two AI avatars side-by-side at a news desk (which creates visible seams), stack them vertically like a FaceTime/Zoom call. Each character is a completely independent render in their own "room." The divider between panels IS the design — no seam to hide.

**Origin:** User's wife suggested it (Feb 24, 2026). Shadow Council rated it A-tier. Validated through 4 render iterations.

---

## The Ghost Mouthing Problem & Solution

### The Problem
When two AI avatars share a scene, the non-speaking character mouths the speaker's words ("ghost mouthing"). This happens because Kling Avatar v2 uses audio to drive lip sync — even with silent audio, the model generates mouth movement.

### The 60Hz Sine Wave Discovery

**4 iterations to solve it:**

| Version | Listener Audio | Listener Model | Result |
|---------|---------------|----------------|--------|
| v1 | Silent WAV (all zeros) | Pro | Full ghost mouthing |
| v2 | Silent WAV + anti-mouth prompts | Pro | Mostly fixed, some jitter |
| v3 | Pink noise (-50dB) | Standard | Almost there, occasional jitter |
| **v4** | **60Hz sine wave (-50dB)** | **Standard** | **CLEAN — no mouthing** |

**Why 60Hz sine works:**
- Pure digital silence (zeros) → model treats as missing/corrupt, hallucinates mouth
- Pink/white noise → random amplitude variation in speech frequencies (300-3400Hz) occasionally triggers lip sync
- 60Hz pure sine → constant amplitude, constant frequency, zero transients, well below speech range. Model sees "audio present, no speech content"

### Winning Configuration

**Speaker:**
- Model: Kling Avatar v2 **Pro** (expressiveness)
- Audio: Real TTS from ElevenLabs v3
- CFG scale: 0.7
- Negative prompt: Standard (body artifacts)

**Listener:**
- Model: Kling Avatar v2 **Standard** (less expressive = less mouth activity)
- Audio: 60Hz sine wave at amplitude 30/32767 (~-60dB)
- CFG scale: **0.9** (higher = stricter prompt enforcement)
- Prompt must include: "Mouth closed, lips together at all times. No talking, no lip movement."
- Negative prompt must include: "talking, speaking, open mouth, lip movement, mouth open, mouthing words, lip sync"

---

## Visual Layout (9:16 Portrait — 1080x1920)

```
+─────────────────────────────+
│  STATUS BAR (signal / LIVE) │  32px
+─────────────────────────────+
│                             │
│      NINJA's PANEL          │  912px
│      [cyan #00E5FF border]  │
│      Name pill: "NINJA"     │
│                             │
+──── 40px gap (call timer) ──+
│                             │
│      GLITCH's PANEL         │  912px
│      [magenta #FF2D95]      │
│      Name pill: "GLITCH"    │
│                             │
+─────────────────────────────+
│  CALL CONTROLS BAR          │  24px
+─────────────────────────────+
```

Each panel: **1080x912** (~6:5 ratio). Kling renders at 1:1 (1080x1080), FFmpeg crops to 1080x912.

### Overlay Variants
- `videochat_overlay_neutral.png` — both panels equal (intros, transitions)
- `videochat_overlay_ninja.png` — Ninja active (thicker cyan border, Glitch dimmed)
- `videochat_overlay_glitch.png` — Glitch active (thicker magenta border, Ninja dimmed)

---

## FFmpeg Pipeline

```bash
ffmpeg -y \
  -i ninja.mp4 -i glitch.mp4 -i videochat_overlay_ninja.png \
  -filter_complex \
    "[0:v]scale=1080:912:force_original_aspect_ratio=increase,crop=1080:912[top]; \
     [1:v]scale=1080:912:force_original_aspect_ratio=increase,crop=1080:912[bot]; \
     [top][bot]vstack=inputs=2,pad=1080:1920:0:32:color=0x0D1117[bg]; \
     [bg][2:v]overlay=0:0:format=auto[v]" \
  -map "[v]" -map 0:a -c:v libx264 -crf 18 -shortest output.mp4
```

**Complexity comparison:**
- News desk: ~100 lines of `geq` alpha gradient feathering
- Video chat: **8 lines of vstack + overlay**

---

## Character References

| Character | Reference Image | Background Vibe |
|-----------|----------------|-----------------|
| Ninja | `assets/overlays/videochat_ref_ninja.png` | Dark gaming cave, cyan LEDs, monitors |
| Glitch | `assets/overlays/Glitch_Facetime_Design.png` | Pink neon hacker den, circuit boards |

- Ninja ref: Generated via Nano Banana Pro from `IMG_2411.jpeg` (new desk presenter design)
- Glitch ref: User-designed, provided directly
- Color temperature contrast sells the "different cameras" illusion (Ninja cool/blue, Glitch warm/pink)

---

## Cost Analysis

| Format | Speaker Cost | Listener Cost | Total/sec | 60s Short |
|--------|-------------|---------------|-----------|-----------|
| Newsdesk (both Pro) | $0.115/s | $0.115/s | $0.230/s | $13.80 |
| **Videochat** | **$0.115/s** | **$0.056/s** | **$0.171/s** | **$10.26** |

**25% cheaper** than newsdesk format — listener on Standard saves money AND produces better results (less expressiveness = less ghost mouthing risk).

---

## Production Pipeline

```
python3 ninja_dual_anchor.py --script-file dialogue.txt --format videochat
```

Pipeline flow:
1. Parse NINJA:/GLITCH: dialogue turns
2. Per turn: TTS (ElevenLabs v3) → generate 60Hz tone (same duration)
3. Upload both refs + audio to fal.ai
4. Parallel Kling: speaker (Pro + TTS) || listener (Standard + 60Hz)
5. Download renders → scale/crop to 1080x912 → vstack → overlay
6. Concat all turns → final video

Fallback: `--format newsdesk` for legacy side-by-side format.

---

## Key Scripts

| Script | Purpose |
|--------|---------|
| `scripts/ninja_dual_anchor.py` | Production pipeline (supports `--format videochat`) |
| `scripts/generate_videochat_overlay.py` | Generate UI overlay PNGs (`--all` for 3 variants) |
| `scripts/generate_videochat_refs.py` | Generate webcam-style character refs via Nano Banana Pro |
| `scripts/test_videochat_render.py` | Quick single-turn test (used during development) |

---

## Advantages Over News Desk

1. **No seam/split line** — panels are separated by design (the gap IS the UI)
2. **No lighting matching** — different rooms, different color temps is expected
3. **No paint-over masking** — each character rendered independently
4. **Simpler FFmpeg** — 8 lines vs 100+ lines
5. **25% cheaper** — listener on Standard tier
6. **Scalable** — adding a third character = just vstack 3 panels
7. **Platform-native** — viewers instantly understand video call aesthetic
8. **Better for mobile** — each face gets ~2.5" on phone vs shared frame

## Limitations

- Less "broadcast authority" than news desk — trades gravitas for relatability
- Each character gets ~48% of frame height vs full frame in single-avatar
- If expanding to 16:9 long-form, may want to keep newsdesk for landscape

## ElevenLabs v3 Audio Tags — What Works & What Doesn't (Feb 25, 2026)

Learned from duo intro v3 render ($16.64 wasted on desync):

### SAFE tags (change tone, don't inflate duration):
- `[sarcastic]` — great for banter, no timing impact
- `[rushed]` — speeds up delivery naturally, keeps lip sync clean

### DANGEROUS tags (add dead time, inflate duration):
- `[laughs]`, `[sighs]`, `[gasps]` — inject vocal reactions that add 0.5-2s per use
- `[deliberate]`, `[slows down]` — stretch delivery, pushes past target duration
- `[frustrated]` — can add sighs/pauses that inflate timing

### NEVER use with Kling Avatar:
- **`speed` parameter** — causes lip sync desync. Kling renders mouth movement to the audio's natural timing. Speeding up playback after the fact means lips fall behind. This wasted an entire render.
- **`style` parameter** — untested with Kling, use with caution

### Duration impact example (same script, same word count):
| Version | Tags Used | Duration | Result |
|---------|-----------|----------|--------|
| v2 | None | 69s | Clean lip sync |
| v3 | [laughs][sighs][deliberate][sarcastic][rushed] + speed:1.1 | 97s | Lip sync desynced, 37% longer |

### Recommended v3 settings for Kling pipeline:
```python
"expressive": {"stability": 0.0, "similarity_boost": 0.75}  # No speed, no style
```
Use `[sarcastic]` and `[rushed]` in-text only. Let punctuation (CAPS, ellipses, !) drive the rest.

---

## Pacing & Assembly Tips (Feb 25, 2026)

- **0.5s TTS padding** stacks up across turns — trim head/tail silence from each clip before concat
- Trimming saved ~1s per turn (8.7s total across 9 turns in testing)
- **Crossfades** between turns would further improve flow (not yet implemented)
- fal.ai queue times (150-350s) do NOT affect render quality — only wall clock time
- **Temp file cleanup:** `/tmp/ninja_dual_*` dirs get cleaned between sessions. Always save final output to `~/output/` immediately. For long renders, consider backing up intermediate clips.
- **Split long scripts:** Renders with 14+ turns risk session timeout. Split into batches of 7-9 turns, render separately, concat manually.

---

## Tips & Best Practices

- **Always use the 60Hz tone** — never pure silence for the listener
- **Standard tier for listener** — Pro is overkill and increases mouth activity risk
- **CFG 0.9 for listener** — enforce the closed-mouth prompt strictly
- **Ninja always top, Glitch always bottom** — consistent positioning helps viewers track who's speaking
- **Active speaker overlay** — switch overlay variant per turn for the border highlight cue
- **Audio-only test first** — always generate TTS and listen before committing to a full Kling render to avoid wasting fal.ai tokens
