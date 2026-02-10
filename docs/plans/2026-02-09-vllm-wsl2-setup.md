# vLLM on WSL2 — Successful Setup

**Date**: 2026-02-09
**Status**: ✅ Completed
**Target**: Vengeance (RTX 4090, 24GB VRAM)
**Supersedes**: Partial findings in `2026-01-22-wsl2-cuda-inference-design.md`

## Overview

vLLM 0.15.1 running in WSL2 on the Vengeance workstation, serving Qwen2.5-Coder-32B-Instruct-AWQ via an OpenAI-compatible API. This revisits the earlier failed WSL2 + vLLM attempt and documents the parameter combination that makes it work.

## Why Revisit vLLM?

The January attempt concluded that vLLM in WSL2 was unreliable for large models. The root cause was actually a combination of:
1. Using `--quantization awq` instead of the faster `awq_marlin` kernel
2. Not using `--enforce-eager` (CUDA graph compilation consumed too much VRAM)
3. Setting `--max-model-len` too high for the available memory budget

With the correct parameters, the 32B AWQ model runs stably in WSL2.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                   VENGEANCE (Windows 11)                      │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                  WSL2 (Ubuntu)                          │  │
│  │                                                        │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │  vLLM 0.15.1 (OpenAI-compatible API)             │  │  │
│  │  │  Model: Qwen2.5-Coder-32B-Instruct-AWQ          │  │  │
│  │  │  Quantization: awq_marlin                        │  │  │
│  │  │  Port: 8080                                      │  │  │
│  │  └──────────────────────┬───────────────────────────┘  │  │
│  │                         │ CUDA Passthrough              │  │
│  └─────────────────────────┼──────────────────────────────┘  │
│                            ▼                                  │
│                   ┌───────────────┐                           │
│                   │  RTX 4090     │                           │
│                   │  24GB VRAM    │                           │
│                   │  (23.8GB used)│                           │
│                   └───────────────┘                           │
└──────────────────────────┬───────────────────────────────────┘
                           │ localhost:8080 (Windows + WSL2)
                           │ Tailscale for remote access
                           ▼
                ┌─────────────────────┐
                │  Kage Bunshin       │
                │  Cluster / Clients  │
                └─────────────────────┘
```

## Prerequisites

- Windows 11 with WSL2 (Ubuntu)
- NVIDIA driver 591.86+ (CUDA passthrough to WSL2)
- Python 3.12 in WSL2
- ~22GB free VRAM (ComfyUI must be closed)

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

## vLLM vs Ollama

Both are now available on Vengeance. Use the right tool for the job:

| | vLLM (WSL2, port 8080) | Ollama (Windows, port 11434) |
|---|---|---|
| **Best for** | High-throughput batch inference, code generation | Interactive chat, quick queries |
| **API** | OpenAI-compatible only | OpenAI-compatible + native Ollama API |
| **Concurrency** | Continuous batching, handles many requests efficiently | Single request at a time |
| **Startup** | ~50 seconds | Instant (Windows service) |
| **Model management** | HuggingFace cache, manual | `ollama pull`, automatic |
| **Context window** | 2048 tokens (limited by VRAM) | Varies by model |
| **VRAM sharing** | Cannot run simultaneously with Ollama/ComfyUI | Cannot run simultaneously with vLLM/ComfyUI |

**Important**: Only ONE GPU-intensive application can run at a time on the RTX 4090. Close ComfyUI and Ollama before starting vLLM, and vice versa.

## Troubleshooting

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

- [ ] Create a startup script to automate vLLM launch
- [ ] Add Tailscale endpoint configuration for remote cluster access
- [ ] Benchmark throughput: tokens/sec for various prompt lengths
- [ ] Integrate with Kage Bunshin smart router for automatic model selection
- [ ] Evaluate if `--max-model-len` can be increased by stopping the display server
