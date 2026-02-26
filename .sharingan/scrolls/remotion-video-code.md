```markdown
---
name: remotion-video-code
domain: Video/Code
level: 3-tomoe
description: React framework for creating videos programmatically with agentic AI. Claude Code + Remotion skill generates motion graphics, product demos, and full videos from natural language prompts. Professional-grade animations achievable in 5-10 iterative prompts. Kie.ai provides cheap TTS/media APIs. Nine-phase workflow validated for enterprise content.
sources:
  - type: youtube
    title: "Claude Code Just Changed Content Creation FOREVER (Tutorial)"
    url: "https://youtu.be/nYO9T4j0pCM"
    channel: "Online Ninja"
    date: "2026-02"
    confidence: medium
  - type: docs
    title: "Remotion Official Documentation"
    url: "https://remotion.dev/docs"
    date: "2026-02"
    confidence: high
  - type: docs
    title: "Remotion Claude Code Integration Guide"
    url: "https://remotion.dev/docs/ai/claude-code"
    date: "2026-02"
    confidence: high
  - type: github
    title: "remotion-media-mcp — MCP server for Kie.ai media generation"
    url: "https://github.com/stephengpope/remotion-media-mcp"
    date: "2026-02"
    confidence: medium
  - type: docs
    title: "Kie.ai API Documentation"
    url: "https://docs.kie.ai"
    date: "2026-02"
    confidence: high
  - type: youtube
    title: "How I Created a Professional Motion Graphics Video With Claude Code + Remotion Skills (No Editing)"
    url: "https://www.youtube.com/watch?v=xAUifztpib8"
    channel: "Andy Lo"
    date: "2026-02"
    confidence: high
  - type: youtube
    title: "Claude Code can now make videos, here's how"
    url: "https://www.youtube.com/watch?v=fOY0_WCR3eY"
    channel: "David Ondrej"
    date: "2026-02"
    confidence: high
  - type: youtube
    title: "Vibecreating Videos JUST became a Reality (Claude Code x Remotion tutorial for non-coders)"
    url: "https://www.youtube.com/watch?v=7J0ru0g3RUw"
    channel: "RoboNuggets"
    date: "2026-02"
    confidence: high
last_updated: 2026-02-22
can_do_from_cli: true
sources_count: 8
---

# Remotion — Programmatic Video with React + Claude Code [3-tomoe]

## Mental Model

Remotion turns React components into video. You write JSX that reads the current frame number, animate properties based on that frame, and Remotion renders each frame via headless Chrome + FFmpeg into an MP4. Think of it as "a video is a function of frames."

**The agentic shift:** Claude Code + the Remotion skill can generate entire video projects from natural language. Claude now understands Remotion's framework at an expert level — it handles composition structure, animation choreography, timing functions, and asset management automatically. This transforms Remotion from a developer tool into a creative tool accessible to non-coders.

**Not a replacement for avatar videos** — Remotion is for motion graphics, text animations, product demos, presentations, and data-driven video. It pairs *alongside* avatar pipelines (Kling/fal.ai), not instead of them.

## The Nine-Phase Workflow (Validated)

**Phases 1–3: Foundation & Direction**
- **Phase 1 (Technical Foundation):** Establish project rules, constraints, and patterns Claude must follow throughout development. Prevents AI from inventing inconsistent behaviors.
- **Phase 2 (Art Direction & Design System):** Define visual tone, motion principles, typography, color, and creative guardrails. This is where consistency lives—not pixel-level control, but "shared visual language" between you and Claude.
- **Phase 3 (Story & Timing):** Break the video into scenes with explicit roles, flow, and frame durations. Before any animation code is written, you have a scene-by-scene breakdown.

**Phases 4–7: Asset & Component Build**
- Create reusable components (intros, transitions, data visualizations, text layers).
- Source/generate assets (images, audio, data).
- Build modular, composable pieces instead of monolithic videos.

**Phases 8–9: Assembly & Iteration**
- Stitch components using `<Sequence>` components.
- Iterate using frame references ("change the text from frame 80 to 150").
- Render to MP4.

**Pro insight:** This workflow feels like "project planning" because it is. Claude works better with explicit systems. The difference between mediocre and professional animations is whether you define the rules upfront.

## Prerequisites

| Requirement | Details |
|---|---|
| Node.js | Required — install from nodejs.org |
| Claude Code | Desktop app (VS Code extension) or web, Opus 4.6 minimum |
| Remotion skill | Installed via `npx skills add remotion-dev/skills` |
| Kie.ai API key (optional) | For TTS voiceover + media generation |
| FFmpeg | Usually bundled, but required for rendering |
| Claude Pro subscription | Required for Claude Code agent mode |

## Best Practices for 3-Tomoe Results

### 1. Design System First, Code Second
**Pattern:** Always execute Phase 2 before generating video code.
- Create a `brand-guidelines` or `art-direction.md` in your project.
- Document colors, typography, motion principles, tone.
- Claude references this for every component it generates.
- Result: Consistent visuals without micromanagement.

### 2. Iterative Prompting (5–10 Rounds)
**Pattern:** Don't one-shot videos. Treat it like reviewing animatic cuts.
1. Generate initial version.
2. Preview in browser.
3. Critique one specific element (frame range + change).
4. Claude updates.
5. Repeat 3–4 times per video.

**Why this works:** Claude's output quality improves with feedback context. Early iterations are 70% right; by round 5–7, they're 95%.

### 3. Modular Components Over Monolithic Videos
**Pattern:** Build reusable pieces.
```tsx
// Good: Reusable across videos
<BenchmarkChart data={benchmarks} />
<AnimatedStats numbers={[1, 2, 3]} />
<TextReveal text="Hello" />

// Bad: Single-use, hard to iterate
// Entire 60-second video in one component
```

### 4. Frame References for Editing
When requesting changes, be specific:
- ❌ "Make the intro faster"
- ✅ "In the combined video, frames 0–40 are the intro. Speed it up so it ends by frame 30."

Frame numbers are your editing language—scrub the preview to find them.

### 5. High-Quality Assets = Better Output
Provide Claude with:
- Brand logos (PNG, no background)
- Product screenshots (high res)
- Color hex codes
- Font names (web-safe preferred)
- Data/CSVs (for charts)

**Why:** Claude can't improve asset quality, only composition quality. Bad assets → bad video. Good assets → Claude's layout choices shine.

### 6. Opus 4.6 Only
Model quality matters.
- Opus 4.6: Expert-level composition, correct React patterns, fewer bugs.
- Older models: Visual confusion, animation timing issues, broken code.

### 7. Sync Voiceover Explicitly
Critical prompt phrase for TTS integration:
> "Add a male voiceover synced to the video. Ensure words align with components as they appear on screen."

This tells Claude to calculate frame-to-word timing, not just concatenate audio.

## Key Concepts (Expanded)

| Concept | Details |
|---|---|
| **Composition** | React component bound to video metadata (width, height, fps, durationInFrames). Registered in `src/Root.tsx`. Entry point for rendering. |
| **useCurrentFrame()** | Hook returning the integer frame number (0-indexed). The foundation of all animation logic. |
| **Sequence** | Component that offsets the start time of children. Think "timeline track." Compose timed elements without manual frame math. `<Sequence from={80}>` starts at frame 80. |
| **interpolate()** | Maps frame ranges to value ranges. `interpolate(frame, [0, 30], [0, 1])` = fade in over 30 frames. Linear by default. |
| **spring()** | Physics-based spring animation. Gives motion weight & realism. Tied to frame number, not duration. Config: `{damping, stiffness, mass}`. |
| **AbsoluteFill** | A `<div>` that fills the canvas. Layout primitive for full-screen backgrounds. |
| **Remotion Studio** | Local dev server (http://localhost:3000). Timeline preview, frame scrubber, composition selector. The canvas for iteration. |
| **Remotion Player** | In-browser component for embedding previews without rendering. Useful for client review. |
| **Agent Skills** | Instruction files (open standard) that teach AI agents how to use tools. Remotion skill contains API patterns, component conventions, best practices. Progressive disclosure—Claude only loads what's relevant. |

## Workflow Reference

### Setup: Install Remotion Skill in Claude Code
```bash
npx create-video@latest          # Blank template + TailwindCSS + Skills
npx skills add remotion-dev/skills  # Installs Remotion skill
npm run dev                        # Launches Remotion Studio
```

### Create a Video from Prompt
**Phase 1 prompt:**
```
[Your Phase 1 prompt establishing technical rules, naming conventions, project structure expectations]
```
Copy from build guide → paste into Claude Code → let Claude generate dev.md.

**Phase 2 prompt:**
```
[Your Phase 2 prompt defining visual tone, motion principles, design constraints]
```
Claude generates art-direction.md.

**Phase 3 prompt:**
```
[Your Phase 3 prompt breaking down scenes, timing, structure]
```
Claude generates scene-breakdown.md.

**Phase 4–7:** Ask Claude to "Create components for [scene name]" referencing the art direction & scene breakdown.

**Phase 8–9:** "Combine all components into one video using Sequence. Render to MP4."

## Integration with Content Pipelines

**Benchmark Videos:** Animated bar charts render in ~4 seconds locally (zero API cost). Reusable across AI comparison videos. Drop MP4 into broll/ folder.

**Product Demos:** Motion graphics intros/outros + Kling avatar body shots = full demo video. Remotion handles the "clean UI walkthrough" parts.

**Explainer Segments:** Generate 30–60 second motion graphics pieces for long-form videos. Cheaper than paying animators, faster than learning After Effects.

**Shorts Pipeline:** Full 60-second motion graphic shorts from prompts. No avatar needed for visual-first content.

**TTS Cost Savings:** Kie.ai ElevenLabs proxy ~5x cheaper than direct API. Integrate once, use across all videos.

## Agent Skills: The Game-Changer

**What they are:** Instruction manuals (structured JSON/YAML) that teach AI agents tool expertise.

**How Claude uses them:**
1. You prompt Claude with "create a video about..."
2. Claude loads the Remotion skill (progressive disclosure—only relevant parts).
3. Skill contains: API patterns, component conventions, animation best practices, reference docs for 3D/audio/captions.
4. Claude generates expert-level Remotion code.

**Why they matter:** Before skills, Claude generated boilerplate. Now it understands *idiomatic* Remotion—timing functions, reusable patterns, performance trade-offs.

**Open standard:** Not Claude-only. Works with Open Code, Agent Zero, other agentic platforms. This is the infrastructure layer for agentic AI.

## Validated Benchmarks

### Benchmark Chart Animation (Feb 2026)
- **Output:** Animated bar chart, 7s, 600KB, 1080×1920 portrait
- **Render time:** ~4 seconds (local, 8x concurrency)
- **Cost:** Zero (pure React → frames → MP4, no external APIs)
- **Reusability:** Drop MP4 into broll/, use in any AI benchmark video
- **Animation pattern:**
```tsx
const startFrame = 40 + index * 18; // Stagger by 18 frames
const progress = spring({ frame: frame - startFrame, fps, config: { damping: 80, stiffness: 100 } });
const displayed = Math.round(interpolate(progress, [0, 1], [0, targetValue]));
```

### Mars Explainer Video (Andy Lo, Feb 2026)
- **Prompt:** Build from natural language description of Mars facts
- **Iterations:** ~3–5 refinement cycles
- **Result:** Professional explainer with motion, timing, voiceover—zero manual animation
- **Key insight:** Phase 2 art direction locked visual consistency. Phase 3 storyboard locked pacing. Phases 4–9 were execution.

### Product Demo Videos (David Ondrej, Feb 2026)
- **Input:** Website URL + brand colors/fonts
- **Claude process:** Downloaded assets, inferred layout, wrote copy, assembled composition
- **Result:** Professional promo video with no manual editing
- **Feedback loop:** Could request text changes → Claude re-rendered specific frame ranges

## Limitations & Gaps (Updated)

- **❌ Real-time rendering:** Rendering 60fps video requires headless Chrome + FFmpeg. Large videos (5+ min) can be slow locally. Lambda rendering (AWS) parallelizes but adds cost.
- **❌ Complex 3D:** Remotion is 2D-first (Three.js integration exists but less documented). Not for 3D character animation.
- **❌ Kie.ai vendor risk:** Third-party API proxy. If kie.ai goes down, TTS pipeline breaks. Keep direct ElevenLabs key as fallback.
- **✓ Learning curve (partially solved):** Non-coders can now create without learning React, thanks to Claude. But understanding frame-based timing still helps for iteration.
- **✓ Sync precision (improved):** Phase 3 storyboarding + explicit timing prompts make voiceover sync reliable. Earlier versions struggled; now validated.
- **✓ Asset management (improved):** Agent skills guide Claude to structure assets cleanly. Fewer "undefined image" errors.
- **❌ Cloud rendering cost:** Remotion Lambda rendering parallelizes but charges per-minute. Long videos get expensive. Local rendering is free.
- **⚠ Licensing:** Free for individuals and companies ≤3 employees. 4+ employees require paid license (price TBD).

## Tips & Patterns

1. **Build guides as templates:** Create Phase 1–3 prompts once, reuse across projects. Store in a `.prompts/` folder.
2. **Component library:** Save reusable components (CountUp, BarChart, TextReveal) in a `components/` folder. Reference them across videos.
3. **Frame scrubber as workflow:** Preview → scrub to problem frame → note frame number → prompt with frame range → Claude updates.
4. **Stitch last:** Build individual clips/scenes, review each, *then* combine. Easier to iterate on parts than on the whole.
5. **Asset versioning:** Keep a `assets/` folder with versioned images/audio. Claude can reference by path.
6. **Opus 4.6 minimum:** Non-negotiable. It's the only model with robust Agent Skills support.
7. **Kie.ai + direct API fallback:** Use Kie.ai for 95% of TTS (cheap). Keep ElevenLabs API key for mission-critical voiceovers if proxy fails.

## Command Reference

| Action | Command |
|---|---|
| Create project | `npx create-video@latest` |
| Add Remotion skill | `npx skills add remotion-dev/skills` |
| Launch Studio | `npm run dev` |
| Render MP4 | `npx remotion render src/index.ts