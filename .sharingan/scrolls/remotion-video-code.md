---
name: remotion-video-code
domain: Video/Code
level: 2-tomoe
description: React framework for creating videos programmatically. Claude Code + Remotion skill generates motion graphics, product demos, and full videos from prompts. Kie.ai provides cheap TTS/media APIs.
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
last_updated: 2026-02-18
can_do_from_cli: true
---

# Remotion — Programmatic Video with React + Claude Code

## Mental Model

Remotion turns React components into video. You write JSX that reads the current frame number, animate properties based on that frame, and Remotion renders each frame via headless Chrome + FFmpeg into an MP4. Think of it as "a video is a function of frames." Claude Code + the Remotion skill can generate entire video projects from natural language prompts.

**Not a replacement for avatar videos** — Remotion is for motion graphics, text animations, product demos, presentations, and data-driven video. It sits *alongside* avatar pipelines (Kling/fal.ai), not instead of them.

## Prerequisites

| Requirement | Details |
|---|---|
| Node.js | Required — install from nodejs.org |
| Claude Code | Desktop app, set to "code" mode, Opus 4.6 recommended |
| Remotion skill | Installed via `npx skills add remotion-dev/skills` |
| Kie.ai API key (optional) | For TTS voiceover + media generation |
| FFmpeg | Usually bundled, but needed for rendering |

## Key Concepts

| Concept | What It Is |
|---|---|
| **Composition** | React component bound to video metadata (width, height, fps, durationInFrames). Registered in `src/Root.tsx`. |
| **useCurrentFrame()** | Hook returning the integer frame number (0-indexed). Core of all animation. |
| **useVideoConfig()** | Hook returning width, height, fps, durationInFrames. |
| **Sequence** | Component that offsets the start time of children — compose timed elements without manual frame math. |
| **interpolate()** | Maps frame ranges to value ranges. `interpolate(frame, [0, 30], [0, 1])` = fade in over 30 frames. |
| **spring()** | Physics-based spring animation helper tied to frame number. |
| **AbsoluteFill** | A `<div>` that fills the entire canvas. Layout primitive. |
| **Remotion Studio** | Local dev server with timeline preview, frame scrubber, composition list. |
| **Remotion Player** | In-browser component for previewing without rendering. |

## Core Workflows

### Workflow 1: Setup — Install Remotion Skill in Claude Code

**When to use:** First time setup.

1. Open Claude Code desktop → toggle to "code" mode → set model to Opus 4.6
2. Create a project folder (e.g., `~/claude-video/`)
3. Prompt Claude: "Add the Remotion skill and update the CLAUDE.md so video generation uses this skill"
4. During setup, select **Blank** template when prompted
5. Claude installs Remotion, creates project structure, updates CLAUDE.md

**Alternative CLI setup:**
```bash
npx create-video@latest    # Scaffold new project (pick Blank + TailwindCSS + Skills)
npx skills add remotion-dev/skills   # Add Remotion skill to Claude Code
```

**Gotchas:**
- Always pick "Blank" template — gives Claude maximum creative freedom.
- The skill file goes into `.claude/skills/` — it gives Claude context on Remotion idioms so it writes correct animation patterns.

### Workflow 2: Create a Design System from Existing Brand

**When to use:** You want videos to match a website or brand aesthetic.

1. Prompt Claude Code: "Review [website URL] and create a design system. Update CLAUDE.md for future reference."
2. If prompted, authorize Claude for Chrome extension (speeds up website review)
3. Claude generates a `brand-guidelines` section in CLAUDE.md with colors, typography, identity rules
4. All future video generation will follow this design system

**Gotchas:**
- Do this BEFORE generating videos — it's the design source of truth.
- Claude Code stores the design system in CLAUDE.md so it persists across sessions.

### Workflow 3: Generate a Video from Prompt

**When to use:** You want to create a motion graphics video.

1. Prompt: "Create a 10-20 second video about [topic] using the exact style from the website design system"
2. Claude writes React components with animations tied to frame numbers
3. Preview opens in browser via Remotion Studio
4. Iterate with natural language ("change the background color", "make the text bigger")

**Gotchas:**
- First render has no audio — voiceover is added in Workflow 4.
- Videos render to the browser for preview; MP4 export is a separate step.

### Workflow 4: Add Voiceover via Kie.ai + ElevenLabs

**When to use:** You want TTS narration synced to the video.

**Setup (one-time):**
1. Get API key from [kie.ai](https://kie.ai) → API Keys → Create New
2. Add to Claude Code: paste the Kie.ai/voiceover config into CLAUDE.md (or prompt Claude to set up Kie.ai with ElevenLabs)
3. Set `KIE_API_KEY` environment variable

**Generate voiceover:**
1. Prompt: "Add a male voiceover to the video. Ensure words align with components as they render."
2. Claude calls Kie.ai → ElevenLabs TTS → generates audio → writes `<Audio>` component synced to frames
3. Preview with audio in browser

**Gotchas:**
- "Ensure words align with components as they render" is the critical prompt phrase — tells Claude to sync timing.
- Kie.ai TTS is ~5x cheaper than ElevenLabs direct ($0.03/1K chars via Turbo v2.5 vs $0.30/1K direct).

### Workflow 5: Stitch Multiple Clips + Export MP4

**When to use:** Joining clips into a final video.

1. Generate multiple clips as separate compositions
2. Prompt: "Combine video 1, video 2, etc. into one video and render it as MP4"
3. Claude stitches compositions using `<Sequence>` components
4. Renders to MP4 via FFmpeg

### Workflow 6: Edit by Frame Reference

**When to use:** Tweaking specific parts of a generated video.

1. Preview the video, note the frame numbers from the scrubber
2. Prompt: "In the combined video, from frame 0 to 80, change 'for business owners' to 'for creators'"
3. Claude modifies the component at those frames

**Gotchas:**
- Frame numbers are your editing language — scrub to find the right range.
- If the preview server stops, prompt "restart the server" — this happens sometimes.

## Command Reference

| Action | Command | Notes |
|---|---|---|
| Create project | `npx create-video@latest` | Pick Blank + TailwindCSS + Skills |
| Add Remotion skill | `npx skills add remotion-dev/skills` | For Claude Code context |
| Launch Studio | `npm run dev` or `npx remotion studio` | Preview server with timeline |
| Render MP4 | `npx remotion render src/index.ts CompositionId out.mp4` | Local render |
| Render specific frames | `npx remotion render ... --frames 0-29` | Frame range |
| Set quality | `npx remotion render ... --crf 18` | Lower = better quality |
| List compositions | `npx remotion compositions` | See all registered videos |
| Cloud render | `npx remotion lambda render ...` | AWS Lambda (parallelized) |
| Upgrade | `npx remotion upgrade` | Update all Remotion packages |

## Kie.ai Quick Reference

| Feature | Details |
|---|---|
| **What** | AI API aggregator — single API key for TTS, image, video, music |
| **Pricing** | Pay-as-you-go, 1 credit = $0.005 USD |
| **TTS models** | ElevenLabs Turbo v2.5 (cheap), Multilingual V2, Flash, V3 |
| **Other APIs** | Veo 3.1, Nano Banana Pro, Suno music, Runway |
| **Auth** | `Authorization: Bearer <KIE_API_KEY>` |
| **Async** | POST job → get `task_id` → poll for result |
| **Docs** | [docs.kie.ai](https://docs.kie.ai) |

## MCP Integration (Advanced)

**remotion-media-mcp** — community MCP server that gives Claude Code direct media generation tools:

```
Claude Code → remotion-media-mcp → Kie.ai API → ElevenLabs/Suno/Veo/Nano Banana
                                                → files saved to public/ folder
                                                → referenced in Remotion compositions
```

Tools provided: `generate_speech`, `generate_sound_effect`, `generate_music`, `generate_image`, `generate_video_from_text`, `generate_video_from_image`, `list_media`

GitHub: [stephengpope/remotion-media-mcp](https://github.com/stephengpope/remotion-media-mcp)

## Integration with Ninja Toolkit

- **Content pipeline:** Use Remotion for intros/outros, lower thirds, title cards, animated stats — things that don't need avatar. Combine with Kling avatar clips in FFmpeg.
- **Thumbnail pipeline:** Kie.ai includes Nano Banana Pro (which we already use for thumbnails) at potentially lower rates.
- **TTS cost savings:** Kie.ai ElevenLabs proxy is ~5x cheaper than direct. Could replace our current ElevenLabs API key for TTS in the content pipeline.
- **Shorts pipeline:** Generate 60-second motion graphic shorts entirely from prompts — no avatar needed for some topics.
- **Glitch:** Could generate animated explainer segments for Glitch's responses.
- **Long-form videos:** B-roll motion graphics segments between avatar talking-head clips.

## Limitations & Gaps

- **Not for avatar/talking head videos:** Remotion generates motion graphics, not AI avatar lip-sync. It complements Kling, doesn't replace it.
- **React knowledge helpful:** While Claude Code writes the code, understanding React helps when debugging or making advanced customizations.
- **Rendering time:** Local rendering uses CPU/GPU via headless Chrome — large videos can be slow. Lambda rendering (AWS) parallelizes but adds cost/complexity.
- **Kie.ai reliability:** Third-party API proxy — if kie.ai goes down, your TTS/media pipeline breaks. Consider keeping direct ElevenLabs key as backup.
- **Licensing:** Free for individuals and companies ≤3 employees. Companies with 4+ employees need a paid license (price not public).
- **Preview server quirk:** Sometimes stops during editing — just prompt Claude to restart it. [CONFIRMED in video]
- **remotion-media-mcp:** Community project, not official Remotion — may lag behind API changes.

## Tips & Best Practices

1. **Design system first:** Always create a brand design system in CLAUDE.md before generating videos — consistency is key.
2. **Frame-based editing:** Reference frame numbers when requesting changes — it's the most precise way to communicate edits.
3. **Blank template:** Always start with Blank — gives Claude maximum flexibility.
4. **Sync voiceover:** Include "ensure words align with components as they render" in your TTS prompt.
5. **Kie.ai over direct APIs:** ~5x cheaper for ElevenLabs TTS. Use direct API keys as fallback only.
6. **Opus 4.6:** The video quality and code quality are significantly better on Opus 4.6 vs older models.
7. **Stitch last:** Generate individual clips first, review each, then stitch. Easier to iterate on parts.
8. **Export MP4 explicitly:** Preview is browser-only — you need to explicitly prompt for MP4 render when done.
