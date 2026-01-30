#!/usr/bin/env python3
"""
local_broll_setup.py — Setup local video generation with RTX 4090

Run this on your machine with the 4090 to set up local B-roll generation.
Supports: CogVideoX-5B, Stable Video Diffusion, LTX-Video

Usage:
    python local_broll_setup.py --install cogvideo
    python local_broll_setup.py --install svd
    python local_broll_setup.py --test
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

MODELS = {
    "cogvideo": {
        "name": "CogVideoX-5B",
        "vram": "~18GB",
        "type": "text-to-video",
        "quality": "High",
        "speed": "~2min/5s clip",
        "repo": "THUDM/CogVideo",
        "hf_model": "THUDM/CogVideoX-5b",
    },
    "svd": {
        "name": "Stable Video Diffusion",
        "vram": "~16GB", 
        "type": "image-to-video",
        "quality": "Very High",
        "speed": "~1min/4s clip",
        "repo": "Stability-AI/generative-models",
        "hf_model": "stabilityai/stable-video-diffusion-img2vid-xt",
    },
    "ltx": {
        "name": "LTX-Video",
        "vram": "~12GB",
        "type": "text-to-video",
        "quality": "Good",
        "speed": "~30s/5s clip",
        "repo": "Lightricks/LTX-Video",
        "hf_model": "Lightricks/LTX-Video",
    },
}


def check_gpu():
    """Check GPU availability and VRAM."""
    try:
        import torch
        if not torch.cuda.is_available():
            print("❌ CUDA not available")
            return False
        
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"✅ GPU: {gpu_name}")
        print(f"✅ VRAM: {vram_gb:.1f} GB")
        
        if vram_gb < 16:
            print("⚠️ Warning: Less than 16GB VRAM, some models may not fit")
        
        return True
    except ImportError:
        print("❌ PyTorch not installed")
        return False


def install_cogvideo():
    """Install CogVideoX dependencies."""
    print("\n🔧 Installing CogVideoX-5B...")
    
    commands = [
        "pip install diffusers>=0.30.0 transformers accelerate",
        "pip install imageio[ffmpeg] decord",
    ]
    
    for cmd in commands:
        print(f"   Running: {cmd}")
        subprocess.run(cmd.split(), check=True)
    
    # Pre-download model
    print("   📥 Pre-downloading model (this may take a while)...")
    subprocess.run([
        "python", "-c",
        "from diffusers import CogVideoXPipeline; "
        "CogVideoXPipeline.from_pretrained('THUDM/CogVideoX-5b', torch_dtype='auto')"
    ])
    
    print("✅ CogVideoX installed!")


def install_svd():
    """Install Stable Video Diffusion dependencies."""
    print("\n🔧 Installing Stable Video Diffusion...")
    
    commands = [
        "pip install diffusers>=0.25.0 transformers accelerate",
        "pip install imageio[ffmpeg]",
    ]
    
    for cmd in commands:
        print(f"   Running: {cmd}")
        subprocess.run(cmd.split(), check=True)
    
    print("   📥 Pre-downloading model...")
    subprocess.run([
        "python", "-c",
        "from diffusers import StableVideoDiffusionPipeline; "
        "import torch; "
        "StableVideoDiffusionPipeline.from_pretrained("
        "'stabilityai/stable-video-diffusion-img2vid-xt', "
        "torch_dtype=torch.float16, variant='fp16')"
    ])
    
    print("✅ Stable Video Diffusion installed!")


def install_ltx():
    """Install LTX-Video dependencies."""
    print("\n🔧 Installing LTX-Video...")
    
    commands = [
        "pip install diffusers>=0.31.0 transformers accelerate",
        "pip install imageio[ffmpeg] sentencepiece",
    ]
    
    for cmd in commands:
        print(f"   Running: {cmd}")
        subprocess.run(cmd.split(), check=True)
    
    print("✅ LTX-Video installed!")


def test_generation():
    """Test video generation with installed model."""
    print("\n🧪 Testing video generation...")
    
    # Try CogVideoX first
    try:
        from diffusers import CogVideoXPipeline
        import torch
        
        print("   Testing CogVideoX-5B...")
        pipe = CogVideoXPipeline.from_pretrained(
            "THUDM/CogVideoX-5b",
            torch_dtype=torch.bfloat16
        ).to("cuda")
        
        pipe.enable_model_cpu_offload()
        pipe.vae.enable_tiling()
        
        video = pipe(
            prompt="A close-up of computer chips on a circuit board, blue lighting",
            num_frames=49,  # ~2 seconds at 24fps
            guidance_scale=6,
        ).frames[0]
        
        # Save test
        from diffusers.utils import export_to_video
        export_to_video(video, "/tmp/test_broll.mp4", fps=24)
        print("✅ Test video saved to /tmp/test_broll.mp4")
        return True
        
    except Exception as e:
        print(f"❌ CogVideoX test failed: {e}")
    
    # Try SVD
    try:
        from diffusers import StableVideoDiffusionPipeline
        from diffusers.utils import load_image, export_to_video
        import torch
        
        print("   Testing Stable Video Diffusion...")
        pipe = StableVideoDiffusionPipeline.from_pretrained(
            "stabilityai/stable-video-diffusion-img2vid-xt",
            torch_dtype=torch.float16,
            variant="fp16"
        ).to("cuda")
        
        # Need an input image for SVD
        print("   ⚠️ SVD requires input image - skipping test")
        return True
        
    except Exception as e:
        print(f"❌ SVD test failed: {e}")
    
    return False


def show_models():
    """Show available models."""
    print("\n📋 Available Models for RTX 4090 (24GB VRAM):\n")
    
    for key, model in MODELS.items():
        print(f"  {key}:")
        print(f"    Name: {model['name']}")
        print(f"    Type: {model['type']}")
        print(f"    VRAM: {model['vram']}")
        print(f"    Quality: {model['quality']}")
        print(f"    Speed: {model['speed']}")
        print()
    
    print("Recommended: cogvideo (best text-to-video for B-roll)")
    print("             svd (if you have reference images)")


def main():
    parser = argparse.ArgumentParser(description="Setup local video generation")
    parser.add_argument("--install", choices=["cogvideo", "svd", "ltx", "all"],
                       help="Install a model")
    parser.add_argument("--test", action="store_true", help="Test generation")
    parser.add_argument("--list", action="store_true", help="List available models")
    parser.add_argument("--check", action="store_true", help="Check GPU")
    
    args = parser.parse_args()
    
    if args.list:
        show_models()
        return
    
    if args.check:
        check_gpu()
        return
    
    if args.install:
        if not check_gpu():
            print("Fix GPU issues first!")
            return
        
        if args.install == "cogvideo" or args.install == "all":
            install_cogvideo()
        if args.install == "svd" or args.install == "all":
            install_svd()
        if args.install == "ltx" or args.install == "all":
            install_ltx()
        return
    
    if args.test:
        test_generation()
        return
    
    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    main()
