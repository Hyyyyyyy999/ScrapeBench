import argparse
import os
import time
import numpy as np
import torch
from PIL import Image
from ..config import load_config
from ..funnel import get_tier
from ..attack.train_utils import load_sd15, load_gallery, build_pipeline, generate_images, add_lora, reset_lora, dreambooth_loss, PROMPTS, CLASS_PROMPT
from ..attack.train_utils import seed_all
from ..metrics.id_sim import IdScorer
from ..metrics.stats import bootstrap_ci_mean
from .results import ensure_csv, append_row, load_done, log, now


def list_galleries(data_root):
    root = os.path.join(data_root, "protected")
    out = {}
    for m in sorted(os.listdir(root)):
        for pid in sorted(os.listdir(os.path.join(root, m))):
            d = os.path.join(root, m, pid)
            if os.path.isdir(d):
                imgs = sorted(i for i in os.listdir(d) if i.lower().endswith((".png", ".jpg", ".jpeg")))
                out[(m, pid)] = [os.path.join(d, i) for i in imgs]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--tiers", default=None)
    ap.add_argument("--methods", default=None)
    ap.add_argument("--ids", default=None)
    args = ap.parse_args()
    cfg = load_config(args.config)
    root = cfg["run"]["data_root"]
    run_name = cfg["run"]["name"]
    run_dir = os.path.join("runs", run_name)
    os.makedirs(run_dir, exist_ok=True)
    res_path = ensure_csv(os.path.join(run_dir, "results.csv"))
    log_path = os.path.join(run_dir, "stage_b.log")
    done = load_done(res_path)
    seed_all(cfg["run"].get("seed", 0))
    galleries = list_galleries(root)
    methods = args.methods.split(",") if args.methods else cfg["stage_b"]["methods"]
    tiers = args.tiers.split(",") if args.tiers else cfg["stage_b"]["tiers"]
    ids = args.ids.split(",") if args.ids else cfg["stage_b"]["ids"]
    if ids == ["all"]:
        ids = sorted({p for _, p in galleries})
    tr_cfg = cfg["stage_b"]
    n_per_prompt = max(1, cfg["run"]["samples_per_cell"] // len(PROMPTS))
    ref_per_id = cfg["run"].get("ref_per_id", 2)
    comps = load_sd15(cfg["run"]["sd_model"], fp16=cfg["run"].get("fp16", True))
    scorer = IdScorer(use_gpu=True)
    cells = [(m, p, t) for m in methods for p in ids for t in tiers]
    log(f"stage_b start cells={len(cells)} done={len(done)}", log_path)
    for m, pid, tier in cells:
        if (m, pid) not in galleries:
            log(f"missing gallery {m}/{pid}", log_path)
            continue
        key = ("B", pid, m, tier, "dreambooth")
        if key in done:
            continue
        paths = galleries[(m, pid)]
        tier_fn = get_tier(tier)
        imgs = [tier_fn(Image.open(p).convert("RGB")) for p in paths]
        reset_lora(comps["unet"])
        opt = add_lora(comps["unet"], rank=tr_cfg.get("lora_rank", 16), lr=tr_cfg.get("lr", 1e-4))
        comps["unet"].train()
        t0 = time.time()
        rng = np.random.default_rng(0)
        steps = tr_cfg.get("steps", 400)
        for st in range(steps):
            idx = rng.integers(0, len(imgs), size=min(4, len(imgs)))
            loss = dreambooth_loss(comps, [imgs[i] for i in idx], tr_cfg.get("prompt", PROMPTS[0]))
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_([p for p in comps["unet"].parameters() if p.requires_grad], 1.0)
            opt.step()
        train_sec = time.time() - t0
        comps["unet"].eval()
        ref_dir = os.path.join(root, "refs", pid)
        ref_paths = [os.path.join(ref_dir, f) for f in sorted(os.listdir(ref_dir))][:ref_per_id]
        ref_embs = scorer.ref_embeddings(pid, ref_paths)
        pipe = build_pipeline(comps)
        t1 = time.time()
        gens = generate_images(pipe, PROMPTS, n_per_prompt=n_per_prompt, steps=30,
                               guidance=7.5, seed=cfg["run"].get("seed", 0))
        gen_sec = time.time() - t1
        del pipe
        torch.cuda.empty_cache()
        sims = []
        for g in gens:
            s, _ = scorer.best_sim(g, ref_embs)
            sims.append(s)
        sims = np.array(sims, dtype=np.float64)
        mean, (lo, hi) = bootstrap_ci_mean(sims)
        tau = cfg["run"].get("tau", 0.30)
        append_row(res_path, dict(
            run=run_name, stage="B", pid=pid, method=m, tier=tier, attack="dreambooth",
            n_gallery=len(paths), n_samples=len(sims), mean_id=round(mean, 4),
            ci_lo=round(lo, 4), ci_hi=round(hi, 4), p_lo="", p_hi="",
            pos_rate=round(float(np.nanmean(sims >= tau)), 4),
            gen_sec=round(train_sec + gen_sec, 1),
            sec_per_img=round((train_sec + gen_sec) / max(1, len(sims)), 2), ts=now(),
        ))
        reset_lora(comps["unet"])
        torch.cuda.empty_cache()
        log(f"B {m}/{pid}/{tier} mean={mean:.3f} train={train_sec:.0f}s gen={gen_sec:.0f}s", log_path)


if __name__ == "__main__":
    main()
