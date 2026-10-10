#!/bin/bash
set -e
cd "$(dirname "$0")/.."
echo "[setup] python $(python3 --version)"
python3 -c "import torch" 2>/dev/null && echo "[setup] torch already present" || {
  pip install --upgrade pip
  pip install torch==2.4.1 torchvision --index-url https://download.pytorch.org/whl/cu121
}
pip install -q diffusers==0.31.0 transformers==4.44.2 peft==0.13.2 accelerate==1.0.1 \
  safetensors insightface onnxruntime-gpu opencv-python-headless kaggle gdown \
  "scikit-image" pandas matplotlib pyyaml scipy tqdm huggingface_hub open_clip_torch
python3 -c "import torch; print('[setup] torch', torch.__version__, 'cuda', torch.cuda.is_available(), torch.cuda.device_count())"
mkdir -p data runs figures report logs
echo "[setup] done"
