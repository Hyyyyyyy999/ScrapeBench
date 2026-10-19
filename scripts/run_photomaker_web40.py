#!/usr/bin/env python3
"""PhotoMaker V1 evaluation for one defense/identity/intervention cell."""
import argparse
import gc
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
from PIL import Image

# Executing a file under scripts/ puts scripts/, rather than the repository
# root, at sys.path[0] on the cluster.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scrapebench.funnel import get_tier
from scrapebench.metrics.id_sim import IdScorer
from scrapebench.metrics.stats import bootstrap_ci_mean
from scrapebench.runner.results import append_row, ensure_csv, now


PROMPTS = (
    "a clean front-facing portrait of a person img for a social media avatar, realistic, high quality",
    "a casual smartphone selfie of a person img, realistic, high quality",
    "a low-light indoor social photo of a person img, realistic, high quality",
    "an outdoor travel photo of a person img with a detailed background, realistic, high quality",
)


def release_transform_models():
    try:
        from scrapebench.funnel.regenerate import _REGEN
        _REGEN.clear()
    except Exception:
        pass
    try:
        from scrapebench.funnel.restore import _UPSAMPLERS
        _UPSAMPLERS.clear()
    except Exception:
        pass
    gc.collect(); torch.cuda.empty_cache()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--method", required=True)
    ap.add_argument("--pid", required=True)
    ap.add_argument("--tier", required=True)
    ap.add_argument("--run-name", default="web4_photomaker")
    ap.add_argument("--steps", type=int, default=30)
    ap.add_argument("--seed", type=int, default=20261018)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    data = Path("data/web40")
    paths = sorted((data / "protected" / args.method / args.pid).glob("*.png"))
    if len(paths) != 4: raise SystemExit(f"expected four inputs, got {len(paths)}")
    tier_fn = get_tier(args.tier)
    inputs = [tier_fn(Image.open(p).convert("RGB")) for p in paths]
    release_transform_models()

    idp = Path("/mnt/beegfs/home/huangyue26/IDProtector")
    sys.path.insert(0, str(idp))
    from diffusers import DDIMScheduler
    from huggingface_hub import hf_hub_download
    from generation_methods.PhotoMaker.photomaker import PhotoMakerStableDiffusionXLPipeline

    ckpt = hf_hub_download("TencentARC/PhotoMaker", "photomaker-v1.bin",
                           repo_type="model", local_files_only=True)
    pipe = PhotoMakerStableDiffusionXLPipeline.from_pretrained(
        "SG161222/RealVisXL_V3.0", torch_dtype=torch.bfloat16,
        use_safetensors=True, variant="fp16", local_files_only=True).to("cuda")
    pipe.set_progress_bar_config(disable=True)
    pipe.load_photomaker_adapter(os.path.dirname(ckpt), subfolder="",
                                 weight_name=os.path.basename(ckpt),
                                 trigger_word="img", pm_version="v1")
    pipe.id_encoder.to("cuda")
    pipe.scheduler = DDIMScheduler.from_config(pipe.scheduler.config)
    pipe.fuse_lora()
    negative = "(asymmetry, worst quality, low quality, illustration, painting, cartoon), open mouth"
    start = time.time(); outputs = []
    for prompt in PROMPTS:
        outputs.extend(pipe(prompt=prompt, input_id_images=inputs,
                            negative_prompt=negative, num_images_per_prompt=1,
                            num_inference_steps=args.steps,
                            start_merge_step=min(30, max(1, int(args.steps * .2))),
                            generator=torch.Generator(device="cuda").manual_seed(args.seed)).images)
    gen_sec = time.time() - start
    del pipe; torch.cuda.empty_cache()

    out_dir = Path("runs") / args.run_name / "generations" / "photomaker" / args.method / args.tier / args.pid
    out_dir.mkdir(parents=True, exist_ok=True)
    scorer = IdScorer(use_gpu=False)
    refs = scorer.ref_embeddings(args.pid, [str(p) for p in sorted((data / "refs" / args.pid).glob("*"))[:2]])
    rows = []; sims = []
    for i, image in enumerate(outputs):
        score, detected = scorer.best_sim(image, refs); sims.append(score)
        name = f"p{i:02d}_s000.png"; image.save(out_dir / name)
        rows.append({"pid": args.pid, "method": args.method, "tier": args.tier,
                     "attack": "photomaker", "prompt_id": i, "prompt": PROMPTS[i],
                     "file": name, "ism": None if np.isnan(score) else round(float(score), 6),
                     "detected": bool(detected)})
    with (out_dir / "samples.jsonl").open("w") as h:
        for row in rows: h.write(json.dumps(row, ensure_ascii=False) + "\n")
    values = np.asarray(sims, dtype=float); mean, (lo, hi) = bootstrap_ci_mean(values)
    result = ensure_csv(str(Path("runs") / args.run_name / "results.csv"))
    append_row(result, dict(run=args.run_name, stage="P", pid=args.pid, method=args.method,
        tier=args.tier, attack="photomaker", n_gallery=4, n_samples=4,
        mean_id=round(mean, 4), ci_lo=round(lo, 4), ci_hi=round(hi, 4),
        p_lo="", p_hi="", pos_rate=round(float(np.nanmean(values >= .30)), 4),
        gen_sec=round(gen_sec, 1), sec_per_img=round(gen_sec / 4, 2), ts=now()))
    print(f"PhotoMaker {args.method}/{args.pid}/{args.tier} mean={mean:.3f} sec={gen_sec:.0f}")


if __name__ == "__main__":
    main()
