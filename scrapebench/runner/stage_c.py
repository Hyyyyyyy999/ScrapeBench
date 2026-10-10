import argparse
import os
import time
import numpy as np
import torch
from PIL import Image
from ..config import load_config
from ..attack.train_utils import load_sd15, build_pipeline, generate_images, add_lora, reset_lora, dreambooth_loss, PROMPTS, seed_all
from ..metrics.id_sim import IdScorer
from ..metrics.stats import bootstrap_ci_mean
from .results import ensure_csv, append_row, load_done, log, now


def gallery_paths(data_root, method, pid):
    d = os.path.join(data_root, "protected", method, pid)
    if not os.path.isdir(d):
        return []
    return [os.path.join(d, i) for i in sorted(os.listdir(d)) if i.lower().endswith((".png", ".jpg", ".jpeg"))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--ids", default=None)
    args = ap.parse_args()
    cfg = load_config(args.config)
    root = cfg["run"]["data_root"]
    run_name = cfg["run"]["name"]
    run_dir = os.path.join("runs", run_name)
    os.makedirs(run_dir, exist_ok=True)
    res_path = ensure_csv(os.path.join(run_dir, "results.csv"))
    log_path = os.path.join(run_dir, "stage_c.log")
    done = load_done(res_path)
    seed_all(cfg["run"].get("seed", 0))
    ids = args.ids.split(",") if args.ids else cfg["stage_c"]["ids"]
    if ids == ["all"]:
        ids = sorted(os.listdir(os.path.join(root, "protected", "fsmg"))) if os.path.isdir(os.path.join(root, "protected", "fsmg")) else []
    ratios = cfg["stage_c"].get("mix_ratios", [0.2, 0.5])
    tr_cfg = cfg["stage_c"]
    n_per_prompt = max(1, cfg["run"]["samples_per_cell"] // len(PROMPTS))
    ref_per_id = cfg["run"].get("ref_per_id", 2)
    comps = load_sd15(cfg["run"]["sd_model"], fp16=cfg["run"].get("fp16", True))
    scorer = IdScorer(use_gpu=True)
    all_ids = ids
    cells = []
    for pid in ids:
        for r in ratios:
            cells.append((pid, f"mix{int(r * 100)}", r))
        cells.append((pid, "purify50", None))
    log(f"stage_c start cells={len(cells)} done={len(done)}", log_path)
    for pid, tag, r in cells:
        key = ("C", pid, "fsmg", tag, "dreambooth")
        if key in done:
            continue
        prot = gallery_paths(root, "fsmg", pid)
        if not prot:
            continue
        imgs = [Image.open(p).convert("RGB").resize((512, 512), Image.LANCZOS) for p in prot]
        if tag.startswith("mix"):
            others = [q for q in all_ids if q != pid]
            np.random.shuffle(others)
            n_clean = int(round(r / (1 - r) * len(imgs)))
            clean_imgs = []
            for q in others:
                for p in gallery_paths(root, "clean", q):
                    clean_imgs.append(Image.open(p).convert("RGB").resize((512, 512), Image.LANCZOS))
                    if len(clean_imgs) >= n_clean:
                        break
                if len(clean_imgs) >= n_clean:
                    break
            imgs = imgs + clean_imgs
            np.random.shuffle(imgs)
        reset_lora(comps["unet"])
        opt = add_lora(comps["unet"], rank=tr_cfg.get("lora_rank", 16), lr=tr_cfg.get("lr", 1e-4))
        comps["unet"].train()
        t0 = time.time()
        rng = np.random.default_rng(0)
        for st in range(tr_cfg.get("steps", 400)):
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
        if not ref_embs:
            log(f"no refs {pid}", log_path)
            continue
        pipe = build_pipeline(comps)
        gens = generate_images(pipe, PROMPTS, n_per_prompt=n_per_prompt, steps=30, guidance=7.5, seed=cfg["run"].get("seed", 0))
        del pipe
        torch.cuda.empty_cache()
        sims = [scorer.best_sim(g, ref_embs)[0] for g in gens]
        sims = np.array(sims, dtype=np.float64)
        mean, (lo, hi) = bootstrap_ci_mean(sims)
        tau = cfg["run"].get("tau", 0.30)
        append_row(res_path, dict(
            run=run_name, stage="C", pid=pid, method="fsmg", tier=tag, attack="dreambooth",
            n_gallery=len(imgs), n_samples=len(sims), mean_id=round(mean, 4),
            ci_lo=round(lo, 4), ci_hi=round(hi, 4), p_lo="", p_hi="",
            pos_rate=round(float(np.nanmean(sims >= tau)), 4),
            gen_sec=round(train_sec, 1), sec_per_img=round(train_sec / max(1, len(sims)), 2), ts=now(),
        ))
        reset_lora(comps["unet"])
        log(f"C {pid}/{tag} mean={mean:.3f} train={train_sec:.0f}s", log_path)


if __name__ == "__main__":
    main()
