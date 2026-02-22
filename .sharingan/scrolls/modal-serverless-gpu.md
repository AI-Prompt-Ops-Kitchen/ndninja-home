---
name: modal-serverless-gpu
domain: Cloud/GPU
level: 2-tomoe
description: Serverless GPU cloud platform — deploy AI workloads via Python SDK with sub-second cold starts, elastic scaling to thousands of GPUs, and pay-per-second billing. $30/mo free credits.
sources:
  - type: web
    title: "Modal: High-performance AI infrastructure"
    url: "https://modal.com/"
    date: "2026-02-22"
    confidence: high
  - type: web
    title: "Modal Pricing"
    url: "https://modal.com/pricing"
    date: "2026-02-22"
    confidence: high
  - type: web
    title: "Top Serverless GPU Clouds for 2026 (RunPod comparison)"
    url: "https://www.runpod.io/articles/guides/top-serverless-gpu-clouds"
    date: "2026-02-22"
    confidence: medium
last_updated: 2026-02-22
can_do_from_cli: true
---

# Modal — Serverless GPU Cloud

## Mental Model
Modal is a serverless GPU cloud where you write Python code, not YAML. You decorate functions with `@app.function(gpu="A100")`, push your code, and Modal handles containers, GPUs, scaling, and teardown. It's like AWS Lambda but for GPU workloads — pay per second, scale to zero, burst to thousands.

## Prerequisites
- Python 3.8+
- `pip install modal` (their CLI + SDK)
- `modal setup` to authenticate (browser-based)
- Free tier: $30/month compute credits (no credit card required)

## Pricing — Why It's Crazy Low

### GPU Rates (per-second billing)
| GPU | VRAM | $/sec | $/hr equiv |
|-----|------|-------|------------|
| T4 | 16GB | $0.000164 | ~$0.59 |
| A10G | 24GB | $0.000306 | ~$1.10 |
| A100 40GB | 40GB | $0.000594 | ~$2.14 |
| A100 80GB | 80GB | $0.000944 | ~$3.40 |
| H100 | 80GB | $0.001267 | ~$4.56 |

### Key Pricing Details
- **$30/month FREE** on Starter tier — enough for significant experimentation
- **Per-second billing** — only pay when your function runs, scales to zero
- **Regional multipliers:** 1.25x for US/EU/UK/Asia-Pacific, up to 2.5x elsewhere
- **Non-preemptible multiplier:** 3x (default is preemptible/spot)
- Combined US non-preemptible = 3.75x base rate
- **CPU:** $0.0000131/core/sec (~$0.047/hr)
- **Memory:** $0.00000163/MB/sec

### Plan Tiers
| Plan | Monthly | Credits | Containers | GPUs |
|------|---------|---------|------------|------|
| Starter (free) | $0 | $30 | 100 | 10 concurrent |
| Team | $250 | $100 | 1,000 | 50 concurrent |
| Enterprise | Custom | Custom | Custom | Custom |

### Cost Comparison vs Alternatives
- **vs fal.ai:** Modal is significantly cheaper for custom models (fal charges per-inference, Modal charges per-second of compute)
- **vs RunPod:** RunPod slightly cheaper per-GPU-hour but Modal has faster cold starts (2-4s vs variable)
- **vs Replicate:** Modal is ~3-5x cheaper for equivalent GPU time since Replicate adds margin
- **vs own RTX 4090:** Modal H100 at ~$4.56/hr beats owning for bursty workloads (no idle cost)

## Core Workflows

### Workflow 1: Deploy a GPU Function
**When to use:** Run any Python function on a GPU (inference, processing, generation)

```python
import modal

app = modal.App("my-app")

@app.function(gpu="A100", timeout=300)
def generate_video(prompt: str) -> bytes:
    # Your GPU code here — install deps in the image
    import torch
    # ...
    return video_bytes

# Call it
with app.run():
    result = generate_video.remote("a ninja in a cyberpunk city")
```

**Gotchas:**
- Container images are built declaratively — no Dockerfile needed
- First deploy builds the image (slow), subsequent deploys reuse cache
- Functions timeout after 300s by default, configurable up to 24hrs

### Workflow 2: Serve an API Endpoint
**When to use:** Deploy a persistent HTTP endpoint (LLM inference, image gen API)

```python
@app.function(gpu="A100")
@modal.web_endpoint(method="POST")
def infer(request: dict):
    prompt = request["prompt"]
    return {"result": run_model(prompt)}
```

Gives you a URL like `https://your-username--my-app-infer.modal.run`

### Workflow 3: Batch Processing
**When to use:** Process thousands of items in parallel

```python
@app.function(gpu="T4")
def process_one(item: str) -> dict:
    return {"item": item, "result": run_model(item)}

@app.local_entrypoint()
def main():
    items = ["a", "b", "c", ...]
    results = list(process_one.map(items))  # Parallel across GPUs!
```

`map()` auto-scales containers — 1000 items can run on 1000 GPUs simultaneously.

### Workflow 4: Custom Container Image
**When to use:** Need specific packages, model weights, CUDA libs

```python
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("torch", "transformers", "accelerate")
    .run_commands("apt-get install -y ffmpeg")
)

@app.function(image=image, gpu="A100")
def my_func():
    ...
```

### Workflow 5: Persistent Storage (Volumes)
**When to use:** Cache model weights, store outputs between runs

```python
vol = modal.Volume.from_name("my-models", create_if_missing=True)

@app.function(gpu="A100", volumes={"/models": vol})
def download_model():
    # Download once, cached in volume
    if not os.path.exists("/models/llama"):
        download_to("/models/llama")
```

## Command Reference
| Action | Command | Notes |
|--------|---------|-------|
| Install | `pip install modal` | Python SDK + CLI |
| Auth | `modal setup` | Browser-based login |
| Deploy | `modal deploy app.py` | Persistent deployment |
| Run once | `modal run app.py` | Execute & teardown |
| Serve dev | `modal serve app.py` | Hot-reload dev server |
| View logs | `modal app logs my-app` | Stream live logs |
| List apps | `modal app list` | See deployments |
| Stop app | `modal app stop my-app` | Teardown |
| Check usage | Dashboard at modal.com | No CLI for billing yet |

## Relevant Examples from Modal
- **Batched Whisper** — high-throughput transcription (relevant for Sharingan podcast pipeline)
- **Flux with torch.compile** — fast image generation (relevant for thumbnail pipeline)
- **LTX-Video** — video clip generation (relevant for B-roll generation)
- **vLLM OpenAI-compatible** — serve LLMs cheaply (relevant for Shadow Council cost reduction)
- **Chatterbox TTS** — speech generation (relevant for Glitch voice)
- **Sandboxes** — run untrusted code safely (relevant for Sage Mode agent execution)

## Integration Points — Ninja Ecosystem

### Content Pipeline (The Dojo)
- **Avatar generation:** Could replace fal.ai Kling calls — deploy Kling/CogVideo/LTX on Modal for ~60% cost savings
- **Thumbnail gen:** Run Flux on Modal A100 instead of paying per-image via Nano Banana
- **B-roll gen:** LTX-Video on Modal for AI-generated B-roll clips
- **TTS:** Self-host Kokoro or Chatterbox on Modal T4 (free tier might cover it)

### Glitch
- **Avatar rendering:** FasterLivePortrait on Modal GPU instead of tying up the Vengeance 4090
- **JoyVASA:** Audio-to-motion pipeline on Modal H100 for faster-than-realtime processing
- **Voice:** ElevenLabs alternative — self-host open TTS model on Modal

### Shadow Council / Sage Mode
- **LLM inference:** Deploy vLLM with Llama/Mistral on Modal for council agents instead of paying per-token API rates
- **Batch analysis:** Parallelize code review across GPUs

### Sharingan
- **Whisper transcription:** Batch-transcribe YouTube videos on Modal (their example does exactly this)
- **Training podcasts:** TTS generation on Modal GPU

## Limitations & Gaps
- **Vendor lock-in:** Everything uses Modal SDK — can't easily migrate to another cloud without rewriting deploy code
- **No raw SSH:** You can't SSH into a container and poke around (use `modal shell` for interactive sessions)
- **Preemption risk:** Cheaper "spot" instances can be interrupted (use non-preemptible for critical jobs, 3x cost)
- **Cold starts:** 2-4 seconds is fast but not zero — not suitable for sub-100ms latency requirements
- **Regional pricing:** Multipliers can sneak up — always check effective rate
- **[SINGLE SOURCE]** Some pricing details from third-party comparison articles, may be slightly outdated

## Tips & Best Practices
- Start with $30 free tier — it's enough to test all GPU types
- Use `modal.Volume` for model weights — avoids re-downloading on every cold start
- Use `gpu="T4"` for inference of smaller models — it's the cheapest and often fast enough
- `@modal.web_endpoint` gives you a public URL instantly — great for webhooks and API integration
- The `map()` pattern is incredibly powerful for batch — think "1000 GPUs for 10 seconds" instead of "1 GPU for 3 hours"
- Compare effective cost: Modal H100 at $4.56/hr * bursty usage often beats fal.ai per-inference pricing for high volume
- Their Sandbox feature could replace Docker for Sage Mode's untrusted code execution
