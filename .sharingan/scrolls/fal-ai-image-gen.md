---
name: fal-ai-image-gen
domain: Image/Character Art
level: 3-tomoe
description: fal.ai image generation for consistent character art — FLUX.2 model family, LoRA training workflows, API parameter reference, and production patterns. Validated against ninja_content.py Kling integration.
sources:
  - type: docs
    title: "fal.ai FLUX.2 Models Catalog"
    url: "https://fal.ai/flux-2"
    date: "2026-02-23"
    confidence: high
  - type: docs
    title: "fal.ai Python SDK Docs"
    url: "https://docs.fal.ai/"
    date: "2026-02-19"
    confidence: high
  - type: docs
    title: "FLUX.2 [flex] API Reference"
    url: "https://fal.ai/models/fal-ai/flux-2-flex/api"
    date: "2026-02-23"
    confidence: high
  - type: docs
    title: "FLUX.2 [pro] API Reference"
    url: "https://fal.ai/models/fal-ai/flux-2-pro"
    date: "2026-02-23"
    confidence: high
  - type: docs
    title: "FLUX.2 [dev] Trainer Reference"
    url: "https://fal.ai/models/fal-ai/flux-2-trainer"
    date: "2026-02-23"
    confidence: high
  - type: docs
    title: "Flux 2 Developer Guide (LoRA + Production)"
    url: "https://fal.ai/learn/devs/flux-2-developer-guide"
    date: "2026-02-23"
    confidence: high
  - type: blog
    title: "Training FLUX.2 LoRAs"
    url: "https://blog.fal.ai/training-flux-2-loras/"
    date: "2026-02-23"
    confidence: high
  - type: github
    title: "Existing fal_client usage in ninja_content.py"
    url: "file:///home/ndninja/scripts/ninja_content.py"
    date: "2026-02-19"
    confidence: high
last_updated: 2026-02-23
sources_count: 8
can_do_from_cli: true
---

# fal.ai Image Generation — FLUX.2 Model Family

## Mental Model
fal.ai hosts FLUX.2 (Black Forest Labs' latest) as GPU-as-a-service APIs. The FLUX.2 family has distinct tiers: **pro** (zero-config, production), **flex** (tunable parameters, multi-reference), **dev** (LoRA-capable base), **klein** (realtime/lightweight), **flash/turbo** (speed). For character work: use **flex** for prompt-controlled poses, **pro** for fire-and-forget quality, and **dev + LoRA** for 95% consistency at scale.

## Prerequisites
- `pip install fal-client`
- `FAL_KEY` env var (replaces older `FAL_AI_API_KEY`)
- Credits at [fal.ai dashboard](https://fal.ai/dashboard)

---

## FLUX.2 Model Decision Table

| Model | Endpoint | Best For | Parameters | Pricing |
|-------|----------|----------|------------|---------|
| **Pro** | `fal-ai/flux-2-pro` | Production fire-and-forget | Prompt + seed only (zero-config) | $0.03/MP base + $0.015/MP extra |
| **Max** | `fal-ai/flux-2-max` | Maximum realism + editing | Prompt + image_urls | Premium tier |
| **Flex** | `fal-ai/flux-2-flex` | Tunable poses, multi-ref editing | guidance_scale, steps, image_urls | $0.05/MP in+out |
| **Dev** | `fal-ai/flux/dev` | LoRA inference, rapid iteration | guidance_scale, steps, lora_config | ~$0.03/img |
| **Klein 9B** | `fal-ai/flux-2-klein/9b` | Fast generation, LoRA support | Lightweight params | Budget tier |
| **Klein 4B** | `fal-ai/flux-2-klein/4b` | Realtime previews | Minimal params | Budget tier |
| **Flash** | `fal-ai/flux-2-flash` | Speed-optimized | Reduced steps | Fast tier |
| **Kontext** | `fal-ai/flux-pro/kontext` | Image EDITING (not poses) | image_url + prompt | $0.025/MP |

**Key insight:** FLUX.2 Pro has NO guidance_scale or inference_steps — it's zero-config by design. Use Flex when you need parameter control.

---

## FLUX.2 Flex — Full API Parameter Reference

| Parameter | Type | Default | Range | Notes |
|-----------|------|---------|-------|-------|
| `prompt` | string | required | - | Full character description every call |
| `guidance_scale` | float | 3.5 | 1.5-10.0 | 5.0-6.5 for character poses |
| `num_inference_steps` | int | 28 | 2-50 | 32-40 for character detail |
| `image_size` | enum/object | landscape_4_3 | see below | Or `{"width": 768, "height": 1024}` |
| `image_urls` | string[] | - | - | Reference images for editing mode |
| `seed` | int | random | - | Pin for reproducibility |
| `enable_prompt_expansion` | bool | true | - | Model enriches your prompt |
| `safety_tolerance` | enum | "2" | 1-5 | 5 = most permissive |
| `output_format` | enum | "jpeg" | jpeg/png | png for transparency pipelines |
| `sync_mode` | bool | false | - | Returns data URI inline |

**Image size presets:** `square_hd`, `square`, `portrait_4_3`, `portrait_16_9`, `landscape_4_3`, `landscape_16_9`

---

## Workflow 1: Character Pose Generation (Flex — Tunable)

```python
import fal_client, os, urllib.request

os.environ["FAL_KEY"] = "your_key"

GLITCH = """
3D Pixar/Disney animation style character (like Big Hero 6, The Incredibles):
Petite athletic girl, approximately 5 heads tall, slender build.
Face: Round cute face, digital goggle visor covering eyes with pink/purple neon glow.
Short dark blonde hair in a high ponytail with black hair tie.
Outfit: Black tactical bodysuit with dark gray armor panels. Hot pink (#FF1493) and
magenta neon-glowing circuit lines on armor. Small katana sheathed on back.
Style: Professional 3D render, Pixar film quality, cinematic lighting, white background.
Full body visible head to toe.
"""

def gen_pose(name, pose_desc, out_dir="output"):
    result = fal_client.subscribe(
        "fal-ai/flux-2-flex",
        arguments={
            "prompt": f"{GLITCH}\nPose: {pose_desc}",
            "guidance_scale": 5.5,
            "num_inference_steps": 35,
            "image_size": "portrait_4_3",
            "output_format": "png",
            "seed": 42,  # pin seed for reproducible batches
        },
    )
    url = result["images"][0]["url"]
    urllib.request.urlretrieve(url, f"{out_dir}/{name}_raw.png")
    print(f"  done: {name} ({result['images'][0].get('width')}x{result['images'][0].get('height')})")
```

## Workflow 2: Fire-and-Forget (Pro — Zero Config)

```python
# No guidance_scale, no steps — model handles everything
result = fal_client.subscribe(
    "fal-ai/flux-2-pro",
    arguments={
        "prompt": f"{GLITCH}\nPose: excited, arms raised, big smile",
        "image_size": "portrait_4_3",
        "output_format": "png",
        "seed": 42,
    },
)
# Pro is cheaper ($0.03/MP vs $0.05/MP) and needs zero tuning
```

---

## Workflow 3: FLUX.2 LoRA Training (Production Consistency)

### Step 1: Prepare Dataset
```bash
# Create training zip: 9-50 images, 1024x1024+ resolution
# Optional: add .txt caption files alongside each image
mkdir glitch_training && cd glitch_training

# Include varied poses, angles, expressions of the SAME character
# front, side, three-quarter, close-up, full-body
# NO watermarks, NO text overlays, NO compression artifacts

# Optional caption files (same name as image, .txt extension)
echo "glitch_char, Pixar 3D girl, pink neon armor, digital goggles, excited pose" > pose_01.txt

zip -r ../glitch_dataset.zip .
```

### Step 2: Upload and Train
```python
import fal_client

# Upload dataset zip
with open("glitch_dataset.zip", "rb") as f:
    dataset_url = fal_client.upload(f.read(), "application/zip")

# Train FLUX.2 LoRA — costs $0.008/step ($8 for 1000 steps)
training = fal_client.subscribe(
    "fal-ai/flux-2-trainer",
    arguments={
        "image_data_url": dataset_url,
        "steps": 1000,                     # 1000 = good baseline for characters
        "learning_rate": 0.00005,           # default, safe for characters
        "default_caption": "glitch_char, Pixar 3D cyberpunk girl, pink neon armor, digital goggles",
        "output_lora_format": "fal",        # "fal" or "comfy" (for ComfyUI)
    },
)

# SAVE THESE PERMANENTLY — cannot recover lost LoRA IDs
lora_url = training["diffusers_lora_file"]["url"]
config_url = training["config_file"]["url"]
print(f"LoRA: {lora_url}")
print(f"Config: {config_url}")
```

### Step 3: Generate with LoRA
```python
result = fal_client.subscribe(
    "fal-ai/flux/dev",                      # Dev for LoRA inference
    arguments={
        "prompt": "glitch_char, excited pose, arms raised, smiling, full body, white background",
        "lora_config": {"path": lora_url, "scale": 1.0},
        "guidance_scale": 3.5,
        "num_inference_steps": 28,
        "image_size": "portrait_4_3",
    },
)
```

### LoRA Pricing
T2I training: **$0.008/step** ($8 for 1000 steps). Edit training: $0.009/step x ref_multiplier (1 ref=2.11x, 2 refs=3.44x).

**LoRA tips:**
- `scale` 0.5-1.5 safe range; >1.5 degrades quality
- Trigger word MUST appear in every generation prompt
- 9-50 images ideal; more is NOT always better (redundancy hurts)
- Varied poses/angles in training = flexible generation
- Caption files let you teach the model which elements vary vs stay fixed

---

## Workflow 4: kontext — Image Editing Only

```python
with open("glitch_base.jpeg", "rb") as f:
    ref_url = fal_client.upload(f.read(), "image/jpeg")

result = fal_client.run("fal-ai/flux-pro/kontext", arguments={
    "image_url": ref_url,
    "prompt": "Change the neon glow color from pink to cyan/teal",
    "guidance_scale": 3.5, "num_inference_steps": 28,
})
```
**Use for:** background swaps, recoloring, lighting. **NEVER for:** poses, proportions, expressions.

---

## guidance_scale Cheat Sheet

| Value | Effect | Use Case |
|-------|--------|----------|
| 1.5-2.0 | Loose, creative | Artistic exploration |
| 3.5 | Balanced default | Edits, kontext, LoRA inference |
| 5.0-6.5 | Strong prompt adherence | Character poses (Flex) |
| 7.0-10.0 | Very strict | Technical accuracy needs |
| 10+ | Over-constrained | Avoid — degrades quality |

**Remember:** Pro has NO guidance_scale. Flex/Dev/Kontext do.

---

## Error Handling + Retry Pattern

```python
import time

def gen_with_retry(model, args, retries=3):
    for i in range(retries):
        try:
            return fal_client.subscribe(model, arguments=args, timeout=300)
        except fal_client.RequestFailedError as e:
            if e.status_code == 429:
                time.sleep(2 ** i)
                continue
            raise
        except fal_client.RequestTimeoutError:
            if i < retries - 1:
                time.sleep(5)
    raise RuntimeError(f"Generation failed after {retries} retries")
```

## Cost Calculator

| Scenario | Cost |
|----------|------|
| 6 poses via Flex (no LoRA) | ~$0.30 |
| 6 poses via Pro (zero-config) | ~$0.18 |
| LoRA training (1000 steps) | ~$8.00 |
| 6 poses with LoRA (Dev) | ~$0.18 |
| **Full LoRA pipeline** | **~$8.18** |

## Integration Points
- **Key location:** `FAL_KEY` in env (or `FAL_AI_API_KEY` — client checks both)
- **Existing usage:** `ninja_content.py` uses `fal_client.run("fal-ai/kling-video/v2/master/image-to-video")`
- **Sprite pipeline:** Generated poses -> `rembg` background removal -> `sprite_layers/poses/`
- **Gen script:** `/home/ndninja/projects/glitch/scripts/gen_sprites.py`

## Best Practices (Hard-Won)
1. **Never use kontext for poses.** It is an edit tool. Full stop.
2. **Pro for production, Flex for experimentation.** Pro is cheaper and zero-config.
3. **Repeat full character description every call** — models have zero memory between requests.
4. **Use `subscribe()` not `run()`** for 30+ step jobs — avoids timeout on slow GPU queues.
5. **Save LoRA URLs permanently** — if you lose them, the trained model is gone.
6. **Test at low steps first** (10-15) to verify composition, then bump to 35 for finals.
7. **Pin seeds** for batch consistency — same seed + same prompt = reproducible output.
8. **Dataset quality > quantity** for LoRA — 15 varied, high-res images beats 50 redundant ones.
9. **Caption files** in LoRA training let you control which elements the model learns to vary.
10. **`enable_prompt_expansion: false`** if your prompts are already detailed — avoids model overriding your intent.
