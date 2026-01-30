#!/bin/bash
# Setup CogVideoX on Vengeance (RTX 4090)
# Run this on vengeance: bash setup_vengeance_cogvideo.sh

set -e

echo "🔧 Setting up CogVideoX on Vengeance..."

# Fix python3-venv (needs password)
echo "Installing python3-venv..."
sudo apt update && sudo apt install -y python3.12-venv

# Create fresh venv
cd ~
rm -rf cogvideo_env
python3 -m venv cogvideo_env
source cogvideo_env/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install PyTorch with CUDA 12.4
echo "Installing PyTorch..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# Install CogVideoX dependencies
echo "Installing CogVideoX..."
pip install diffusers>=0.30.0 transformers accelerate
pip install imageio[ffmpeg] decord sentencepiece

# Verify
echo "Verifying installation..."
python -c "
import torch
print(f'PyTorch {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
    print(f'VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB')

from diffusers import CogVideoXPipeline
print('CogVideoX available!')
"

echo ""
echo "✅ Setup complete!"
echo "To use: source ~/cogvideo_env/bin/activate"
