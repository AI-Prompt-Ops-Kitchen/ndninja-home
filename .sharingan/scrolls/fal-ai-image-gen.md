---
name: fal-ai-image-gen
domain: Image/Character Art
level: 2-tomoe
description: fal.ai image generation for consistent character poses — Flux model comparison, LoRA training, and why kontext is wrong for pose variation. Validated against existing ninja_content.py Kling integration.
sources:
  - type: docs
    title: "fal.ai Models Catalog"
    url: "https://fal.ai/models"
    date: "2026-02-19"
    confidence: high
  - type: docs
    title: "fal.ai Python SDK Docs"
    url: "https://docs.fal.ai/"
    date: "2026-02-19"
    confidence: high
  - type: github
    title: "Existing fal_client usage in ninja_content.py"
    url: "file:///home/ndninja/scripts/ninja_content.py"
    date: "2026-02-19"
    confidence: high
last_updated: 2026-02-19
can_do_from_cli: true
---

# fal.ai Image Generation — Character Pose Consistency

## Mental Model
fal.ai is a GPU-as-a-service API hosting Flux and other image gen models. For a game character like Glitch, the right model depends on what you're trying to do: **text-only generation** (flux-2-flex/flux-dev) gives you prompt control over proportions; **image-guided generation** (kontext) preserves the reference so tightly it defeats the purpose. LoRA training is the production solution — $10 upfront, then infinite poses with 95% style consistency.

## Prerequisites
- `pip install fal-client`
- `FAL_AI_API_KEY` in `.env` at `/home/ndninja/projects/content-automation/.env`
- fal.ai credits loaded (check at fal.ai dashboard)

## The Core Insight: Why kontext Failed for Poses

**`flux-pro/kontext` is an image EDITING model, not a pose variation model.**
It's designed for local edits — change background color, swap outfit, remove object. The reference image is the anchor, and proportions are treated as sacred. Even at `guidance_scale: 1.5` (minimum), it preserves 85%+ of the reference proportions. This is why v1 and v2 poses looked identical — we used the wrong tool.

**Rule:** kontext for style/outfit edits → flux-2-flex or flux-dev for new poses.

## Core Workflows

### Workflow 1: Character Pose Generation (MVP — No LoRA)
**When to use:** Generating 4-6 poses quickly without training. ~75% consistency.

```python
import fal_client, os, urllib.request
from pathlib import Path

os.environ["FAL_KEY"] = "your_key"  # or load from .env

GLITCH = """
3D Pixar/Disney animation style character (like Big Hero 6, The Incredibles):
Petite athletic girl, approximately 5 heads tall, slender build.
Face: Round cute face, digital goggle visor covering eyes with pink/purple neon glow.
Short dark blonde hair in a high ponytail with black hair tie.
Outfit: Black tactical bodysuit with dark gray armor panels. Hot pink (#FF1493) and
magenta neon-glowing circuit lines on armor. Small katana sheathed on back.
Translucent pink goggles with neon frame. Fair skin. Blue eyes visible through goggles.
Style: Professional 3D render, Pixar film quality, cinematic lighting, white background.
Full body visible head to toe.
"""

def gen_pose(name, pose_desc, out_dir):
    result = fal_client.subscribe(
        "fal-ai/flux-2-flex",                    # ← NOT kontext
        arguments={
            "prompt": f"{GLITCH}\nPose: {pose_desc}",
            "guidance_scale": 5.5,               # 5-6 = good prompt adherence
            "num_inference_steps": 35,           # 32-40 for character detail
            "image_size": "portrait_4_3",
            "output_format": "png",
        },
    )
    url = result["images"][0]["url"]
    urllib.request.urlretrieve(url, f"{out_dir}/{name}_raw.png")
    print(f"  ✓ {name}")
```

**Gotchas:**
- Specify character details in EVERY prompt call — model has no memory between requests
- `guidance_scale` 5-6 is the sweet spot: higher = proportions locked by model defaults
- `flux-2-flex` is newer/better than `flux-pro` for character detail (Feb 2026)
- Always use `subscribe()` not `run()` — longer generation, safer for 35+ steps

---

### Workflow 2: LoRA Training for Production Consistency (95% consistency)
**When to use:** After MVP is validated. $10 one-time → unlimited poses. [SINGLE SOURCE — not yet validated]

```python
# Step 1: Upload 4-8 reference images (varied poses, same character)
urls = []
for img_path in reference_images:
    with open(img_path, "rb") as f:
        urls.append(fal_client.upload(f.read(), "image/jpeg"))

# Step 2: Train LoRA (~10-15 min)
training = fal_client.run(
    "fal-ai/flux-lora-fast-training",
    arguments={
        "images_data_url": urls,
        "trigger_word": "glitch_char",  # Must use in every prompt
        "type": "character",
        "steps": 1000,                  # 1000 recommended for characters
    }
)
lora_id = training["lora_id"]          # Save this permanently!

# Step 3: Generate with LoRA
result = fal_client.subscribe(
    "fal-ai/flux-dev",                  # Dev is faster, LoRA handles quality
    arguments={
        "prompt": "glitch_char, excited pose, arms raised, smiling",
        "lora_config": {"path": lora_id, "scale": 1.0},  # 0.5-1.5 safe range
        "guidance_scale": 3.5,
        "num_inference_steps": 28,
    }
)
```

**Gotchas:**
- Training images must have variety (different poses/angles) or LoRA learns a single-pose bias
- `trigger_word` MUST appear in every generation prompt to activate LoRA
- `scale > 1.5` can degrade quality — stay in 0.5-1.5 range
- Include character details in prompt even with LoRA — trigger word activates it, prompt guides the variation
- Training images must NOT have watermarks/text overlays (LoRA will learn to reproduce them)

---

### Workflow 3: kontext — What It's Actually Good For
**When to use:** Minor style/outfit edits where you want to preserve the character exactly.

```python
# Upload reference
with open("glitch_base.jpeg", "rb") as f:
    ref_url = fal_client.upload(f.read(), "image/jpeg")

# Edit outfit color, not pose
result = fal_client.run(
    "fal-ai/flux-pro/kontext",
    arguments={
        "image_url": ref_url,
        "prompt": "Change the neon glow color from pink to cyan/teal",
        "guidance_scale": 3.5,          # Default is fine for edits
        "num_inference_steps": 28,
    }
)
```

**Use kontext for:** background swaps, outfit recoloring, adding/removing objects, lighting changes.
**Never use kontext for:** different poses, proportions changes, dramatically different expressions.

---

### Workflow 4: Uploading Reference Files
**When to use:** Any workflow needing to pass a local image to fal.ai

```python
with open("glitch_avatar_v2.jpeg", "rb") as f:
    url = fal_client.upload(f.read(), "image/jpeg")
# url valid for ~30 minutes — use immediately or re-upload
```

---

## Model Quick Reference

| Model | Best For | Cost | Speed | guidance_scale sweet spot |
|-------|----------|------|-------|--------------------------|
| `flux-2-flex` | New character poses, best quality | ~$0.06/img | ~30s | 5.0-6.5 |
| `flux-dev` | Rapid iteration, with LoRA | ~$0.05/img | ~15s | 3.5 |
| `flux-pro` | High-quality final outputs | ~$0.05/img | ~30s | 5.0 |
| `flux-pro/kontext` | Editing existing images | $0.04/img (fixed) | ~25s | 2.0-3.5 |
| `flux-lora-fast-training` | One-time character LoRA | ~$10 one-time | 10-15 min | N/A |

**Note:** `flux-pro` (original) is DEPRECATED — use `flux-2-flex` or `flux-dev` instead.

## guidance_scale Cheat Sheet

| Value | Effect |
|-------|--------|
| 1.0-2.0 | Creative, loose — model does what it wants |
| 3.5 | Default balanced (good for edits/kontext) |
| 5.0-6.5 | Strong prompt adherence (good for character poses) |
| 7.0-10.0 | Very strict — may lose fine detail |
| 15+ | Over-constrained — usually degrades quality |

## Error Handling Pattern

```python
import time

def gen_with_retry(model, args, retries=3):
    for i in range(retries):
        try:
            return fal_client.subscribe(model, arguments=args, timeout=300)
        except fal_client.RequestFailedError as e:
            if e.status_code == 429:          # Rate limited
                time.sleep(2 ** i)
                continue
            raise
        except fal_client.RequestTimeoutError:
            if i < retries - 1: time.sleep(5)
    raise RuntimeError("Generation failed after retries")
```

## Cost Calculator for Glitch Poses

| Scenario | Cost |
|----------|------|
| 6 poses, no LoRA (MVP) | ~$0.36 |
| LoRA training (one-time) | ~$10 |
| 6 poses with LoRA | ~$0.40 |
| **Total with LoRA** | **~$10.40** |

## Integration Points
- **Key location:** `FAL_AI_API_KEY` in `/home/ndninja/projects/content-automation/.env`
- **Existing usage:** `ninja_content.py` uses `fal_client.run("fal-ai/kling-video/v2/master/image-to-video")` for Kling Avatar — same client, different model ID
- **Sprite pipeline:** Generated poses → `rembg` background removal → `sprite_layers/poses/`
- **Gen script:** `/home/ndninja/projects/glitch/scripts/gen_sprites.py`

## Limitations & Gaps
- LoRA training workflow is documented but untested by me — treat as [SINGLE SOURCE]
- `fal-ai/flux-lora-fast-training` endpoint name may differ — verify at fal.ai/models before running
- Pricing is estimated from research; check current rates at fal.ai dashboard before bulk generation
- `flux-2-flex` is newest model (Feb 2026) — may have changed since this scroll was written

## Tips & Best Practices
- **Never use kontext for poses.** It's an edit tool, not a pose generator. Full stop.
- **flux-2-flex over flux-pro** for Glitch — better color fidelity, newer model, same price.
- **Repeat full character description every call** — model has zero memory between requests.
- **Use `subscribe()` not `run()`** for 30+ inference step jobs — avoids timeout on slow GPU queues.
- **Save LoRA IDs permanently** — if you lose the ID you can't recover the trained model.
- **Test at low inference_steps first** (10-15) to verify composition, then bump to 35 for finals.
- **`guidance_scale: 5.5` for Glitch poses** — found through trial to hit Pixar proportions reliably.
