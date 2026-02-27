---
name: nano-banana-pro
domain: Image/Character Art
level: 3-tomoe
description: Google's Nano Banana Pro (Gemini 3 Pro Image) — reasoning-driven image generation and editing via generate_content API. Powers the Ninja thumbnail pipeline, B-roll Ken Burns images, and Dojo Thumbnail Studio. NOT a fal.ai model — runs on Google's Gemini API.
sources:
  - type: docs
    title: "Nano Banana image generation — Gemini API"
    url: "https://ai.google.dev/gemini-api/docs/image-generation"
    date: "2026-02-24"
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
last_updated: 2026-02-24
sources_count: 8
can_do_from_cli: true
---

# Nano Banana Pro — Google Gemini 3 Pro Image Generation

## Mental Model

"Nano Banana" is Google's branding for native image generation built into the Gemini model family. There are two tiers:

| Codename | Model ID | Based On | Strength |
|----------|----------|----------|----------|
| **Nano Banana** | `gemini-2.5-flash-image` | Gemini 2.5 Flash | Speed, volume, budget |
| **Nano Banana Pro** | `gemini-3-pro-image-preview` | Gemini 3 Pro | Reasoning, precision, text rendering |
| **Nano Banana Pro 2** | `gemini-3.1-flash-image-preview` | Gemini 3.1 Flash | Pro quality at Flash speed, ~40% cheaper |

**UPDATE (2026-02-26):** Nano Banana Pro 2 launched. It combines Pro's reasoning quality with Flash's speed. New model ID: `gemini-3.1-flash-image-preview`. Supports controllable thinking levels ("minimal"/"high"), additional aspect ratios (1:4, 4:1, 1:8, 8:1), 512px quick-preview resolution, and Google Image Search grounding. All pipeline scripts updated to use Pro 2 as the new default.

**Key insight:** Unlike FLUX/Stable Diffusion (diffusion-only), Nano Banana Pro is a full multimodal LLM that reasons about your prompt before generating. It uses an internal "Thinking" phase (similar to chain-of-thought) to plan composition, follow complex instructions, and render accurate text. This is why it excels at structured layouts like thumbnails.

**NOT a fal.ai model.** Uses Google's `google-genai` Python SDK and `GOOGLE_API_KEY` / `GEMINI_API_KEY` for auth. Completely separate from the fal.ai FLUX pipeline.

---

## API Access

### Prerequisites
```bash
pip install google-genai pillow
# Env: GOOGLE_API_KEY or GEMINI_API_KEY
```

### Basic Generation
```python
from google import genai
from google.genai import types

client = genai.Client(api_key="YOUR_KEY")

response = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents="A 3D Pixar ninja with digital goggles, excited pose",
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"],
        image_config=types.ImageConfig(
            aspectRatio="9:16",     # Shorts thumbnails
            image_size="2K",        # 1K | 2K | 4K
        ),
    ),
)

# Extract image from response
for part in response.candidates[0].content.parts:
    if hasattr(part, "inline_data") and part.inline_data:
        with open("output.png", "wb") as f:
            f.write(part.inline_data.data)
```

### Reference Image Editing (up to 14 images)
```python
with open("reference.jpg", "rb") as f:
    ref_data = f.read()

response = client.models.generate_content(
    model="gemini-3-pro-image-preview",
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
`1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, `21:9`

### Resolution Options
| Setting | Approx Output | Use Case |
|---------|--------------|----------|
| `1K` (default) | ~1024px long edge | Drafts, B-roll Ken Burns |
| `2K` | ~2048px long edge | Thumbnails, social media |
| `4K` | ~4096px long edge | Print, high-DPI displays |

**Note:** Use uppercase `K` only — lowercase is rejected by the API.

### Token Limits
- Input: 65,536 tokens (text + images combined)
- Output: 32,768 tokens
- Up to 14 reference images in a single request

### What It Excels At
- **Text rendering in images** — state-of-the-art for headlines, labels, UI mockups
- **Instruction following** — complex multi-element compositions (character + topic + text + branding)
- **Identity consistency** — face/character recognition from reference images
- **Structured layouts** — thumbnails, infographics, product mockups
- **Pixar/3D style** — excellent at cartoon/animated character aesthetics
- **Speed** — 8-12 seconds per generation (faster than FLUX Pro/Max)

### What It Struggles With
- **Fine artistic control** — no guidance_scale, no inference steps tuning
- **LoRA/fine-tuning** — not supported (use FLUX Dev for that)
- **Exact pose reproduction** — reference images guide style, not pixel-perfect pose matching
- **Transparency/alpha** — outputs RGB; no native RGBA support
- **Deterministic seeds** — no seed parameter for reproducible outputs
- **Function calling** — not supported on this model variant

---

## Prompt Engineering for Character Thumbnails

### The Ninja Thumbnail Formula (validated in production)
```
SUBJECT: [Full character description every call — models have zero memory]
CRITICAL: [Non-negotiable character traits — goggles, mask, etc.]
COMPOSITION: [Layout rules — character placement, topic visualization]
STYLE: [Aesthetic direction — Pixar, lighting, aspect ratio]
TEXT ELEMENTS: [Headlines, branding — NBP excels at this]
```

### Style Keywords That Work
- `3D Pixar/Disney animation style (like The Incredibles or Big Hero 6)`
- `Soft, appealing character design with expressive digital goggle eyes`
- `Dramatic lighting with blue accent rim lights`
- `High contrast for mobile visibility`
- `Professional 3D render, cinematic lighting`

### Expression Through Goggles (our character's signature)
The ninja has digital goggles instead of visible eyes. Expressions come from LED patterns:
- **Shocked:** `digital goggle eyes wide with shock/surprise expression`
- **Excited:** `digital goggle eyes showing excited/happy expression with upward curved LED eyes`
- **Thinking:** `digital goggle eyes showing contemplative/squinting expression`

### Topic-Aware Icons
`ninja_thumbnail.py` auto-detects topic keywords and injects relevant visual icon instructions. Examples: gaming controller for gaming topics, glowing skull for security, rocket for space. This significantly improves thumbnail relevance.

---

## Character Consistency Techniques

1. **Reference image every call** — always pass `ninja_helmet_v3_futuristic.jpg` as the first content part
2. **Full description every call** — repeat the complete character spec (goggles, hood, armor, katana)
3. **CRITICAL markers** — use "CRITICAL:" prefix for non-negotiable traits the model must preserve
4. **Style anchors** — name specific Pixar films ("like Big Hero 6") for consistent 3D aesthetic
5. **No seed control** — unlike FLUX, Nano Banana Pro has no seed parameter. Consistency comes from reference images + detailed prompts, not deterministic generation

**Limitation:** Cannot train a LoRA on this model. For pixel-perfect character consistency at scale, FLUX Dev + LoRA is still the better path. Nano Banana Pro trades that for reasoning ability and text rendering.

---

## Thumbnail Pipeline Integration

### ninja_thumbnail.py (CLI)
```bash
python scripts/ninja_thumbnail.py --topic "State of Play February 2026" --style excited
python scripts/ninja_thumbnail.py --topic "PS Plus March Games" --style shocked --output custom.png
```
- Styles: `engaging`, `shocked`, `thinking`, `pointing`, `excited`
- Auto-detects topic icons via `_detect_topic_icons()`
- Auto-generates punchy headline via `_extract_headline()`
- Reference image: `assets/reference/ninja_helmet_v3_futuristic.jpg`
- Output: `output/thumbnails/thumb_{topic}_{style}.png`

### Dojo Thumbnail Studio (Web UI)
- `POST /api/thumbnail-studio/generate` — fire-and-forget with WS status updates
- `POST /api/thumbnail-studio/generate-from-image` — with custom inspiration image
- `GET /api/thumbnail-studio/gallery` — browse recent thumbnails
- `POST /api/thumbnail-studio/attach/{filename}` — link thumbnail to a pipeline job
- Supports custom headline override and aspect ratio selection

### B-roll Ken Burns (ninja_broll.py)
Uses the cheaper **Nano Banana** (`gemini-2.5-flash-image`) for B-roll stills — no need for Pro quality on background images that get Ken Burns panned. This is a deliberate cost optimization.

---

## Comparison: Nano Banana Pro vs FLUX.2

| Dimension | Nano Banana Pro | FLUX.2 (Pro/Max/Flex) |
|-----------|----------------|----------------------|
| **Architecture** | Multimodal LLM + reasoning | Diffusion model |
| **Text in images** | Excellent (state-of-art) | Poor to mediocre |
| **Parameter control** | None (zero-config) | guidance_scale, steps, seed |
| **LoRA support** | No | Yes (Dev model) |
| **Speed** | 8-12s | 15-60s depending on model |
| **Seed/reproducibility** | No seed parameter | Full seed support |
| **Multi-image input** | Up to 14 references | 1-2 via Flex/Kontext |
| **Artistic style** | Good, instruction-driven | Excellent, atmosphere-rich |
| **Identity consistency** | Strong (from reference) | Needs LoRA for reliable |
| **Pricing** | ~$0.13/2K image | ~$0.03-0.05/image |
| **Best for** | Thumbnails, text-heavy, layouts | Artistic renders, LoRA characters |

**Decision rule:** Use Nano Banana Pro when you need text rendering or complex structured layouts. Use FLUX when you need artistic atmosphere, LoRA consistency, or parameter control.

---

## Cost & Speed

| Tier | Resolution | Cost/Image | Speed |
|------|-----------|------------|-------|
| Nano Banana (Flash) | 1K | Free tier / minimal | 3-5s |
| Nano Banana Pro | 1K | ~$0.07 | 8-12s |
| Nano Banana Pro | 2K | ~$0.13 | 10-15s |
| Nano Banana Pro | 4K | ~$0.24 | 15-20s |
| Nano Banana Pro (Batch) | Any | 50% discount | Up to 24h |

**Free tier:** ~50 images/day in Google AI Studio. Paid API: 60 RPM default.

**Our usage pattern:** ~2-5 thumbnails per video ($0.26-0.65), plus B-roll images on Nano Banana Flash (near-free). Monthly cost for daily content: roughly $10-20.

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

1. **Always pass reference image** for character thumbnails — without it, the ninja looks different every time
2. **Use CRITICAL: prefix** for traits that must not be ignored (goggles, no human eyes, mask)
3. **Nano Banana Flash for B-roll, Pro for thumbnails** — dont overspend on background images
4. **response_modalities must include "IMAGE"** — without it, you only get text back
5. **Text rendering is the killer feature** — lean into headlines and branding in the prompt
6. **Multi-turn editing works** — you can iterate on a generated image in conversation
7. **No seed = no exact reproduction** — generate 2-3 variants and pick the best
8. **9:16 for Shorts, 16:9 for long-form** — set aspect ratio explicitly every call
9. **Auto-detect resolution from input** — the openclaw skill auto-bumps to 2K/4K based on reference image size
10. **Thinking mode is always on** — the model reasons internally before generating; this is why it follows complex prompts better than pure diffusion models
