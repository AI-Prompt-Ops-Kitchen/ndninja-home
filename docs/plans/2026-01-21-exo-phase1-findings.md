# EXO Integration Phase 1 - Findings Report

**Date**: 2026-01-21
**Status**: **BLOCKED** - Hardware Incompatibility

## Executive Summary

EXO distributed inference system was successfully installed and cluster formation was verified on the Kage Bunshin infrastructure. However, **model inference is blocked due to hardware incompatibility**. EXO's MLX backend requires either:
- Apple Silicon (Mac) hardware, OR
- NVIDIA GPUs with CUDA support

The Kage Bunshin cluster lacks both, making EXO unsuitable for this infrastructure.

## Hardware Analysis

| Node | GPU | CUDA Support | EXO Compatible |
|------|-----|--------------|----------------|
| ndnlinuxsrv1 | Intel UHD Graphics 770 | ❌ | ❌ |
| ndnlinuxsrv2 | Intel UHD Graphics 770 | ❌ | ❌ |
| rog-flow-z13 | AMD Radeon (Strix Halo) | ❌ | ❌ |
| Vengeance | NVIDIA RTX 4090 | ✅ | ❌ (Windows) |

**Critical Issue**: EXO requires MLX (Apple Silicon) or CUDA. The cluster has:
- Intel iGPUs (no CUDA support)
- AMD iGPU (ROCm only, not MLX-compatible)
- Windows machine with NVIDIA GPU (EXO doesn't support Windows)

## What Was Accomplished

### Successful Steps
1. ✅ Python 3.13.7 verified on all nodes
2. ✅ EXO installed via source build (uv + git clone) on all 3 Linux nodes
3. ✅ Dashboard built (npm install && npm run build)
4. ✅ EXO processes started on all 3 nodes
5. ✅ Cluster formation verified (srv1 + srv2 discovered each other via libp2p)
6. ✅ API responding on port 52416 with model list

### Blocking Issue
When attempting to run inference:
```
RunnerFailed: libcublasLt.so.13: cannot open shared object file: No such file or directory
```

This CUDA library error confirms EXO requires NVIDIA GPU support, which the Intel/AMD iGPU nodes don't provide.

## Network Discovery Issue

**Additional finding**: rog-flow-z13 couldn't join the srv1+srv2 cluster because:
- srv1 and srv2 are on LAN (192.168.68.x)
- rog-flow-z13 is accessed via Tailscale (100.93.x.x)
- EXO uses mDNS for peer discovery, which doesn't work across network segments

## Recommendations

### Option 1: Alternative Distributed Inference Solutions
Consider frameworks designed for CPU or heterogeneous GPU hardware:

| Framework | CPU Support | AMD GPU | Multi-node |
|-----------|-------------|---------|------------|
| **vLLM** | ✅ | ✅ (ROCm) | ✅ |
| **llama.cpp** | ✅ | ✅ (Vulkan) | Limited |
| **Ray Serve + vLLM** | ✅ | ✅ | ✅ |
| **TensorRT-LLM** | ❌ | ❌ | ✅ (NVIDIA only) |

**Recommended**: vLLM with Ray Serve
- Supports CPU inference
- ROCm support for AMD GPUs
- Built-in distributed serving
- OpenAI-compatible API

### Option 2: Add NVIDIA GPU to Linux Servers
If dedicated GPU support is desired:
- Add an NVIDIA GPU to ndnlinuxsrv1 or ndnlinuxsrv2
- Install CUDA toolkit
- EXO would then work, but only on CUDA-capable nodes

### Option 3: Use Ollama Cluster
Continue using the existing Ollama setup:
- Ollama is already running on the cluster
- Supports CPU inference
- Works with AMD ROCm
- Proven stability

## Cleanup

To stop EXO processes:
```bash
# On ndnlinuxsrv1
pkill -f "uv run exo"

# On ndnlinuxsrv2
ssh ndnlinuxsrv2 'pkill -f "uv run exo"'

# On rog-flow-z13
ssh -p 2222 rog-flow-z13 'pkill -f "uv run exo"'
```

## Conclusion

EXO is an impressive distributed inference framework, but it's **not compatible with the Kage Bunshin cluster's hardware**. For distributed LLM inference on this infrastructure, **vLLM with Ray Serve** is the recommended alternative.

---

**Next Steps**:
1. Cleanup EXO processes
2. Evaluate vLLM + Ray Serve as an alternative
3. Update Kage Bunshin project plan with findings
