#!/bin/bash
set -e
cd "$(dirname "$0")/.."
export HF_HUB_ENABLE_HF_TRANSFER=0
python3 - <<'EOF'
from huggingface_hub import snapshot_download, hf_hub_download
print("[models] SD1.5 ...", flush=True)
snapshot_download("stable-diffusion-v1-5/stable-diffusion-v1-5",
                  allow_patterns=["*.json", "*.txt", "*fp16.safetensors", "*.safetensors"],
                  ignore_patterns=["*.ckpt", "*nonema*", "v1-5-pruned-emaonly.safetensors"])
print("[models] IP-Adapter-FaceID ...", flush=True)
hf_hub_download("h94/IP-Adapter-FaceID", "ip-adapter-faceid_sd15.bin")
print("[models] done", flush=True)
EOF
