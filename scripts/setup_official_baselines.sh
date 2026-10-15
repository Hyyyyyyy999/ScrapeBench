#!/bin/bash
set -euo pipefail
cd /mnt/beegfs/home/huangyue26/ScrapBench
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY all_proxy
mkdir -p external

clone_clean() {
  local url=$1
  local dst=$2
  if git -C "$dst" rev-parse HEAD >/dev/null 2>&1; then
    return
  fi
  if [ -e "$dst" ]; then
    mv "$dst" "${dst}.incomplete.$(date +%s)"
  fi
  git clone --depth 1 --recurse-submodules "$url" "$dst"
}

clone_clean https://github.com/AIASLab/GAP-Diff.git external/GAP-Diff
clone_clean https://github.com/showlab/IDProtector.git external/IDProtector

if [ ! -x external/gapdiff_env/bin/python ]; then
  conda create -y -p /mnt/beegfs/home/huangyue26/ScrapBench/external/gapdiff_env python=3.9
  /mnt/beegfs/home/huangyue26/ScrapBench/external/gapdiff_env/bin/pip install -r external/GAP-Diff/requirements.txt
fi
if [ ! -s external/GAP-Diff/weights/model/G_per16_pretrain.pth ]; then
  mkdir -p external/GAP-Diff/weights/model
  venv/bin/gdown 1UVYFNOLlXl2xZNgVzBkXmMsDx693R6ud -O external/GAP-Diff/weights/model/G_per16_pretrain.pth
fi

if [ ! -x external/idprotector_env/bin/python ]; then
  conda create -y -p /mnt/beegfs/home/huangyue26/ScrapBench/external/idprotector_env python=3.9
  /mnt/beegfs/home/huangyue26/ScrapBench/external/idprotector_env/bin/pip install \
    torch==2.4.1 torchvision==0.19.1 --index-url https://download.pytorch.org/whl/cu118
  /mnt/beegfs/home/huangyue26/ScrapBench/external/idprotector_env/bin/pip install \
    transformers==4.37.2 diffusers==0.29.2 accelerate safetensors omegaconf \
    peft==0.12.0 insightface==0.7.3 onnxruntime onnx2torch einops timm \
    kornia brisque pyiqa torch-dct opencv-python scikit-image scikit-learn
fi
test -s external/IDProtector/protector_model.pt
touch external/.official_baselines_ready
