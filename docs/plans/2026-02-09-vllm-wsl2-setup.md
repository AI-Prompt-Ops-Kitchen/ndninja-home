# Vengeance LLM Inference — Ollama (Primary) + vLLM (Reference)

**Date**: 2026-02-09
**Updated**: 2026-02-09
**Status**: ✅ Completed
**Target**: Vengeance (RTX 4090, 24GB VRAM)

## Overview

Vengeance serves LLM inference via **Ollama on native Windows** as the primary solution. Ollama loads models on demand and automatically unloads them after 5 minutes of inactivity, freeing VRAM for other GPU workloads (ComfyUI, etc.).

vLLM 0.15.1 in WSL2 was also validated as working (correcting earlier findings) and is documented below as a reference for batch inference scenarios.

## Decision: Why Ollama over vLLM

| Factor | Ollama (chosen) | vLLM |
|--------|-----------------|------|
| **VRAM sharing** | On-demand load/unload — GPU free when idle | Holds 23.8 GB permanently |
| **Startup** | Instant (Windows service) | ~50 seconds cold start |
| **Multi-model** | 5 models available, swaps automatically | Single model per instance |
| **Coexistence** | Works alongside ComfyUI (when idle) | Cannot coexist with ComfyUI |
| **Concurrency** | Single request at a time | Continuous batching |
| **Best for** | Interactive use, shared GPU | High-throughput batch workloads |

The RTX 4090 is shared between LLM inference, ComfyUI image/video generation, and other GPU tasks. vLLM's always-on VRAM usage makes it impractical for this shared-GPU workflow.

## Architecture (Primary — Ollama)

```
┌─────────────────────────────────────────────────────────────┐
│                     VENGEANCE (Windows 11)                    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           Ollama (Native Windows)                    │    │
│  │           :11434 (OLLAMA_HOST=0.0.0.0)              │    │
│  │           OLLAMA_KEEP_ALIVE=5m                       │    │
│  │                                                      │    │
│  │  Models (loaded on demand, unloaded after 5m idle):  │    │
│  │  ┌─────────────────────────────────────────────┐    │    │
│  │  │  qwen2.5:72b (47GB)  deepseek-r1:32b (19GB) │    │    │
│  │  │  deepseek-coder:33b (18GB)  qwen2.5:32b (19GB)│   │    │
│  │  │  qwen2.5:3b (1.9GB)                          │    │    │
│  │  └─────────────────────────────────────────────┘    │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                         │                                    │
│                         ▼                                    │
│                ┌───────────────┐                            │
│                │  RTX 4090     │  VRAM idle: ~1.9 GB        │
│                │  24GB VRAM    │  VRAM with model: varies   │
│                └───────────────┘                            │
└─────────────────────────┬───────────────────────────────────┘
                          │ Tailscale (100.98.226.75:11434)
                          │ localhost:11434
                          ▼
              ┌─────────────────────┐
              │  Kage Bunshin       │
              │  Cluster / Clients  │
              └─────────────────────┘
```

## Ollama Setup

### Prerequisites

- Windows 11 with latest NVIDIA driver
- Ollama for Windows installed (`C:\Users\Steam\AppData\Local\Programs\Ollama\`)
- Tailscale connected

### Environment Variables

Set as system/user environment variables:

```
OLLAMA_HOST=0.0.0.0:11434     # Listen on all interfaces (system var)
OLLAMA_KEEP_ALIVE=5m           # Unload models after 5 min idle (user var)
```

### Starting Ollama

```bash
# Launch via tray app (recommended — manages server lifecycle)
start "" "C:\Users\Steam\AppData\Local\Programs\Ollama\ollama app.exe"
```

### Available Models

| Model | Size | Use Case |
|-------|------|----------|
| qwen2.5:72b | 47 GB | Production quality reasoning |
| deepseek-r1:32b | 19 GB | Reasoning/thinking model |
| deepseek-coder:33b | 18 GB | Code generation |
| qwen2.5:32b | 19 GB | General purpose |
| qwen2.5:3b | 1.9 GB | Fast responses |

### API Access

**OpenAI-compatible (from anywhere):**
```bash
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen2.5:3b", "messages": [{"role": "user", "content": "Hello"}]}'
```

**Native Ollama API:**
```bash
curl http://localhost:11434/api/generate \
  -d '{"model": "qwen2.5:3b", "prompt": "Hello", "stream": false}'
```

**From cluster (via Tailscale):**
```bash
curl http://100.98.226.75:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen2.5:72b", "messages": [{"role": "user", "content": "Hello"}]}'
```

**Check loaded models:**
```bash
curl http://localhost:11434/api/ps
```

**List available models:**
```bash
ollama list
```

### VRAM Behavior

```
Idle (no model loaded):     ~1.9 GB  (display server only)
With qwen2.5:3b loaded:    ~4.9 GB  (auto-unloads after 5 min)
With qwen2.5:32b loaded:   ~21 GB   (auto-unloads after 5 min)
With qwen2.5:72b loaded:   ~24 GB   (auto-unloads after 5 min)
```

Models load on first request (~5-15 seconds depending on size) and free VRAM automatically after 5 minutes of inactivity.

### Validation Results

- [x] Ollama v0.13.5 running on native Windows
- [x] RTX 4090 detected (24 GB VRAM)
- [x] `OLLAMA_KEEP_ALIVE=5m` confirmed working (models show `expires_at` timestamp)
- [x] Models load on demand and unload after idle timeout
- [x] OpenAI-compatible API responds correctly
- [x] Accessible from cluster via Tailscale at `100.98.226.75:11434`
- [x] VRAM returns to ~1.9 GB after model unload

---

## vLLM Setup (Reference — For Batch Workloads)

> **Note**: vLLM holds the full model in VRAM permanently (~23.8 GB for the 32B model).
> Only use this when you need high-throughput continuous batching and can dedicate the GPU.

### Architecture (vLLM)

```
┌──────────────────────────────────────────────────────────────┐
│                   VENGEANCE (Windows 11)                      │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  WSL2 (Ubuntu) → vLLM 0.15.1 → :8080                  │  │
│  │  Model: Qwen2.5-Coder-32B-Instruct-AWQ (awq_marlin)   │  │
│  └────────────────────────┬───────────────────────────────┘  │
│                           │ CUDA Passthrough                  │
│                  RTX 4090 (23.8 GB / 24 GB used)             │
└──────────────────────────────────────────────────────────────┘
```

### Prerequisites

- Windows 11 with WSL2 (Ubuntu)
- NVIDIA driver 591.86+ (CUDA passthrough to WSL2)
- Python 3.12 in WSL2
- ~22GB free VRAM (ComfyUI and Ollama must be closed)

## Installation Steps

### 1. Verify CUDA passthrough

```bash
wsl -d Ubuntu -- nvidia-smi
```

Expected: RTX 4090 visible with CUDA 13.1.

### 2. Create Python venv

```bash
# Install python3.12-venv if needed (run as root since sudo may need password)
wsl -d Ubuntu -u root -- apt-get install -y python3.12-venv

# Create venv
wsl -d Ubuntu -- python3 -m venv /home/steam/vllm-env
```

### 3. Install vLLM

```bash
wsl -d Ubuntu -- bash -c "source /home/steam/vllm-env/bin/activate && pip install vllm"
```

This installs vLLM 0.15.1 with PyTorch 2.9.1 and all CUDA dependencies (~3.5GB).

### 4. Clear bytecode cache (if upgrading)

If you see `ValueError: bad marshal data (invalid reference)` on first run:

```bash
wsl -d Ubuntu -- bash -c "find /home/steam/vllm-env -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; find /home/steam/vllm-env -name '*.pyc' -delete 2>/dev/null"
```

### 5. Start the server

```bash
wsl -d Ubuntu -- bash -c "source /home/steam/vllm-env/bin/activate && python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-Coder-32B-Instruct-AWQ \
  --quantization awq_marlin \
  --host 0.0.0.0 \
  --port 8080 \
  --gpu-memory-utilization 0.92 \
  --max-model-len 2048 \
  --enforce-eager"
```

Startup takes ~50 seconds. The model downloads (~18GB) on first run and is cached at `~/.cache/huggingface/`.

## Critical Parameters

| Parameter | Value | Why |
|-----------|-------|-----|
| `--quantization awq_marlin` | awq_marlin | Faster inference kernel than plain `awq`, lower memory overhead |
| `--enforce-eager` | enabled | **Skips CUDA graph compilation**, saves ~2-4 GB VRAM. Without this, the 32B model OOMs |
| `--max-model-len 2048` | 2048 | Limits KV cache allocation. 4096 requires ~1GB KV cache which doesn't fit after model loading |
| `--gpu-memory-utilization 0.92` | 0.92 | Uses 92% of VRAM for model + KV cache (default 0.9 is too conservative for this model) |

### What happens without these parameters

| Missing Parameter | Failure Mode |
|-------------------|-------------|
| No `awq_marlin` | Works but slower. vLLM logs suggest switching to awq_marlin |
| No `--enforce-eager` | CUDA graph compilation uses ~2-4GB extra VRAM → OOM |
| `--max-model-len 4096` | Needs 1.0 GiB KV cache, only 0.14 GiB available → `ValueError` |
| `--gpu-memory-utilization 0.85` | Wastes ~1.7GB VRAM, may not leave enough for KV cache |

## API Endpoints

The server exposes an OpenAI-compatible API:

### Chat Completions

```bash
curl -s http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-Coder-32B-Instruct-AWQ",
    "messages": [{"role": "user", "content": "Write a Python function to check if a number is prime."}],
    "max_tokens": 256,
    "temperature": 0.7
  }'
```

### Text Completions

```bash
curl -s http://localhost:8080/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-Coder-32B-Instruct-AWQ",
    "prompt": "def fibonacci(n):",
    "max_tokens": 128
  }'
```

### List Models

```bash
curl -s http://localhost:8080/v1/models
```

### Health Check

```bash
curl -s http://localhost:8080/health
```

## VRAM Budget

```
Total VRAM:                    24,564 MiB (24.0 GB)
├─ Display server (Xwayland):   2,275 MiB ( 2.2 GB)
├─ Model weights (AWQ 4-bit):  18,140 MiB (17.7 GB)
├─ KV cache + runtime:          3,407 MiB ( 3.3 GB)
└─ Free:                          317 MiB ( 0.3 GB)
                               ─────────
Used:                          23,822 MiB (23.3 GB) → 97% utilization
```

## Validation Results

- [x] RTX 4090 detected via CUDA passthrough in WSL2
- [x] vLLM 0.15.1 installed with PyTorch 2.9.1
- [x] Qwen2.5-Coder-32B-Instruct-AWQ loaded successfully (18.14 GiB)
- [x] Server responds on `http://localhost:8080` from both WSL2 and Windows
- [x] Chat completions endpoint returns correct structured responses
- [x] 159 tokens generated for a coding prompt (prime number function)

## Troubleshooting

### Ollama

| Issue | Solution |
|-------|----------|
| Ollama not responding | Launch `"ollama app.exe"` from Programs\Ollama |
| Model slow to load | First request loads model into VRAM (~5-15s). Subsequent requests are fast. |
| VRAM not freeing | Check `curl localhost:11434/api/ps` — model unloads after `OLLAMA_KEEP_ALIVE` (5m) |
| Can't connect from cluster | Ensure `OLLAMA_HOST=0.0.0.0:11434` is set as system env var |
| Out of VRAM | Another GPU app (ComfyUI) may be running. Close it first. |

### vLLM

| Issue | Solution |
|-------|----------|
| `ValueError: bad marshal data` | Clear `__pycache__` dirs in venv (see step 4) |
| OOM / KV cache too small | Ensure `--enforce-eager`, `--max-model-len 2048`, `--gpu-memory-utilization 0.92` |
| `awq_marlin` not used | Explicitly pass `--quantization awq_marlin` |
| WSL2 `pin_memory=False` warning | Normal for WSL2, does not affect correctness (slight perf impact) |
| Port not accessible from Windows | Use `--host 0.0.0.0`, WSL2 auto-forwards to Windows localhost |
| CUDA not found in WSL2 | Update Windows NVIDIA driver to 591.86+ |
| `sudo` requires password in WSL2 | Use `wsl -d Ubuntu -u root -- <command>` instead |

## Next Steps

- [ ] Integrate Ollama endpoint with Kage Bunshin smart router for automatic model selection
- [ ] Benchmark Ollama throughput: tokens/sec for various models and prompt lengths
- [ ] Evaluate pulling newer models as they release (`ollama pull`)
- [ ] Monitor GPU utilization and inference latency over time
