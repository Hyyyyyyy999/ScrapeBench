import os
import time

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"

from huggingface_hub import snapshot_download


def dl(repo, allow_patterns, ignore_patterns=()):
    for attempt in range(30):
        try:
            p = snapshot_download(repo, allow_patterns=allow_patterns, ignore_patterns=list(ignore_patterns))
            print(f"DONE {repo} -> {p}", flush=True)
            return
        except Exception as e:
            print(f"retry {attempt} {repo}: {type(e).__name__} {str(e)[:160]}", flush=True)
            time.sleep(60)
    raise SystemExit(f"FAILED {repo}")


dl("stabilityai/stable-diffusion-xl-base-1.0",
   allow_patterns=["*.json", "*.txt", "*fp16.safetensors", "tokenizer/*", "tokenizer_2/*", "scheduler/*"],
   ignore_patterns=["*.png", "*.jpg", "*.bin"])

print("PREFETCH ALL DONE", flush=True)
