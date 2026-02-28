---
name: nano-banana-pro
domain: Image/Character Art
level: 3-tomoe
description: Google's Nano Banana model family (Pro + NB2) — reasoning-driven image generation via generate_content API. JSON structured prompting for consistency. Powers the Ninja thumbnail pipeline, B-roll Ken Burns images, and Dojo Thumbnail Studio.
sources:
  - type: docs
    title: "Nano Banana image generation — Gemini API"
    url: "https://ai.google.dev/gemini-api/docs/image-generation"
    date: "2026-02-27"
    confidence: high
  - type: docs
    title: "Gemini 3 Pro Image Preview — Model Card"
    url: "https://ai.google.dev/gemini-api/docs/models/gemini-3-pro-image-preview"
    date: "2026-02-24"
    confidence: high
  - type: docs
    title: "Google Vertex AI — Generate images with Gemini"
    url: "https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/image-generation"
    date: "2026-02-24"
    confidence: high
  - type: blog
    title: "Nano Banana Pro — Google DeepMind"
    url: "https://deepmind.google/models/gemini-image/pro/"
    date: "2026-02-24"
    confidence: high
  - type: youtube
    title: "Anti-Gravity + Nano Banana 2 Destroys Every AI Image Tool (FREE Skill)"
    url: "https://youtu.be/iTKkoGd3YcM"
    date: "2026-02-27"
    confidence: medium
    notes: "Nate Herk — JSON prompting technique, Kie.ai pricing, skill-based workflow"
  - type: youtube
    title: "Nano Banana 2 + Kling 3.0 = Consistent Characters SOLVED"
    url: "https://youtu.be/2psBexPkw3I"
    date: "2026-02-27"
    confidence: high
    notes: "@taoprompts — 8-shot character reference sheet technique, multi-character scenes, realism keywords, Kling Omni Reference workflow"
  - type: codebase
    title: "ninja_thumbnail.py — thumbnail generation"
    url: "file:///home/ndninja/scripts/ninja_thumbnail.py"
    date: "2026-02-24"
    confidence: high
  - type: codebase
    title: "ninja_broll.py — B-roll Ken Burns images"
    url: "file:///home/ndninja/scripts/ninja_broll.py"
    date: "2026-02-24"
    confidence: high
  - type: codebase
    title: "Dojo Thumbnail Studio"
    url: "file:///home/ndninja/projects/ninja-dashboard/backend/thumbnail_studio.py"
    date: "2026-02-24"
    confidence: high
  - type: third-party
    title: "Nano Banana Pro pricing analysis"
    url: "https://pricepertoken.com/pricing-page/model/google-gemini-3-pro-image-preview"
    date: "2026-02-24"
    confidence: medium
last_updated: 2026-02-28
sources_count: 10
can_do_from_cli: true
---

# Nano Banana — Google Gemini Image Generation Family

## Mental Model

"Nano Banana" is Google's branding for native image generation built into the Gemini model family. Three tiers:

| Codename | Model ID | Based On | Strength |
|----------|----------|----------|----------|
| **Nano Banana** | `gemini-2.5-flash-image` | Gemini 2.5 Flash | Speed, volume, budget |
| **Nano Banana Pro** | `gemini-3-pro-image-preview` | Gemini 3 Pro | Reasoning, precision, complex compositions |
| **Nano Banana 2** | `gemini-3.1-flash-image-preview` | Gemini 3.1 Flash | **New default.** Pro quality at Flash speed, better text, ~40% cheaper |

**NB2 is now the recommended model for most generation tasks.** It combines Pro's reasoning quality with Flash's speed. Significantly better text rendering — near-zero misspellings vs Pro's occasional garbled characters. Supports controllable thinking levels ("minimal"/"high"), additional aspect ratios (1:4, 4:1, 1:8, 8:1), 512px quick-preview resolution, Google Image Search grounding, and up to 10 reference objects. Knowledge cutoff: January 2025 (use Google Search grounding for current data).

**Key insight:** Unlike FLUX/Stable Diffusion (diffusion-only), Nano Banana is a full multimodal LLM that reasons about your prompt before generating. It uses an internal "Thinking" phase (similar to chain-of-thought) to plan composition, follow complex instructions, and render accurate text. This is why it excels at structured layouts like thumbnails.

**NOT a fal.ai model.** Uses Google's `google-genai` Python SDK and `GOOGLE_API_KEY` / `GEMINI_API_KEY` for auth. Completely separate from the fal.ai FLUX pipeline.

---

## API Access

### Prerequisites
```bash
pip install google-genai pillow
# Env: GOOGLE_API_KEY or GEMINI_API_KEY
```

### Basic Generation (NB2)
```python
from google import genai
from google.genai import types

client = genai.Client(api_key="YOUR_KEY")

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",  # NB2
    contents="A 3D Pixar ninja with digital goggles, excited pose",
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"],
        image_config=types.ImageConfig(aspectRatio="9:16", image_size="2K"),
    ),
)

# Extract image from response
for part in response.candidates[0].content.parts:
    if hasattr(part, "inline_data") and part.inline_data:
        with open("output.png", "wb") as f:
            f.write(part.inline_data.data)
```

### Reference Image Editing
```python
with open("reference.jpg", "rb") as f:
    ref_data = f.read()

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[
        types.Part.from_bytes(data=ref_data, mime_type="image/jpeg"),
        "Using this exact character design, create a thumbnail with shocked expression",
    ],
    config=types.GenerateContentConfig(
        response_modalities=["image", "text"],
        image_config=types.ImageConfig(aspectRatio="9:16"),
    ),
)
```

---

## Model Capabilities & Parameters

### Supported Aspect Ratios
**All models:** `1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, `21:9`
**NB2 only:** `1:4`, `4:1`, `1:8`, `8:1` (extreme aspect ratios for banners/strips)

### Resolution Options
| Setting | Approx Output | Use Case |
|---------|--------------|----------|
| `0.5K` (NB2 only) | ~512px long edge | Quick previews, draft iterations |
| `1K` (default) | ~1024px long edge | Drafts, B-roll Ken Burns |
| `2K` | ~2048px long edge | Thumbnails, social media |
| `4K` | ~4096px long edge | Print, high-DPI displays |

**Note:** Use uppercase `K` only — lowercase is rejected by the API.

### Thinking Levels (NB2)
NB2 has controllable thinking via `thinkingLevel`:
- `"minimal"` (default) — faster, good for straightforward prompts
- `"high"` — slower, better for complex multi-element compositions
- Optional `includeThoughts: true` to see reasoning (billed regardless)

**Tip:** Use `"high"` for thumbnails with text + character + topic elements. Use `"minimal"` for simple B-roll stills.

### Google Search Grounding (NB2)
NB2 can search the web before generating — useful for current events, real people's likenesses, or recent game UI screenshots. The model's knowledge cutoff is January 2025, so Search grounding bridges the gap.

### Token Limits
- Input: 65,536 tokens (text + images combined)
- Output: 32,768 tokens
- Up to 10 reference objects (NB2) / 14 reference images (Pro)
- Up to 4 character reference images for identity consistency (NB2)

### What It Excels At
- **Text rendering in images** — NB2 is near-perfect (massive upgrade from Pro's occasional garbled text)
- **Instruction following** — complex multi-element compositions (character + topic + text + branding)
- **Identity consistency** — face/character recognition from reference images
- **Structured layouts** — thumbnails, infographics, product mockups, diagrams
- **Pixar/3D style** — excellent at cartoon/animated character aesthetics
- **Speed** — NB2: 5-12s, Pro: 8-20s (both faster than FLUX Pro/Max)
- **JSON prompt parsing** — natively understands structured JSON, enabling precise control

### What It Struggles With
- **Fine artistic control** — no guidance_scale, no inference steps tuning
- **LoRA/fine-tuning** — not supported (use FLUX Dev for that)
- **Exact pose reproduction** — reference images guide style, not pixel-perfect pose matching
- **Transparency/alpha** — outputs RGB; no native RGBA support
- **Deterministic seeds** — no seed parameter for reproducible outputs
- **Function calling** — not supported on this model variant
- **Spatial accuracy on infographics** — labels can occasionally point to wrong elements (observed in Nate Herk's old-fashioned cocktail test)

---

## JSON Structured Prompting (NEW — Feb 27, 2026)

**The single biggest consistency upgrade for NB2.** Instead of plain text prompts (vague, slot-machine results), wrap image requests in a JSON structure with explicit fields. NB2 parses JSON natively and follows each argument precisely.

### Why It Works
- Plain text prompts are ambiguous — "dramatic lighting" could mean anything
- JSON gives the model explicit, named arguments for every visual dimension
- Results are dramatically more consistent across generations
- The model doesn't have to guess what you meant — each field is unambiguous
- Works especially well with NB2 because the reasoning layer parses structure before generating

### JSON Prompt Schema

```json
{
  "prompt": "Main subject description — what you want to see",
  "negative_prompt": "Things to exclude — artifacts, unwanted elements",
  "style": "Photography style (e.g., documentary realism, editorial, cinematic)",
  "composition": {
    "layout": "Rule of thirds, centered, symmetrical, etc.",
    "camera_angle": "Eye level, low angle, high angle, bird's eye",
    "framing": "Close-up, medium shot, full body, extreme close-up",
    "camera_height": "Ground level, chest height, overhead",
    "lens": "85mm portrait, 35mm wide, 50mm standard, macro",
    "focus": "Shallow DOF on subject, deep focus, selective focus",
    "depth_of_field": "f/1.4 bokeh, f/8 sharp throughout"
  },
  "lighting": {
    "type": "Natural, studio, dramatic, golden hour, neon",
    "direction": "Side lit, backlit, Rembrandt, butterfly",
    "consistency": "Soft diffused, hard shadows, mixed",
    "color_temperature": "Warm 3200K, cool 5600K, mixed"
  },
  "color_grading": "Desaturated moody, vibrant pop, film emulation",
  "resolution": "4K",
  "aspect_ratio": "9:16"
}
```

### How to Use JSON Prompting in Our Pipeline

You don't write the JSON by hand. The LLM (Claude or Gemini) writes it for you based on a plain-text request. The workflow is:

1. **User gives a plain-text intent** — "Ninja character excited about PS Plus games"
2. **LLM converts to JSON prompt** using the schema above + our character spec
3. **JSON prompt gets sent to NB2** for generation
4. **Save the JSON prompt alongside the image** for reproducibility

This is exactly how Claude Code skills work — the skill teaches the LLM to always output structured prompts rather than plain text.

### Ninja Thumbnail JSON Template

```json
{
  "prompt": "3D Pixar ninja character with digital LED goggles showing [EXPRESSION], wearing dark tactical hood and light armor, [POSE], [TOPIC_ELEMENT visible in scene]",
  "negative_prompt": "realistic human eyes, cyberpunk neon city, matrix code, green digital rain, blurry text, watermark",
  "style": "3D Pixar/Disney animation (like The Incredibles or Big Hero 6)",
  "composition": {
    "layout": "Character fills 60% of frame, topic element in remaining space",
    "camera_angle": "Slightly low angle (heroic framing)",
    "framing": "Medium shot, waist up",
    "lens": "35mm, slight wide-angle for energy"
  },
  "lighting": {
    "type": "Dramatic studio with blue accent rim lights",
    "direction": "Three-point: key left, fill right, rim back",
    "consistency": "High contrast for mobile thumbnail visibility"
  },
  "text_elements": {
    "headline": "[PUNCHY 3-5 WORD HEADLINE]",
    "position": "Top or bottom third, large bold text",
    "style": "Clean sans-serif, high contrast against background"
  },
  "resolution": "2K",
  "aspect_ratio": "9:16"
}
```

### Iterating on Style with JSON

Once you find a style you like, save that JSON prompt and reuse its `style`, `lighting`, and `composition` fields for all future thumbnails. Only change `prompt`, `text_elements`, and expression per video. This is how you get a consistent channel look across all thumbnails — something plain-text prompts can't reliably do.

### Expression Through Goggles (our character's signature)
The ninja has digital goggles instead of visible eyes. Map expressions in the JSON `prompt` field:
- **Shocked:** `digital goggle eyes wide with shock/surprise expression`
- **Excited:** `digital goggle eyes showing excited/happy expression with upward curved LED eyes`
- **Thinking:** `digital goggle eyes showing contemplative/squinting expression`

### Topic-Aware Icons
`ninja_thumbnail.py` auto-detects topic keywords and injects relevant visual icon instructions. Examples: gaming controller for gaming topics, glowing skull for security, rocket for space.

---

## Character Consistency

- **Reference image every call** — always pass `ninja_helmet_v3_futuristic.jpg` as the first content part
- **Full description every call** — models have zero memory between requests
- **JSON prompting helps massively** — lock style/lighting/composition in a template, only vary subject per video
- **No LoRA** — for pixel-perfect consistency at scale, FLUX Dev + LoRA is still better. NB2 trades that for reasoning + text rendering.

---

## Character Reference Sheet Technique (NEW — Feb 28, 2026)

**Source:** [@taoprompts — "Nano Banana 2 + Kling 3.0 = Consistent Characters SOLVED"](https://youtu.be/2psBexPkw3I)

This technique solves multi-angle character consistency by generating a structured 8-shot reference sheet, then using it as input for all subsequent generations. The reference sheet becomes the single source of truth for a character's appearance from every angle.

### The 8-Shot Layout

The character reference sheet is a single image divided into **4 vertical columns**, each representing a different angle. Each column has:
- **Top row:** Full body shot
- **Bottom row:** Close-up face shot matching the same angle

| Column 1 | Column 2 | Column 3 | Column 4 |
|-----------|----------|----------|----------|
| Full body — front | Full body — 3/4 left | Full body — side left | Full body — side right |
| Face close-up — front | Face close-up — 3/4 left | Face close-up — side left | Face close-up — side right |

**Why 8 shots:** Having the character from 4 angles (full body + face for each) gives NB2 enough reference data to maintain consistency regardless of camera position in subsequent generations — front, side, 3/4, close-up, or far away.

### Reference Sheet Prompt Structure

```
A character reference sheet of [CHARACTER DESCRIPTION]. The sheet is divided
into four vertical columns showing the character from different angles:

Column 1: Front-facing full body shot (top) and front-facing close-up of the
face (bottom).
Column 2: Three-quarter view from the left, full body shot (top) and
three-quarter view close-up of the face (bottom).
Column 3: Side profile facing left, full body shot (top) and side profile
close-up of the face (bottom).
Column 4: Side profile facing right, full body shot (top) and side profile
close-up of the face (bottom).

Photorealistic, DSLR camera, muted color tones.
```

**Key elements:**
- Keep the character description simple but specific (e.g., "female Viking character with red hair")
- Explicitly describe each column and angle
- **Realism keywords at the bottom are critical:** `photorealistic, DSLR, camera, muted color tones` — the "DSLR" keyword tells NB2 to produce realistic output
- How realistic the reference sheet is determines how realistic ALL subsequent generations will be

### Platforms for Generation

- **Higgs Field AI** (`higgsfield.ai`) — has NB2 model in image generator, supports reference image upload
- **Google Gemini** — direct API or web interface
- **Google AI Studio** — our standard pipeline via `google-genai` SDK

### Common Problem: Mirrored Side Profiles (and the Fix)

NB2 frequently generates both side profiles facing the **same direction** instead of opposite directions. This is the most common failure mode.

**Fix workflow:**
1. Generate the reference sheet (even if side profiles are wrong)
2. Download the incorrect sheet
3. Upload it back into NB2 as a reference image
4. Prompt: `"Change the character reference sheet so that the full body shot of [character] in the third column faces the opposite direction."`
5. NB2 will regenerate with the corrected orientation

This iterative correction is built into NB2's image-editing capability — it understands spatial instructions about its own output.

### Multi-Character Scenes (Up to 14 References)

Once you have reference sheets for multiple characters, upload them all as reference images and describe a scene:

1. Upload each character's reference sheet (up to **14 reference images** in NB2)
2. Describe the scene with both/all characters together
3. Add realism keywords: `"Photorealistic, shot on a DSLR camera with muted colors, shot on 35mm film"`

**Quality note:** Consistency degrades as you add more character references. 2-3 characters works well; 5+ gets progressively less reliable.

**Prompt example for multi-character:**
```
[Character A] and [Character B] standing together in a Viking village
marketplace. Three-quarter full body view. Photorealistic, shot on a DSLR
camera with muted colors, shot on 35mm film.
```

### Realism Keywords Cheat Sheet

Always append these to prompts when generating reference sheets or scenes:
- `photorealistic` — baseline realism
- `DSLR camera` / `DSLR` — triggers photo-quality rendering
- `muted color tones` — prevents oversaturated AI look
- `shot on 35mm film` — adds subtle film grain and natural color grading
- `natural lighting` — prevents flat AI lighting

### Application to Our Pipeline

**For Ninja + Glitch dual-anchor:**
- Generate 8-shot reference sheets for both characters
- Use these as inputs for Kling 3.0 Omni Reference (see kling-avatar-api scroll)
- Generate a "together" shot from NB2 as the starting frame for video generation
- This solves character drift during video — the reference sheet anchors consistency across cuts and camera angles

**For thumbnails:**
- Reference sheets can replace single reference images for more consistent character rendering across thumbnail variations
- Particularly useful when the character needs to appear at different angles per thumbnail

---

## Thumbnail Pipeline Integration

| Tool | Command / Endpoint | Notes |
|------|-------------------|-------|
| **CLI** | `python scripts/ninja_thumbnail.py --topic "..." --style excited` | Styles: engaging/shocked/thinking/pointing/excited |
| **Dojo** | `POST /api/thumbnail-studio/generate` | Fire-and-forget + WS updates |
| **Dojo gallery** | `GET /api/thumbnail-studio/gallery` | Browse recent thumbnails |
| **B-roll** | `ninja_broll.py` | Uses NB Flash (cheap) for Ken Burns stills |

- Reference image: `assets/reference/ninja_helmet_v3_futuristic.jpg`
- Output: `output/thumbnails/thumb_{topic}_{style}.png`
- **DONE (Feb 27, 2026):** `ninja_thumbnail.py` updated to JSON prompting. Use `--save-prompt` to save JSON alongside image, `--show-prompt` to preview without generating.

---

## Comparison: NB2 vs NB Pro vs FLUX.2

| Dimension | Nano Banana 2 | Nano Banana Pro | FLUX.2 (Pro/Max/Flex) |
|-----------|--------------|----------------|----------------------|
| **Architecture** | LLM + reasoning | LLM + reasoning | Diffusion model |
| **Text in images** | Near-perfect | Good (occasional errors) | Poor to mediocre |
| **Parameter control** | thinkingLevel only | None | guidance_scale, steps, seed |
| **LoRA support** | No | No | Yes (Dev model) |
| **Speed** | 5-12s | 8-20s | 15-60s |
| **Seed/reproducibility** | No | No | Full seed support |
| **Multi-image input** | 10 objects + 4 character refs | Up to 14 references | 1-2 via Flex/Kontext |
| **Search grounding** | Yes (web + image) | No | No |
| **JSON prompt parsing** | Excellent | Good | Not applicable |
| **Identity consistency** | Strong (from reference) | Strong (from reference) | Needs LoRA |
| **Pricing (2K)** | ~$0.07 | ~$0.13 | ~$0.03-0.05 |
| **Best for** | Thumbnails, text-heavy, JSON | Complex reasoning | Artistic renders, LoRA |

**Decision rule:**
- **NB2** = default for almost everything. Cheaper, faster, better text than Pro.
- **NB Pro** = only if you need maximum reasoning on very complex compositions (rare).
- **FLUX** = artistic atmosphere, LoRA consistency, or pixel-level parameter control.

---

## Cost & Speed

### Google AI Studio Direct (Recommended)

| Tier | Resolution | Cost/Image | Speed |
|------|-----------|------------|-------|
| Nano Banana (Flash) | 1K | Free tier / minimal | 3-5s |
| **Nano Banana 2** | **0.5K** | **~$0.02** | **~5s** |
| **Nano Banana 2** | **1K** | **~$0.04** | **~8s** |
| **Nano Banana 2** | **2K** | **~$0.07** | **~10s** |
| **Nano Banana 2** | **4K** | **~$0.13** | **~12s** |
| Nano Banana Pro | 1K | ~$0.07 | 8-12s |
| Nano Banana Pro | 2K | ~$0.13 | 10-15s |
| Nano Banana Pro | 4K | ~$0.24 | 15-20s |
| Any model (Batch) | Any | 50% discount | Up to 24h |

**NB2 is ~40% cheaper than Pro at every resolution tier, with comparable or better quality.** The 0.5K preview tier is new and useful for fast draft iterations before generating at full resolution.

**Free tier:** ~50 images/day in Google AI Studio. Paid API: 60 RPM default.

**Our usage pattern with NB2:** ~2-5 thumbnails per video ($0.14-0.35 at 2K), plus B-roll images on Nano Banana Flash (near-free). Monthly cost for daily content: roughly $5-12. Down from $10-20 on Pro.

### Third-Party Proxies (Not Recommended for Us)
Kie.ai offers NB2 routing at reportedly ~$0.04/1K, $0.09/4K — but we already have direct Google API access. Adding a middleman introduces vendor risk for marginal savings (~$3-5/month at our volume). The Remotion MCP uses Kie.ai for TTS/media, but for image generation stick with direct `google-genai` SDK.

### All Images Include SynthID Watermark
Google embeds an invisible SynthID watermark in all generated images for provenance tracking. This does not affect visual quality and is not visible to viewers.

---

## Environment Setup

```bash
# Required env var (already set in our environment)
export GOOGLE_API_KEY="your_key_here"
# OR
export GEMINI_API_KEY="your_key_here"

# The SDK checks GOOGLE_API_KEY first, then GEMINI_API_KEY
```

**SDK:** `google-genai` (not `google-generativeai` — that is the older package)

---

## Best Practices (Hard-Won)

1. **Use JSON prompts for consistency** — structured prompts with explicit fields (style, lighting, composition) produce dramatically more predictable results than plain text. Save winning JSON templates and reuse the style/lighting/composition fields across generations.
2. **Always pass reference image** for character thumbnails — without it, the ninja looks different every time
3. **Use CRITICAL: prefix** in plain-text prompts for traits that must not be ignored (goggles, no human eyes, mask). In JSON prompts, put these in the main `prompt` field.
4. **NB2 for thumbnails, NB Flash for B-roll** — NB2 is now cheaper than Pro was. No reason to use Pro for standard thumbnails.
5. **response_modalities must include "IMAGE"** — without it, you only get text back
6. **Text rendering is the killer feature** — lean into headlines and branding. NB2's text accuracy is a significant upgrade from Pro.
7. **Use `thinkingLevel: "high"` for complex compositions** — thumbnails with character + text + topic benefit from deeper reasoning. Use `"minimal"` for simple B-roll.
8. **negative_prompt in JSON** — explicitly list what you don't want (realistic human eyes, cyberpunk neon, blurry text, watermarks). This field significantly reduces bad outputs.
9. **Multi-turn editing works** — you can iterate on a generated image in conversation
10. **No seed = no exact reproduction** — generate 2-3 variants and pick the best. JSON prompting reduces variance but doesn't eliminate it.
11. **9:16 for Shorts, 16:9 for long-form** — set aspect ratio explicitly every call
12. **0.5K for drafts, 2K for final** — use NB2's new 512px preview to iterate cheaply, then generate final at 2K
13. **Enable Google Search grounding** for current events — game announcements, new releases, etc. The model's cutoff is Jan 2025.
14. **Save JSON prompts alongside images** — creates a reproducible prompt library. When you find a style that works, you can reapply it to new subjects.
