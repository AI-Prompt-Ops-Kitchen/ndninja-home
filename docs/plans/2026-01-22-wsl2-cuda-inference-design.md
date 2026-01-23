# Vengeance LLM Inference Server

**Date**: 2026-01-22
**Updated**: 2026-01-23
**Status**: ✅ Completed
**Target**: Vengeance (RTX 4090)

## Overview

Set up Vengeance as a standalone LLM inference server accessible from the Kage Bunshin cluster via Tailscale.

**Final Solution**: Ollama on native Windows (not WSL2 + vLLM)

## What We Learned

### WSL2 + vLLM Approach (Attempted)

**What worked:**
- WSL2 with CUDA detected RTX 4090 correctly (`nvidia-smi` worked)
- Docker + NVIDIA Container Toolkit installed successfully
- vLLM ran small models (Qwen2.5-7B) without issues
- Port forwarding from Windows to WSL2 worked

**What failed:**
- Larger models (32B/72B) crashed with "Engine core initialization failed"
- CUDA graph compilation issues in WSL2 environment
- Even with `--enforce-eager` flag, containers were unstable
- Docker log buffering in WSL2 made debugging difficult

**Root cause:** vLLM's CUDA graph optimization doesn't work reliably in WSL2 for large models.

### Ollama on Native Windows (Success)

Ollama running directly on Windows works perfectly with all model sizes:
- No WSL2 layer = no CUDA graph issues
- Native Windows CUDA driver = full performance
- Auto-starts as Windows service
- Already had models pre-installed

## Architecture (Final)

```
┌─────────────────────────────────────────────────────────────┐
│                     VENGEANCE (Windows 11)                   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                 Ollama (Native Windows)              │    │
│  │                      :11434                          │    │
│  │  ┌─────────────────────────────────────────────┐    │    │
│  │  │  Models: qwen2.5:72b, deepseek-r1:32b,      │    │    │
│  │  │          deepseek-coder:33b, qwen2.5:32b    │    │    │
│  │  └─────────────────────────────────────────────┘    │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                         │                                    │
│                         ▼                                    │
│                ┌───────────────┐                            │
│                │  RTX 4090     │                            │
│                │  24GB VRAM    │                            │
│                └───────────────┘                            │
└─────────────────────────┬───────────────────────────────────┘
                          │ Tailscale (100.98.226.75:11434)
                          ▼
              ┌─────────────────────┐
              │  Kage Bunshin       │
              │  Cluster / Clients  │
              └─────────────────────┘
```

## Configuration

### Prerequisites

- Windows 11 with latest NVIDIA driver
- Ollama for Windows installed
- Tailscale connected

### Environment Variable

Set `OLLAMA_HOST` to listen on all interfaces:

```
OLLAMA_HOST=0.0.0.0:11434
```

This is configured as a system environment variable on Vengeance.

### Auto-Start

Ollama runs as a Windows service and starts automatically on boot.

## Available Models

| Model | Size | Use Case |
|-------|------|----------|
| qwen2.5:72b | 47GB | Production quality reasoning |
| deepseek-r1:32b | 19GB | Reasoning/thinking model |
| deepseek-coder:33b | 19GB | Code generation |
| qwen2.5:32b | 19GB | General purpose |
| qwen2.5:3b | 2GB | Fast responses |

## API Access

### From Cluster (via Tailscale)

**OpenAI-compatible endpoint:**
```bash
curl http://100.98.226.75:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen2.5:72b", "messages": [{"role": "user", "content": "Hello"}]}'
```

**Native Ollama API:**
```bash
curl http://100.98.226.75:11434/api/generate \
  -d '{"model": "qwen2.5:72b", "prompt": "Hello", "stream": false}'
```

**List models:**
```bash
curl http://100.98.226.75:11434/v1/models
```

## Validation Results

- [x] RTX 4090 detected (22.8 GiB available)
- [x] Ollama starts without errors
- [x] 72B model loads and responds correctly
- [x] Remote access from srv1 works via Tailscale
- [x] OpenAI-compatible API works

## Lessons Learned

1. **WSL2 + vLLM is unreliable for large models** - CUDA graph compilation fails
2. **Native Windows apps work better for GPU** - No virtualization overhead
3. **Ollama is simpler** - No Docker, no port forwarding, just works
4. **Keep Windows for gaming PCs** - No need to dual-boot or replace OS

## Next Steps

- **Load Balancing**: Add Ollama endpoint to cluster load balancer
- **Monitoring**: Track GPU utilization and inference latency
- **Model Updates**: Pull newer model versions as released
