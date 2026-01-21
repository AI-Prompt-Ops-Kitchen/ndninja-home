# EXO Integration Phase 1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Set up 3-node EXO cluster alongside Ollama, benchmark distributed inference vs single-node, achieve ≥30% speedup.

**Architecture:** EXO P2P mesh on port 52415 across ndnlinuxsrv1, ndnlinuxsrv2, rog-flow-z13. Ollama unchanged on port 11434. Side-by-side comparison.

**Tech Stack:** EXO (Python 3.12+), Tailscale networking, AMD ROCm (rog-flow-z13 only)

---

## Task 1: Verify Python Version on All Nodes

**Goal:** Confirm Python 3.12+ is available on all 3 Linux nodes (EXO requirement).

**Step 1: Check ndnlinuxsrv1 (local)**

Run:
```bash
python3 --version
```
Expected: Python 3.12.x or higher

**Step 2: Check ndnlinuxsrv2**

Run:
```bash
ssh ndnlinuxsrv2 'python3 --version'
```
Expected: Python 3.12.x or higher

**Step 3: Check rog-flow-z13**

Run:
```bash
ssh -p 2222 rog-flow-z13 'python3 --version'
```
Expected: Python 3.12.x or higher

**Step 4: Document versions**

If any node has Python < 3.12, note it for upgrade. Otherwise proceed.

---

## Task 2: Install EXO on ndnlinuxsrv1

**Goal:** Install EXO package on primary node.

**Step 1: Install EXO via pip**

Run:
```bash
pip install exo
```
Expected: Successfully installed exo-X.X.X

**Step 2: Verify installation**

Run:
```bash
exo --version
```
Expected: Version number displayed

**Step 3: Check EXO help**

Run:
```bash
exo --help
```
Expected: Help text showing available commands including `run`

---

## Task 3: Install EXO on ndnlinuxsrv2

**Goal:** Install EXO package on secondary CPU node.

**Step 1: Install EXO via SSH**

Run:
```bash
ssh ndnlinuxsrv2 'pip install exo'
```
Expected: Successfully installed exo-X.X.X

**Step 2: Verify installation**

Run:
```bash
ssh ndnlinuxsrv2 'exo --version'
```
Expected: Version number displayed

---

## Task 4: Install EXO on rog-flow-z13 (with AMD GPU support)

**Goal:** Install EXO with ROCm backend for AMD GPU acceleration.

**Step 1: Install EXO with AMD extras via SSH**

Run:
```bash
ssh -p 2222 rog-flow-z13 'pip install exo[amd]'
```
Expected: Successfully installed exo with AMD dependencies

**Step 2: Verify installation**

Run:
```bash
ssh -p 2222 rog-flow-z13 'exo --version'
```
Expected: Version number displayed

**Step 3: Verify ROCm is detected**

Run:
```bash
ssh -p 2222 rog-flow-z13 'rocm-smi --showproductname'
```
Expected: Shows AMD Radeon 8060S GPU

---

## Task 5: Start EXO Cluster - Node 1 (ndnlinuxsrv1)

**Goal:** Start EXO on primary node with peer configuration.

**Step 1: Start EXO in background**

Run:
```bash
nohup exo run --node-id srv1 --broadcast-port 52415 \
  --chatgpt-api-port 52416 \
  > /tmp/exo-srv1.log 2>&1 &
echo $! > /tmp/exo-srv1.pid
```
Expected: Process starts, PID saved

**Step 2: Verify process running**

Run:
```bash
sleep 3 && ps -p $(cat /tmp/exo-srv1.pid)
```
Expected: Process exists

**Step 3: Check initial log**

Run:
```bash
tail -20 /tmp/exo-srv1.log
```
Expected: EXO startup messages, listening on ports

---

## Task 6: Start EXO Cluster - Node 2 (ndnlinuxsrv2)

**Goal:** Start EXO on secondary CPU node.

**Step 1: Start EXO via SSH**

Run:
```bash
ssh ndnlinuxsrv2 'nohup exo run --node-id srv2 --broadcast-port 52415 \
  --chatgpt-api-port 52416 \
  > /tmp/exo-srv2.log 2>&1 &
echo $! > /tmp/exo-srv2.pid'
```
Expected: Process starts

**Step 2: Verify process running**

Run:
```bash
ssh ndnlinuxsrv2 'sleep 3 && ps -p $(cat /tmp/exo-srv2.pid)'
```
Expected: Process exists

---

## Task 7: Start EXO Cluster - Node 3 (rog-flow-z13)

**Goal:** Start EXO on GPU node.

**Step 1: Start EXO via SSH**

Run:
```bash
ssh -p 2222 rog-flow-z13 'nohup exo run --node-id rog --broadcast-port 52415 \
  --chatgpt-api-port 52416 \
  > /tmp/exo-rog.log 2>&1 &
echo $! > /tmp/exo-rog.pid'
```
Expected: Process starts

**Step 2: Verify process running**

Run:
```bash
ssh -p 2222 rog-flow-z13 'sleep 3 && ps -p $(cat /tmp/exo-rog.pid)'
```
Expected: Process exists

---

## Task 8: Verify Cluster Formation

**Goal:** Confirm all 3 nodes see each other in the EXO mesh.

**Step 1: Check EXO dashboard**

Open in browser:
```
http://100.77.248.9:52416
```
Expected: EXO web UI showing connected nodes

**Step 2: Check logs for peer discovery**

Run:
```bash
grep -i "peer\|node\|connect" /tmp/exo-srv1.log | tail -20
```
Expected: Messages about discovering/connecting to other nodes

**Step 3: List cluster status via API**

Run:
```bash
curl -s http://localhost:52416/v1/models | jq .
```
Expected: JSON response (may be empty if no models yet)

---

## Task 9: Download Model Through EXO

**Goal:** Pull qwen2.5:3b model through the EXO cluster.

**Step 1: Download model via EXO**

Run:
```bash
exo download qwen2.5:3b
```
Expected: Model download progress, completion message

Note: If `exo download` not available, use the web UI or API to trigger download.

**Step 2: Verify model available**

Run:
```bash
curl -s http://localhost:52416/v1/models | jq '.data[].id'
```
Expected: "qwen2.5:3b" in list

---

## Task 10: Create Benchmark Script

**Files:**
- Create: `scripts/benchmark_exo_vs_ollama.py`

**Step 1: Write benchmark script**

```python
#!/usr/bin/env python3
"""
Benchmark: EXO Cluster vs Ollama Single-Node
============================================
Measures tokens/sec, time-to-first-token, total time.
"""

import argparse
import json
import time
import urllib.request
from dataclasses import dataclass
from typing import Optional


@dataclass
class BenchmarkResult:
    name: str
    model: str
    total_time: float
    tokens: int
    tokens_per_sec: float
    time_to_first_token: Optional[float] = None
    error: Optional[str] = None


PROMPT = "Write a Python function that implements binary search. Include docstring and type hints."


def benchmark_ollama(host: str, model: str) -> BenchmarkResult:
    """Benchmark Ollama single-node inference."""
    url = f"{host}/api/generate"
    payload = {
        "model": model,
        "prompt": PROMPT,
        "stream": False,
    }

    start = time.time()
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())

        total_time = time.time() - start
        tokens = data.get("eval_count", 0)
        tokens_per_sec = tokens / total_time if total_time > 0 else 0

        return BenchmarkResult(
            name=f"Ollama ({host})",
            model=model,
            total_time=total_time,
            tokens=tokens,
            tokens_per_sec=tokens_per_sec,
        )
    except Exception as e:
        return BenchmarkResult(
            name=f"Ollama ({host})",
            model=model,
            total_time=0,
            tokens=0,
            tokens_per_sec=0,
            error=str(e),
        )


def benchmark_exo(host: str, model: str) -> BenchmarkResult:
    """Benchmark EXO cluster inference."""
    url = f"{host}/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": PROMPT}],
        "stream": False,
    }

    start = time.time()
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())

        total_time = time.time() - start
        # Extract token count from response
        usage = data.get("usage", {})
        tokens = usage.get("completion_tokens", 0)
        tokens_per_sec = tokens / total_time if total_time > 0 else 0

        return BenchmarkResult(
            name=f"EXO Cluster ({host})",
            model=model,
            total_time=total_time,
            tokens=tokens,
            tokens_per_sec=tokens_per_sec,
        )
    except Exception as e:
        return BenchmarkResult(
            name=f"EXO Cluster ({host})",
            model=model,
            total_time=0,
            tokens=0,
            tokens_per_sec=0,
            error=str(e),
        )


def print_results(results: list[BenchmarkResult]):
    """Print formatted benchmark results."""
    print("\n" + "=" * 70)
    print("BENCHMARK RESULTS: EXO vs Ollama")
    print("=" * 70)
    print(f"{'Name':<30} {'Model':<15} {'Time':>8} {'Tokens':>8} {'Tok/s':>10}")
    print("-" * 70)

    for r in results:
        if r.error:
            print(f"{r.name:<30} {r.model:<15} {'ERROR':>8} {r.error[:20]}")
        else:
            print(f"{r.name:<30} {r.model:<15} {r.total_time:>7.2f}s {r.tokens:>8} {r.tokens_per_sec:>9.1f}")

    print("-" * 70)

    # Calculate speedup
    ollama_results = [r for r in results if "Ollama" in r.name and not r.error]
    exo_results = [r for r in results if "EXO" in r.name and not r.error]

    if ollama_results and exo_results:
        best_ollama = max(ollama_results, key=lambda r: r.tokens_per_sec)
        best_exo = max(exo_results, key=lambda r: r.tokens_per_sec)

        if best_ollama.tokens_per_sec > 0:
            speedup = ((best_exo.tokens_per_sec - best_ollama.tokens_per_sec)
                      / best_ollama.tokens_per_sec * 100)
            print(f"\nSpeedup: {speedup:+.1f}% (EXO vs best Ollama)")

            if speedup >= 30:
                print("✓ SUCCESS: Target ≥30% speedup achieved!")
            elif speedup > 0:
                print("~ PARTIAL: Some speedup, but below 30% target")
            else:
                print("✗ FAIL: EXO slower than single-node Ollama")


def main():
    parser = argparse.ArgumentParser(description="Benchmark EXO vs Ollama")
    parser.add_argument("--model", default="qwen2.5:3b", help="Model to test")
    parser.add_argument("--runs", type=int, default=3, help="Number of runs per config")
    args = parser.parse_args()

    results = []

    print(f"Benchmarking model: {args.model}")
    print(f"Runs per configuration: {args.runs}")

    # Ollama baselines
    ollama_hosts = [
        "http://localhost:11434",           # ndnlinuxsrv1
        "http://100.93.122.109:11434",      # rog-flow-z13 (GPU)
    ]

    for host in ollama_hosts:
        print(f"\nTesting Ollama at {host}...")
        for i in range(args.runs):
            result = benchmark_ollama(host, args.model)
            results.append(result)
            if not result.error:
                print(f"  Run {i+1}: {result.tokens_per_sec:.1f} tok/s")

    # EXO cluster
    exo_host = "http://localhost:52416"
    print(f"\nTesting EXO cluster at {exo_host}...")
    for i in range(args.runs):
        result = benchmark_exo(exo_host, args.model)
        results.append(result)
        if not result.error:
            print(f"  Run {i+1}: {result.tokens_per_sec:.1f} tok/s")

    print_results(results)


if __name__ == "__main__":
    main()
```

**Step 2: Make executable**

Run:
```bash
chmod +x scripts/benchmark_exo_vs_ollama.py
```

**Step 3: Commit benchmark script**

Run:
```bash
git add scripts/benchmark_exo_vs_ollama.py
git commit -m "feat: add EXO vs Ollama benchmark script"
```

---

## Task 11: Run Baseline Ollama Benchmarks

**Goal:** Establish performance baseline with single-node Ollama.

**Step 1: Run benchmark (Ollama only first)**

Run:
```bash
python3 scripts/benchmark_exo_vs_ollama.py --model qwen2.5:3b --runs 3
```
Expected: Results showing tokens/sec for Ollama configurations

**Step 2: Document baseline results**

Note the best Ollama tokens/sec for comparison.

---

## Task 12: Run Full Benchmark Comparison

**Goal:** Compare EXO cluster vs Ollama baselines.

**Step 1: Ensure EXO cluster is running**

Run:
```bash
curl -s http://localhost:52416/v1/models | jq .
```
Expected: Model list including qwen2.5:3b

**Step 2: Run full benchmark**

Run:
```bash
python3 scripts/benchmark_exo_vs_ollama.py --model qwen2.5:3b --runs 5
```
Expected: Complete comparison with speedup percentage

**Step 3: Save results**

Run:
```bash
python3 scripts/benchmark_exo_vs_ollama.py --model qwen2.5:3b --runs 5 > docs/benchmark-results-qwen3b.txt 2>&1
```

---

## Task 13: Scale Up to 32B Model (if Step 12 passes)

**Goal:** Test with larger model to see if benefits increase.

**Step 1: Download larger model through EXO**

Run:
```bash
exo download qwen2.5-coder:32b
```
Expected: Model distributed across cluster

**Step 2: Run benchmark with 32B model**

Run:
```bash
python3 scripts/benchmark_exo_vs_ollama.py --model qwen2.5-coder:32b --runs 3
```
Expected: Results showing distributed inference performance

**Step 3: Save results**

Run:
```bash
python3 scripts/benchmark_exo_vs_ollama.py --model qwen2.5-coder:32b --runs 3 > docs/benchmark-results-qwen32b.txt 2>&1
```

---

## Task 14: Document Results and Recommendation

**Files:**
- Create: `docs/exo-phase1-results.md`

**Step 1: Write results document**

Include:
- Cluster formation: success/fail
- Benchmark results table
- Speedup percentage achieved
- Go/no-go recommendation for Phase 2
- Any issues encountered

**Step 2: Commit all results**

Run:
```bash
git add docs/
git commit -m "docs: add EXO Phase 1 POC results and benchmarks"
```

---

## Task 15: Cleanup (Optional)

**Goal:** Stop EXO processes if not continuing to Phase 2.

**Step 1: Stop EXO on all nodes**

Run:
```bash
# Local
kill $(cat /tmp/exo-srv1.pid) 2>/dev/null

# ndnlinuxsrv2
ssh ndnlinuxsrv2 'kill $(cat /tmp/exo-srv2.pid) 2>/dev/null'

# rog-flow-z13
ssh -p 2222 rog-flow-z13 'kill $(cat /tmp/exo-rog.pid) 2>/dev/null'
```

**Step 2: Verify Ollama still running**

Run:
```bash
curl -s http://localhost:11434/api/tags | jq '.models | length'
```
Expected: Number of models (Ollama unaffected)

---

## Summary

| Task | Description | Est. Steps |
|------|-------------|------------|
| 1 | Verify Python 3.12+ | 4 |
| 2-4 | Install EXO on all nodes | 6 |
| 5-7 | Start EXO cluster | 6 |
| 8 | Verify cluster formation | 3 |
| 9 | Download model | 2 |
| 10 | Create benchmark script | 3 |
| 11 | Baseline Ollama benchmarks | 2 |
| 12 | Full comparison benchmark | 3 |
| 13 | Scale to 32B (conditional) | 3 |
| 14 | Document results | 2 |
| 15 | Cleanup (optional) | 2 |

**Total: 15 tasks, ~36 steps**
