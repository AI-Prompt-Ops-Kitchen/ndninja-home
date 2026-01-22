# WSL2 + CUDA Inference Server Design

**Date**: 2026-01-22
**Status**: Approved
**Target**: Vengeance (RTX 4090)

## Overview

Set up Vengeance as a standalone LLM inference server using WSL2 with CUDA, accessible from the Kage Bunshin cluster via Tailscale.

**Why WSL2:**
- No OS replacement needed (keep Windows)
- Full CUDA support via NVIDIA WSL driver
- Near-native GPU performance

**Why vLLM (not EXO):**
- Better standalone server support
- OpenAI-compatible API out of the box
- No cluster discovery complexity
- More mature production deployment

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     VENGEANCE (Windows 11)                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    WSL2 (Ubuntu 22.04)               │    │
│  │  ┌─────────────┐    ┌─────────────┐                 │    │
│  │  │   vLLM      │───▶│  CUDA 12.x  │                 │    │
│  │  │  Server     │    │  Libraries  │                 │    │
│  │  │  :8000      │    └──────┬──────┘                 │    │
│  │  └──────┬──────┘           │                        │    │
│  └─────────┼──────────────────┼────────────────────────┘    │
│            │                  ▼                              │
│            │         ┌───────────────┐                      │
│            │         │  RTX 4090     │                      │
│            │         │  24GB VRAM    │                      │
│            │         └───────────────┘                      │
└────────────┼────────────────────────────────────────────────┘
             │ Tailscale (100.x.x.x:8000)
             ▼
┌─────────────────────┐
│  Kage Bunshin       │
│  Cluster / Clients  │
└─────────────────────┘
```

## Prerequisites

- Windows 11 (or Windows 10 21H2+)
- Latest NVIDIA driver (545+)
- WSL2 enabled
- ~50GB free disk space

## Implementation Steps

### Step 1: WSL2 Setup (Windows PowerShell)

```powershell
# Enable WSL2 and install Ubuntu
wsl --install -d Ubuntu-22.04

# Restart if prompted, then set as default
wsl --set-default Ubuntu-22.04
```

### Step 2: CUDA Toolkit (WSL2 Ubuntu)

```bash
# NVIDIA WSL-CUDA package (uses Windows driver)
wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt update
sudo apt install -y cuda-toolkit-12-4

# Verify GPU access
nvidia-smi
```

### Step 3: vLLM Installation

```bash
# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip

# Create venv and install vLLM
python3.11 -m venv ~/vllm-env
source ~/vllm-env/bin/activate
pip install vllm
```

### Step 4: Start Server

```bash
# Run with Llama 3.1 8B for testing
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-3.1-8B-Instruct \
  --host 0.0.0.0 \
  --port 8000
```

## Testing & Validation

### Local Test (WSL2)

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.1-8B-Instruct",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 50
  }'
```

### Remote Test (from srv1)

```bash
curl http://<vengeance-tailscale-ip>:8000/v1/models

curl http://<vengeance-tailscale-ip>:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "meta-llama/Llama-3.1-8B-Instruct", "messages": [{"role": "user", "content": "Hello!"}]}'
```

### Success Criteria

- [ ] `nvidia-smi` shows RTX 4090 in WSL2
- [ ] vLLM starts without CUDA errors
- [ ] Local curl returns valid response
- [ ] Remote curl from srv1 works via Tailscale
- [ ] GPU utilization visible during inference

## Model Recommendations

For 24GB VRAM (RTX 4090):

| Model | Size | VRAM Usage | Use Case |
|-------|------|------------|----------|
| Llama-3.1-8B-Instruct | 8B | ~8GB | Testing, fast responses |
| Llama-3.1-70B-Instruct | 70B | ~20GB (4-bit) | Production quality |
| Qwen2.5-72B-Instruct | 72B | ~22GB (4-bit) | Coding, reasoning |
| DeepSeek-Coder-33B | 33B | ~18GB | Code generation |

### Running Quantized Models

```bash
# 70B with AWQ 4-bit quantization
python -m vllm.entrypoints.openai.api_server \
  --model TheBloke/Llama-2-70B-Chat-AWQ \
  --quantization awq \
  --host 0.0.0.0 --port 8000
```

## Next Steps

After Phase A is validated:
- **Phase B**: Deploy vLLM on Linux cluster (srv1/srv2) for CPU inference
- **Load Balancing**: Add nginx/traefik to route requests across GPU and CPU endpoints
- **Monitoring**: Add Prometheus metrics for inference performance
