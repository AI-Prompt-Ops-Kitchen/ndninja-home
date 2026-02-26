---
name: modal-serverless-gpu
domain: Cloud/GPU
level: 3-tomoe
description: Serverless GPU cloud platform — deploy AI workloads via Python SDK with sub-second cold starts, elastic scaling to thousands of GPUs, and pay-per-second billing. $30/mo free credits.
sources:
  - type: web
    title: "Modal: High-performance AI infrastructure"
    url: "https://modal.com/"
    date: "2026-02-23"
    confidence: high
  - type: web
    title: "Modal Pricing"
    url: "https://modal.com/pricing"
    date: "2026-02-23"
    confidence: high
  - type: web
    title: "Top Serverless GPU Clouds for 2026 (RunPod comparison)"
    url: "https://www.runpod.io/articles/guides/top-serverless-gpu-clouds"
    date: "2026-02-23"
    confidence: medium
  - type: web
    title: "Best Serverless GPU Platforms for AI in 2026 (Koyeb)"
    url: "https://www.koyeb.com/blog/best-serverless-gpu-platforms-for-ai-apps-and-inference-in-2026"
    date: "2026-02-23"
    confidence: high
  - type: web
    title: "Modal Whisper Deployment Tutorial"
    url: "https://modal.com/blog/how-to-deploy-whisper"
    date: "2026-02-23"
    confidence: high
  - type: web
    title: "Modal Batched Whisper Example"
    url: "https://modal.com/docs/examples/batched_whisper"
    date: "2026-02-23"
    confidence: high
  - type: web
    title: "Modal Secrets & Environments Docs"
    url: "https://modal.com/docs/guide/secrets"
    date: "2026-02-23"
    confidence: high
sources_count: 7
last_updated: 2026-02-23
can_do_from_cli: true
---

# Modal — Serverless GPU Cloud

## Mental Model
Modal is a serverless GPU cloud where you write Python code, not YAML. Decorate functions with `@app.function(gpu="A100")`, push, and Modal handles containers, GPUs, scaling, and teardown. Like AWS Lambda for GPU workloads — pay per second, scale to zero, burst to thousands.

## Prerequisites
- Python 3.8+
- `pip install modal` (CLI + SDK)
- `modal setup` (browser-based auth)
- Free tier: $30/month compute credits (no credit card)

## GPU Pricing (Feb 2026)

| GPU | VRAM | $/sec | $/hr |
|-----|------|-------|------|
| T4 | 16GB | $0.000164 | $0.59 |
| L4 | 24GB | $0.000222 | $0.80 |
| A10G | 24GB | $0.000306 | $1.10 |
| L40S | 48GB | $0.000542 | $1.95 |
| A100 40GB | 40GB | $0.000583 | $2.10 |
| A100 80GB | 80GB | $0.000694 | $2.50 |
| H100 | 80GB | $0.001097 | $3.95 |
| H200 | 141GB | $0.001261 | $4.54 |
| B200 | 192GB | $0.001736 | $6.25 |

**Multipliers (stack these):**
- Regional: 1.25x (US/EU/UK/APAC), up to 2.5x elsewhere
- Non-preemptible: 3x (default is preemptible/spot)
- US non-preemptible effective = **3.75x** base rate

**Other compute:** CPU $0.047/hr/core, Memory $0.008/GiB/hr

### Plan Tiers
| Plan | Monthly | Credits | Containers | GPUs |
|------|---------|---------|------------|------|
| Starter (free) | $0 | $30 | 100 | 10 concurrent |
| Team | $250 | $100 | 1,000 | 50 concurrent |
| Enterprise | Custom | Custom | Custom | Custom |

## Cross-Platform Pricing Comparison ($/hr, base rates)

| GPU | Modal | RunPod | fal.ai | Replicate | Koyeb |
|-----|-------|--------|--------|-----------|-------|
| T4 | $0.59 | $0.44 | — | — | — |
| L40S | $1.95 | $1.90 | — | $3.51 | $1.55 |
| A100 80GB | $2.50 | $2.72 | $0.99* | $5.04 | $2.00 |
| H100 | $3.95 | $4.18 | $1.99* | $5.49 | $3.30 |

*fal.ai rates are "starting points" — actual pricing requires sales contact.

**Verdict:** Modal is middle-of-road on raw $/hr but wins on DX (pure Python, no Docker, instant deploys). RunPod cheapest for raw GPU time. Replicate is 2x more expensive but zero-config for popular models. fal.ai is cheapest if you negotiate but vendor-locked.

## Core Workflows

### 1. Deploy a GPU Function
```python
import modal

app = modal.App("my-app")

@app.function(gpu="A100", timeout=300)
def generate_video(prompt: str) -> bytes:
    import torch
    # GPU code here
    return video_bytes

with app.run():
    result = generate_video.remote("a ninja in a cyberpunk city")
```

### 2. Serve an API Endpoint
```python
@app.function(gpu="A100")
@modal.web_endpoint(method="POST")
def infer(request: dict):
    return {"result": run_model(request["prompt"])}
# URL: https://your-username--my-app-infer.modal.run
```

### 3. Batch Processing (the killer feature)
```python
@app.function(gpu="T4")
def process_one(item: str) -> dict:
    return {"item": item, "result": run_model(item)}

@app.local_entrypoint()
def main():
    items = ["a", "b", "c", ...]
    results = list(process_one.map(items))  # 1000 items = 1000 GPUs
```

### 4. Custom Container Image
```python
image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("torch", "transformers", "accelerate")
    .run_commands("apt-get install -y ffmpeg")
)

@app.function(image=image, gpu="A100")
def my_func():
    ...
```

### 5. Volumes (Persistent Storage)
```python
vol = modal.Volume.from_name("my-models", create_if_missing=True)

@app.function(gpu="A100", volumes={"/models": vol})
def download_model():
    if not os.path.exists("/models/llama"):
        download_to("/models/llama")
```

### 6. Secrets Management
```python
# Create secrets at modal.com/secrets (encrypted at rest, injected at runtime)
@app.function(
    gpu="T4",
    secrets=[modal.Secret.from_name("my-api-keys")]
)
def call_api():
    import os
    key = os.environ["API_KEY"]  # Injected as env vars
```

**Environments:** Use `modal.config.default_environment = "dev"` or `--env dev` CLI flag to separate dev/prod secrets, volumes, and deployments.

## Complete Example: Whisper Transcription Service

57-minute podcast transcribed in 2m14s for ~$0.11.

```python
import modal

app = modal.App("whisper-transcriber")

image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("ffmpeg")
    .pip_install("openai-whisper", "librosa", "torch", "numpy")
)

vol = modal.Volume.from_name("whisper-cache", create_if_missing=True)

@app.cls(image=image, gpu="H100", volumes={"/cache": vol})
class WhisperTranscriber:
    @modal.enter()
    def load_model(self):
        import whisper
        self.model = whisper.load_model(
            "large-v3", download_root="/cache/models"
        )

    @modal.method()
    def transcribe(self, audio_bytes: bytes) -> str:
        import tempfile, librosa, numpy as np
        with tempfile.NamedTemporaryFile(suffix=".wav") as f:
            f.write(audio_bytes)
            f.flush()
            audio, sr = librosa.load(f.name, sr=16000)
        result = self.model.transcribe(audio)
        return result["text"]

@app.local_entrypoint()
def main(url: str = "https://example.com/podcast.mp3"):
    import urllib.request
    data = urllib.request.urlopen(url).read()
    transcriber = WhisperTranscriber()
    text = transcriber.transcribe.remote(data)
    print(text)
```

```bash
# Run it
modal run whisper_app.py --url "https://example.com/audio.mp3"

# Deploy as persistent service
modal deploy whisper_app.py
```

### Batched Whisper (High-Throughput)
For bulk transcription, use `@modal.batched` to auto-batch requests:
```python
@app.cls(image=image, gpu="A10G")
class BatchWhisper:
    @modal.enter()
    def load(self):
        self.model = whisper.load_model("large-v3", download_root="/cache")

    @modal.batched(max_batch_size=64, wait_ms=1000)
    def transcribe(self, audio_samples: list[bytes]) -> list[str]:
        # Process up to 64 audio clips in one GPU pass
        return [self.model.transcribe(s)["text"] for s in audio_samples]
```

## Command Reference
| Action | Command |
|--------|---------|
| Install | `pip install modal` |
| Auth | `modal setup` |
| Deploy | `modal deploy app.py` |
| Run once | `modal run app.py` |
| Dev server | `modal serve app.py` (hot-reload) |
| Logs | `modal app logs my-app` |
| List apps | `modal app list` |
| Stop | `modal app stop my-app` |
| Shell | `modal shell --gpu A100` (interactive) |
| Volume ls | `modal volume ls my-models` |
| Env switch | `modal run app.py --env prod` |

## GPU Selection Guide
| Workload | Recommended GPU | Why |
|----------|----------------|-----|
| Small model inference (SDXL, Whisper) | **T4** ($0.59/hr) | Cheapest, 16GB enough |
| Medium models (Flux, 7B LLMs) | **L4** ($0.80/hr) | Good perf/cost, 24GB |
| Large models (13B+, batch inference) | **A100 40GB** ($2.10/hr) | Fast memory bandwidth |
| Huge models (70B, video gen) | **A100 80GB** ($2.50/hr) | Need the VRAM |
| Maximum speed (production APIs) | **H100** ($3.95/hr) | 3x A100 throughput |
| Frontier models (405B) | **H200** ($4.54/hr) | 141GB HBM3e |

## Integration Points — Ninja Ecosystem

### The Dojo (Content Pipeline)
- **Avatar gen:** Deploy Kling/CogVideo on Modal for ~60% cost savings vs fal.ai
- **Thumbnails:** Flux on Modal A100 instead of per-image Nano Banana pricing
- **B-roll:** LTX-Video on Modal for AI-generated B-roll clips
- **TTS:** Self-host Kokoro on Modal T4 (free $30 tier might cover it)

### Glitch
- **Avatar rendering:** FasterLivePortrait on Modal instead of tying up Vengeance 4090

### Sharingan
- **Whisper:** Batch-transcribe YouTube videos; **Shadow Council:** vLLM on Modal vs per-token APIs

## Limitations
- **Vendor lock-in:** Modal SDK everywhere — rewrite needed to migrate
- **No raw SSH:** Use `modal shell` for interactive sessions
- **Preemption risk:** Spot instances can be interrupted (3x cost for guaranteed)
- **Cold starts:** 2-4s is fast but not sub-100ms
- **Multiplier stacking:** US non-preemptible = 3.75x base rate — always check effective cost
- **Volume limits:** 100 GiB default, request increase for large model caches

## Tips & Best Practices
- **$30 free tier** covers ~50 hrs of T4 or ~12 hrs of A100 — plenty to prototype
- **Always use Volumes** for model weights — avoids re-downloading on cold starts
- **Start with T4** — upgrade GPU only if you need it
- **`map()` is the superpower** — think "1000 GPUs for 10 seconds" not "1 GPU for 3 hours"
- **Use `@modal.enter()`** for model loading — runs once per container, not per request
- **`@modal.batched()`** for high-throughput — auto-batches requests for GPU efficiency
- **Secrets over env vars** — encrypted at rest, scoped per environment
- **`modal serve` for dev** — hot-reload saves round-trips vs full `modal deploy`
- **`--env` flag** — keep dev and prod deployments separate
