from huggingface_hub import snapshot_download
snapshot_download("stabilityai/stable-diffusion-xl-base-1.0",
                  allow_patterns=["*.json", "*.txt", "*fp16.safetensors"])
print("sdxl done")
