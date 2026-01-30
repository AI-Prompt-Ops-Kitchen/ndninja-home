# MuseTalk Setup Log — Vengeance (2026-01-26)

## Status: ✅ INSTALLED & READY

## Machine
- **Host:** Vengeance (Windows 11 WSL2 Ubuntu)
- **SSH:** `ssh Steam@100.98.226.75`
- **GPU:** NVIDIA RTX 4090 (24GB VRAM)
- **CPU:** 14th gen Intel i9, 64GB RAM
- **CUDA Driver:** 591.74 (CUDA 13.1 capable)

## Installation Location
- **Code:** `/mnt/d/musetalk/` (D: drive, 2.4TB free)
- **Conda env:** `~/miniforge3/envs/musetalk/` (Linux native filesystem)
- **FFmpeg static:** `/mnt/d/musetalk/ffmpeg-7.0.2-amd64-static/`

## Environment
- **Python:** 3.10.19 (conda, via miniforge3)
- **PyTorch:** 2.6.0+cu124 (CUDA 12.4)
- **Conda env name:** `musetalk`

### Activate Environment
```bash
source ~/miniforge3/bin/activate musetalk
cd /mnt/d/musetalk
export FFMPEG_PATH=/mnt/d/musetalk/ffmpeg-7.0.2-amd64-static
```

## Key Dependencies Installed
| Package | Version | Status |
|---------|---------|--------|
| PyTorch | 2.6.0+cu124 | ✅ |
| diffusers | 0.30.2 | ✅ |
| transformers | 4.39.2 | ✅ |
| opencv-python | 4.9.0 | ✅ |
| mmcv | 2.0.1 | ✅ |
| mmdet | 3.1.0 | ✅ |
| mmpose | 1.1.0 | ✅ |
| librosa | 0.11.0 | ✅ |
| tensorflow | 2.12.0 | ✅ (CPU only — no CUDA for TF, but TF is only used for tensorboard) |
| omegaconf | 2.3.0 | ✅ |
| einops | 0.8.1 | ✅ |
| gradio | 5.24.0 | ✅ |
| huggingface_hub | 0.30.2 | ✅ |

## Model Weights
All models downloaded and verified:

| Model | Path | Size |
|-------|------|------|
| MuseTalk V1.0 | `models/musetalk/pytorch_model.bin` | 3.2 GB |
| MuseTalk V1.5 | `models/musetalkV15/unet.pth` | 3.2 GB |
| SyncNet | `models/syncnet/latentsync_syncnet.pt` | 1.4 GB |
| DWPose | `models/dwpose/dw-ll_ucoco_384.pth` | 389 MB |
| Face Parse BiSeNet | `models/face-parse-bisent/79999_iter.pth` | 51 MB |
| ResNet18 | `models/face-parse-bisent/resnet18-5c106cde.pth` | 45 MB |
| SD VAE | `models/sd-vae/diffusion_pytorch_model.bin` | 320 MB |
| Whisper Tiny | `models/whisper/pytorch_model.bin` | 145 MB |

**Total model size:** ~8.7 GB

## Sanity Check Results
```
PyTorch 2.6.0+cu124 — CUDA available — RTX 4090 — 24.0 GB VRAM
diffusers: OK (v0.30.2) [AutoencoderKL found]
cv2: OK (v4.9.0)
mmcv: OK (v2.0.1)
mmpose: OK (v1.1.0)
mmdet: OK (v3.1.0)
librosa: OK (v0.11.0)
transformers: OK (v4.39.2)
omegaconf: OK (v2.3.0)
einops: OK (v0.8.1)
soundfile: OK (v0.12.1)
```

## Usage (Quick Reference)

### Normal Inference (V1.5 Recommended)
```bash
source ~/miniforge3/bin/activate musetalk
cd /mnt/d/musetalk
export FFMPEG_PATH=/mnt/d/musetalk/ffmpeg-7.0.2-amd64-static
sh inference.sh v1.5 normal
```

### Real-time Inference
```bash
sh inference.sh v1.5 realtime
```

### Gradio Web UI
```bash
python app.py --use_float16 --ffmpeg_path /mnt/d/musetalk/ffmpeg-7.0.2-amd64-static
```

### Config File
Edit `configs/inference/test.yaml` to set:
- `video_path`: Path to input video
- `audio_path`: Path to input audio

## Issues & Notes
1. **Sudo not available** — installed via conda/miniforge (no apt packages installed)
2. **NTFS symlink limitation** — conda env lives on Linux native FS (`~/miniforge3/envs/musetalk/`), code on `/mnt/d/musetalk/`
3. **openmim dependency conflicts** — `openxlab` pins ancient `setuptools==60.2.0` and `requests==2.28.2`. Upgraded setuptools and requests after openmim install; the conflicts are harmless (openxlab is an optional download tool, not used at runtime)
4. **chumpy build issue** — required `pip install --no-build-isolation chumpy` to work around setuptools/pip module import issue in its setup.py
5. **TensorFlow TF-TRT warning** — expected, TensorRT not installed. TF is only used for tensorboard logging, not core inference
6. **numpy pinned to 1.23.5** — as required by MuseTalk's requirements.txt. Works fine with Python 3.10
7. **ffmpeg** — not installed system-wide (no sudo). Using static binary at `/mnt/d/musetalk/ffmpeg-7.0.2-amd64-static/ffmpeg`. Must set `FFMPEG_PATH` env var or pass `--ffmpeg_path` arg.

## Setup Process Summary
1. ✅ SSH verified, GPU visible (`nvidia-smi` via WSL2)
2. ✅ Cloned repo to `/mnt/d/musetalk/`
3. ✅ Created conda env `musetalk` with Python 3.10.19
4. ✅ Installed PyTorch 2.6.0 with CUDA 12.4
5. ✅ Installed all requirements.txt dependencies
6. ✅ Installed MMLab packages (mmengine, mmcv 2.0.1, mmdet 3.1.0, mmpose 1.1.0)
7. ✅ Downloaded ffmpeg 7.0.2 static binary
8. ✅ Downloaded all model weights (~8.7 GB)
9. ✅ Sanity check passed — all imports OK, GPU detected
