# EXO Integration Phase 1 POC Design

**Date:** 2026-01-21
**Status:** Approved
**Project:** Kage Bunshin no Jutsu - EXO Integration

## Overview

Integrate EXO distributed LLM inference framework alongside existing Ollama infrastructure to achieve faster inference through pipeline parallelism across a 3-node Linux cluster.

## Goals

| Priority | Goal |
|----------|------|
| **Primary** | Faster inference via pipeline parallelism (≥30% speedup target) |
| **Secondary** | Run larger models (70B+) that won't fit on single node |
| **Secondary** | Unified interface for distributed inference |

## Constraints

- **Windows not supported:** Vengeance (RTX 4090, Windows 11) cannot participate in EXO cluster
- **Non-destructive:** Ollama must remain operational throughout POC
- **Full access:** All 3 Linux nodes available for experimentation

## Architecture

### Cluster Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                     EXO P2P Mesh Network                        │
│                    (Automatic Discovery)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │  ndnlinuxsrv1    │  │  ndnlinuxsrv2    │  │ rog-flow-z13  │ │
│  │  100.77.248.9    │  │  100.113.166.1   │  │ 100.93.122.109│ │
│  │  CPU             │  │  CPU             │  │ AMD 8060S GPU │ │
│  │                  │  │                  │  │               │ │
│  │  ┌────────────┐  │  │  ┌────────────┐  │  │ ┌───────────┐ │ │
│  │  │ EXO Node   │  │  │  │ EXO Node   │  │  │ │ EXO Node  │ │ │
│  │  │ Port 52415 │◄─┼──┼─►│ Port 52415 │◄─┼──┼►│ Port 52415│ │ │
│  │  └────────────┘  │  │  └────────────┘  │  │ └───────────┘ │ │
│  │  ┌────────────┐  │  │  ┌────────────┐  │  │ ┌───────────┐ │ │
│  │  │ Ollama     │  │  │  │ Ollama     │  │  │ │ Ollama    │ │ │
│  │  │ Port 11434 │  │  │  │ Port 11434 │  │  │ │ Port 11434│ │ │
│  │  └────────────┘  │  │  └────────────┘  │  │ └───────────┘ │ │
│  └──────────────────┘  └──────────────────┘  └───────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

- **EXO on port 52415, Ollama on 11434** - No port conflicts
- **Manual peer discovery** - Tailscale subnets require explicit peer IPs
- **GPU-prioritized compute** - rog-flow-z13's AMD GPU handles heavy layers
- **Side-by-side operation** - Easy A/B comparison, non-destructive

## Installation & Setup

### Prerequisites (per node)

- Python 3.12+
- pip/pipx
- Tailscale connected

### Installation Commands

```bash
# On each Linux node:
pip install exo

# Additional for rog-flow-z13 (AMD GPU):
pip install exo[amd]
```

### Startup Commands

```bash
# On ndnlinuxsrv1 (primary entry point):
exo run --node-id srv1 --peers 100.113.166.1:52415,100.93.122.109:52415

# On ndnlinuxsrv2:
exo run --node-id srv2 --peers 100.77.248.9:52415,100.93.122.109:52415

# On rog-flow-z13:
exo run --node-id rog --peers 100.77.248.9:52415,100.113.166.1:52415
```

### Validation

- EXO dashboard at `http://<any-node>:52415`
- All 3 nodes visible in mesh

## Benchmark Strategy

### Test Prompt (consistent)

```
Write a Python function that implements binary search. Include docstring and type hints.
```

### Metrics to Capture

| Metric | Description |
|--------|-------------|
| Tokens/second | Raw generation speed |
| Time-to-first-token | Latency before output starts |
| Total time | End-to-end request duration |
| GPU/CPU utilization | Resource distribution |

### Test Matrix

| Model | Ollama (srv1) | Ollama (rog GPU) | EXO (3-node) |
|-------|---------------|------------------|--------------|
| qwen2.5:3b | ✓ | ✓ | ✓ |
| qwen2.5-coder:32b | ✓ | ✓ | ✓ |

### Benchmark Commands

```bash
# Ollama baseline
curl -s http://localhost:11434/api/generate \
  -d '{"model":"qwen2.5:3b","prompt":"...","stream":false}' | jq '.eval_count, .eval_duration'

# EXO cluster
curl -s http://100.77.248.9:52415/v1/chat/completions \
  -d '{"model":"qwen2.5:3b","messages":[{"role":"user","content":"..."}]}'
```

## Success Metrics

### Primary Criteria

| Metric | Target |
|--------|--------|
| Tokens/sec improvement | ≥30% faster than best single-node |
| Cluster formation | All 3 nodes visible in EXO dashboard |
| Inference completion | 100% success rate on test prompts |

### Secondary Criteria

| Metric | Target |
|--------|--------|
| Time-to-first-token | ≤2x single-node latency |
| Large model capability | Run 70B+ model across cluster |

### Decision Matrix

| Result | Action |
|--------|--------|
| ≥30% speedup | Phase 2: Kage Bunshin integration, production harden |
| 10-30% speedup | Evaluate complexity tradeoff, consider GPU-only config |
| <10% or slower | Shelve EXO, focus on Ollama load balancing |

## Implementation Steps

| Step | Task | Node(s) |
|------|------|---------|
| 1 | Verify Python 3.12+ on all nodes | All 3 |
| 2 | Install EXO package | All 3 |
| 3 | Install AMD ROCm backend | rog-flow-z13 |
| 4 | Start EXO with manual peer config | All 3 |
| 5 | Verify cluster formation in dashboard | Any |
| 6 | Download qwen2.5:3b through EXO | Cluster |
| 7 | Run baseline Ollama benchmarks | srv1, rog |
| 8 | Run EXO cluster benchmarks | Cluster |
| 9 | Compare results, document findings | - |
| 10 | Scale up to 32B model if Step 8 passes | Cluster |

## Rollback Plan

```bash
# Clean removal if needed:
pip uninstall exo
sudo systemctl disable --now exo  # if service created

# Ollama remains untouched - zero risk
```

## Deliverables

1. Working 3-node EXO cluster
2. Benchmark results: Ollama vs EXO comparison table
3. Go/no-go recommendation for Phase 2

## References

- [EXO GitHub Repository](https://github.com/exo-explore/exo)
- [EXO Deep Dive Article](https://medium.com/@leif.markthaler/deep-dive-exo-distributed-ai-inference-on-consumer-hardware-068e341d8e3c)
