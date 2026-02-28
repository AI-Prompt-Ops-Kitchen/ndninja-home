---
name: remotion-explainer-videos
domain: Video/Production
level: 3-tomoe
description: End-to-end workflow for producing instructional explainer videos from existing documents. Document → narration script → per-section TTS → Remotion animated composition → two renders (clean + music). Validated on Copilot for M365 reference card (Feb 28, 2026).
sources:
  - type: codebase
    title: "CopilotExplainer composition"
    url: "file:///home/ndninja/projects/remotion-video/src/CopilotExplainer.tsx"
    date: "2026-02-28"
    confidence: high
  - type: codebase
    title: "Per-section TTS generation script"
    url: "file:///home/ndninja/scripts/copilot_tts_gen.py"
    date: "2026-02-28"
    confidence: high
  - type: codebase
    title: "Narration script"
    url: "file:///home/ndninja/output/copilot_narration_script.txt"
    date: "2026-02-28"
    confidence: high
  - type: related-scroll
    title: "Remotion — Programmatic Video with React"
    url: "file:///home/ndninja/.sharingan/scrolls/remotion-video-code.md"
    date: "2026-02-28"
    confidence: high
  - type: related-scroll
    title: "AI Document Production"
    url: "file:///home/ndninja/.sharingan/scrolls/ai-document-production.md"
    date: "2026-02-28"
    confidence: high
  - type: related-scroll
    title: "ElevenLabs Audio Platform"
    url: "file:///home/ndninja/.sharingan/scrolls/elevenlabs-audio-platform.md"
    date: "2026-02-28"
    confidence: high
last_updated: 2026-02-28
sources_count: 6
can_do_from_cli: true
---

# Remotion Explainer Videos — Document-to-Video Pipeline

## Mental Model

Turn any structured document (reference card, training guide, SOP, slide deck) into an animated instructional video with professional narration. The pipeline:

```
Document → Narration Script → Per-Section TTS → Remotion Composition → Two Renders
                                                                        ├── Clean (narration only)
                                                                        └── Music (narration + background)
```

This is the **video companion** to the AI Document Production workflow. Same illustrations, same structure, different medium. One source document produces HTML + PDF + Video.

---

## The Pipeline (7 Steps)

### Step 1: Write the Narration Script

Convert document sections into spoken narration. Save to `output/<project>_narration_script.txt` for review before spending on TTS.

**Rules for narration writing:**
- **Conversational but professional** — this is workplace training, not YouTube energy
- **~150 words per minute** at calm speaking pace (use this for duration estimates)
- **No visual references** like "as you can see" — audio must stand alone
- **Transition phrases** between sections ("So where do you actually use this?", "Here's a technique that...")
- **Example prompts read verbatim** in quotes — listeners need to hear the exact phrasing
- **Each section is self-contained** — generates as separate TTS segment

**Timing estimation:**

| Target Duration | Word Count | Sections |
|----------------|------------|----------|
| 2 minutes | ~300 words | 3-4 sections |
| 4-5 minutes | ~600-750 words | 6-8 sections |
| 8-10 minutes | ~1200-1500 words | 10-12 sections |

### Step 2: Generate Per-Section TTS

Generate **one MP3 per section** (not one giant file). Per-section gives:
- Precise timing control in Remotion (each section's exact duration is known)
- Ability to re-generate a single section without re-doing the whole video
- Natural gaps between sections (0.5s silence via Sequence spacing)

**Script pattern** (reuse `copilot_tts_gen.py` as template):

```python
from ninja_content import generate_tts, get_audio_duration

SECTIONS = {
    "title": "...",
    "section1": "...",
    # ...
    "outro": "...",
}

durations = {}
for name, text in SECTIONS.items():
    output_path = f"{OUTPUT_DIR}/{project}_{name}.mp3"
    generate_tts(text, output_path, voice_id=VOICE_ID,
                 pad_start=0.3, voice_style="calm")
    durations[name] = get_audio_duration(output_path)

# Write timing manifest
with open(f"{OUTPUT_DIR}/{project}_timing.json", "w") as f:
    json.dump(durations, f, indent=2)
```

**Voice style selection:**

| Content Type | Style | Stability | Why |
|-------------|-------|-----------|-----|
| Workplace training | `"calm"` | 1.0 | Steady, professional, no surprises |
| Product demo | `"natural"` | 0.5 | Balanced energy |
| YouTube content | `"expressive"` | 0.0 | High energy, emotional range |

**The timing manifest is critical** — it's the source of truth for frame calculations in the Remotion composition. Save it to `public/` alongside the MP3s.

**Cost:** ElevenLabs v3 at ~$0.15 per 1,000 characters. A 4.5-minute video (~4,600 chars) costs ~$0.65.

### Step 3: Copy Assets to Remotion Public Folder

Everything Remotion needs must be in `projects/remotion-video/public/`:

```
public/
├── {project}_title.mp3          # TTS segments
├── {project}_section1.mp3
├── {project}_section2.mp3
├── ...
├── {project}_outro.mp3
├── {project}_timing.json        # Duration manifest
├── nb2_section1_*.png           # Illustrations
├── nb2_section2_*.png
├── ...
└── background_music.mp3         # Optional Suno track
```

Remotion accesses these via `staticFile("filename.mp3")`.

### Step 4: Build the Remotion Composition

Create `src/{ProjectName}Explainer.tsx`. Key architecture:

**Frame math from timing manifest:**
```tsx
const FPS = 30;
const sec = (s: number) => Math.round(s * FPS);
const GAP = 0.5; // seconds between sections

// Cumulative start times
const START = {
  title: 0,
  section1: DUR.title + GAP,
  section2: DUR.title + GAP + DUR.section1 + GAP,
  // ...
};
```

**Component hierarchy:**
```
CopilotExplainer (main)
├── Audio layers (per-section Sequences)
├── Optional background music Audio
├── TitleCard (Sequence)
├── SectionScene × N (Sequences)
│   ├── SectionBadge (spring-animated number circle)
│   ├── FadeIn title
│   ├── FadeIn illustration (Img + staticFile)
│   ├── ExampleCard × N (staggered slide-in)
│   ├── Bullet points (staggered fade-in)
│   └── CalloutBox (delayed fade-in at ~55% through section)
└── OutroCard (Sequence)
```

**Animation timing rules:**
- Section badge: spring at frame 0 (instant pop)
- Title: fade in at frame 5
- Illustration: fade in at frame 15
- Bullets/cards: stagger at 15-18 frame intervals starting at frame 30
- Callout boxes: appear at ~55% through the section duration
- Section fade-out: last 20 frames

**Visual design (corporate/training style):**
- 1920×1080 (16:9 landscape) — standard for training content
- Light background (white/off-white), NOT dark theme
- Color-coded sections matching source document palette
- Left column: illustration (460px). Right column: text content
- Bottom accent bar in section color (4px)
- Segoe UI font family (matches Microsoft branding)

**Two-version pattern:**
```tsx
export interface ExplainerProps {
  withMusic: boolean;
}

// Background music at 12% volume — audible but doesn't compete with narration
{withMusic && (
  <Audio src={staticFile("background_music.mp3")} volume={0.12} />
)}
```

### Step 5: Register in Root.tsx

Register both clean and music versions as separate compositions:

```tsx
<Composition
  id="ProjectExplainer"
  component={ProjectExplainer}
  durationInFrames={TOTAL_FRAMES}
  fps={30}
  width={1920}
  height={1080}
  defaultProps={{ withMusic: false }}
/>
<Composition
  id="ProjectExplainerMusic"
  component={ProjectExplainer}
  durationInFrames={TOTAL_FRAMES}
  fps={30}
  width={1920}
  height={1080}
  defaultProps={{ withMusic: true }}
/>
```

### Step 6: Preview and Render

```bash
# Preview in Remotion Studio (scrub timeline, check sync)
npm run dev

# Verify compositions registered
npx remotion compositions src/index.ts

# Render both versions
npx remotion render src/index.ts ProjectExplainer out/project_clean.mp4
npx remotion render src/index.ts ProjectExplainerMusic out/project_music.mp4
```

**Render time reference:** 8,574 frames (4m 46s video) renders in ~3 minutes locally.

### Step 7: Deliver and Review

Send to Vengeance (or preview server) for review. Extract key frames for visual QA:

```bash
# Extract 1 frame per section for quick visual review
ffmpeg -i video.mp4 -vf "select='eq(n\,0)+eq(n\,90)+eq(n\,300)...'" -vsync vfr frames/frame_%03d.png
```

---

## Reusable Components Library

These components from CopilotExplainer.tsx are generic and reusable:

| Component | Purpose | Reuse Pattern |
|-----------|---------|---------------|
| `FadeIn` | Fade + slide up with configurable delay/duration | Any text or element entrance |
| `SectionBadge` | Spring-animated numbered circle | Any numbered section |
| `ExampleCard` | Slide-in card with colored left border | Any prompt/example display |
| `CalloutBox` | Bordered info box with title | Tips, warnings, notes |
| `SectionScene` | Full section layout (image left, content right) | Any document section |
| `TitleCard` | Centered title on gradient background | Any video title |
| `OutroCard` | Closing message with footer | Any video ending |

**Future improvement:** Extract these into a shared `src/components/` library so new explainer compositions import them directly.

---

## Cost Reference

| Component | Cost | Notes |
|-----------|------|-------|
| ElevenLabs TTS (4.5 min) | ~$0.65 | ~4,600 chars at v3 pricing |
| NB2 illustrations (6 images) | ~$0.30 | If generating new; $0 if reusing from document |
| Suno background music | $0 | User subscription |
| Remotion rendering | $0 | Local render, no cloud |
| **Total (new illustrations)** | **~$0.95** | |
| **Total (reusing document images)** | **~$0.65** | |

---

## Adaptation Guide

To create a new explainer from a different document:

1. **Copy the pattern:** Duplicate `copilot_tts_gen.py` → change `SECTIONS` dict
2. **Match the palette:** Update color constants in the composition to match the source document
3. **Adjust section count:** Add/remove entries in the `SECTIONS` array
4. **Swap illustrations:** Copy new images to `public/`, update `image` field in section data
5. **Re-render:** Both versions auto-update via the timing manifest

**What changes per project:** Section text, colors, images, section count
**What stays the same:** Component library, animation patterns, render pipeline, two-version pattern

---

## Validated: Copilot for M365 Explainer (Feb 28, 2026)

- **Source:** `output/copilot_reference_card.html` (6-section reference card)
- **Output:** Two 4m 46s MP4s (clean + music), 16 MB each
- **Composition:** `CopilotExplainer.tsx` — 460 lines, 6 animated sections
- **TTS:** 8 segments (title + 6 sections + outro) via ElevenLabs v3 calm style
- **Illustrations:** 6 NB2 images reused from the PDF (zero additional image cost)
- **Total cost:** ~$0.65 (TTS only)
- **Render time:** ~3 minutes per version locally
- **Visual QA:** All sections render correctly, color coding matches PDF, text readable, animations smooth
- **Minor issues noted:** Frame 0 is white (fade-in delay), paperclip emoji renders as square (use text instead of emoji), bottom half of section slides has empty space (content clusters in top third)

---

## Limitations

- **Not for complex animations:** This pattern is for section-by-section reveals with text + images. For cinematic motion graphics, custom animation is needed.
- **Audio sync is approximate:** TTS duration drives section timing, but individual words aren't synced to specific visual elements. Good enough for training content.
- **Font rendering:** Remotion uses Chrome's font stack. Custom fonts need to be loaded explicitly. System fonts (Segoe UI, Arial) work out of the box.
- **Emoji rendering:** Some emojis don't render in Remotion's headless Chrome. Use text descriptions instead.
- **Music length:** If background music is shorter than the video, it stops. For longer videos, use a looping track or generate a longer Suno piece.

---

## Related Scrolls

- `remotion-video-code` — Framework fundamentals, Kie.ai integration, command reference
- `ai-document-production` — Document → HTML → PDF pipeline (produces the source material)
- `elevenlabs-audio-platform` — TTS voice settings, v3 model details, expressive tags
- `nano-banana-pro` — NB2 image generation for illustrations
