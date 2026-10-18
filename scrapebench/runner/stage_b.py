import argparse
import json
import os
import time
import numpy as np
import torch
from PIL import Image
from ..config import load_config
from ..funnel import get_tier
from ..attack.train_utils import load_sd15, load_gallery, build_pipeline, generate_images, add_lora, reset_lora, dreambooth_loss, dreambooth_prior_loss, PROMPTS, CLASS_PROMPT
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
    ap.add_argument("--steps", type=int, default=None)
    ap.add_argument("--samples-per-prompt", type=int, default=None)
    ap.add_argument("--force", action="store_true")
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
    prompts = tr_cfg.get("prompts", PROMPTS)
    n_per_prompt = args.samples_per_prompt or tr_cfg.get(
        "samples_per_prompt", max(1, cfg["run"]["samples_per_cell"] // len(prompts))
    )
    ref_per_id = cfg["run"].get("ref_per_id", 2)
    comps = load_sd15(tr_cfg.get("model", cfg["run"]["sd_model"]),
                      fp16=cfg["run"].get("fp16", True))
    training_mode = tr_cfg.get("training_mode", "lora")
    base_unet_state = None
    base_text_state = None
    if training_mode == "full_unet":
        # GAP-Diff trains DreamBooth's UNet rather than a LoRA adapter.  Keep a
        # CPU checkpoint so every method/tier/identity cell starts identically.
        base_unet_state = {k: v.detach().cpu().clone() for k, v in comps["unet"].state_dict().items()}
        base_text_state = {k: v.detach().cpu().clone() for k, v in comps["text_encoder"].state_dict().items()}
    class_dir = tr_cfg.get("class_data_dir")
    if not class_dir or not os.path.isdir(class_dir):
        raise RuntimeError(f"DreamBooth class_data_dir is missing: {class_dir}")
    class_paths = [os.path.join(class_dir, name) for name in sorted(os.listdir(class_dir))
                   if name.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))]
    if len(class_paths) < tr_cfg.get("num_class_images", 200):
        raise RuntimeError(f"need {tr_cfg.get('num_class_images', 200)} class images, found {len(class_paths)}")
    class_images = [Image.open(path).convert("RGB").resize((512, 512))
                    for path in class_paths[:tr_cfg.get("num_class_images", 200)]]
    scorer = IdScorer(use_gpu=True)
    cells = [(m, p, t) for m in methods for p in ids for t in tiers]
    log(f"stage_b start cells={len(cells)} done={len(done)}", log_path)
    for m, pid, tier in cells:
        if (m, pid) not in galleries:
            log(f"missing gallery {m}/{pid}", log_path)
            continue
        key = ("B", pid, m, tier, "dreambooth")
        if key in done and not args.force:
            continue
        paths = galleries[(m, pid)]
        tier_fn = get_tier(tier)
        imgs = [tier_fn(Image.open(p).convert("RGB")) for p in paths]
        reset_lora(comps["unet"])
        if training_mode == "full_unet":
            comps["unet"].load_state_dict(base_unet_state)
            comps["text_encoder"].load_state_dict(base_text_state)
            comps["unet"].requires_grad_(True)
            comps["text_encoder"].requires_grad_(True)
            params = list(comps["unet"].parameters()) + list(comps["text_encoder"].parameters())
            opt = torch.optim.AdamW(params, lr=tr_cfg.get("lr", 5e-7))
        else:
            opt = add_lora(comps["unet"], rank=tr_cfg.get("lora_rank", 16), lr=tr_cfg.get("lr", 1e-4))
        comps["unet"].train()
        t0 = time.time()
        rng = np.random.default_rng(0)
        steps = args.steps or tr_cfg.get("steps", 400)
        for st in range(steps):
            batch_size = tr_cfg.get("batch_size", 1 if training_mode == "full_unet" else 4)
            idx = rng.integers(0, len(imgs), size=min(batch_size, len(imgs)))
            if training_mode == "full_unet":
                class_idx = rng.integers(0, len(class_images), size=len(idx))
                loss = dreambooth_prior_loss(
                    comps, [imgs[i] for i in idx], [class_images[i] for i in class_idx],
                    tr_cfg.get("prompt", PROMPTS[0]),
                    tr_cfg.get("class_prompt", CLASS_PROMPT),
                    tr_cfg.get("prior_loss_weight", 1.0),
                )
            else:
                loss = dreambooth_loss(comps, [imgs[i] for i in idx], tr_cfg.get("prompt", PROMPTS[0]))
            opt.zero_grad(set_to_none=True)
            loss.backward()
            trainable = ([p for p in comps["unet"].parameters() if p.requires_grad] +
                         [p for p in comps["text_encoder"].parameters() if p.requires_grad])
            torch.nn.utils.clip_grad_norm_(trainable, 1.0)
            opt.step()
        train_sec = time.time() - t0
        comps["unet"].eval()
        ref_dir = os.path.join(root, "refs", pid)
        ref_paths = [os.path.join(ref_dir, f) for f in sorted(os.listdir(ref_dir))][:ref_per_id]
        ref_embs = scorer.ref_embeddings(pid, ref_paths)
        if not ref_embs:
            log(f"no refs {m}/{pid}", log_path)
            continue
        pipe = build_pipeline(comps)
        t1 = time.time()
        gens = generate_images(pipe, prompts, n_per_prompt=n_per_prompt,
                               steps=tr_cfg.get("generation_steps", 30),
                               guidance=7.5, seed=cfg["run"].get("seed", 0))
        gen_sec = time.time() - t1
        del pipe
        torch.cuda.empty_cache()
        sims = []
        detections = []
        save_outputs = bool(tr_cfg.get("save_outputs", False))
        output_dir = os.path.join(run_dir, "generations", "dreambooth", m, tier, pid)
        if save_outputs:
            os.makedirs(output_dir, exist_ok=True)
        sample_rows = []
        for idx, g in enumerate(gens):
            s, detected = scorer.best_sim(g, ref_embs)
            sims.append(s)
            detections.append(bool(detected))
            prompt_idx = idx // n_per_prompt
            if save_outputs:
                filename = f"p{prompt_idx:02d}_s{idx % n_per_prompt:03d}.png"
                g.save(os.path.join(output_dir, filename))
                sample_rows.append({
                    "pid": pid, "method": m, "tier": tier,
                    "prompt_id": prompt_idx, "prompt": prompts[prompt_idx],
                    "sample_id": idx % n_per_prompt, "file": filename,
                    "ism": None if np.isnan(s) else round(float(s), 6),
                    "detected": bool(detected),
                })
        if save_outputs:
            with open(os.path.join(output_dir, "samples.jsonl"), "w") as handle:
                for row in sample_rows:
                    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
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
        if training_mode == "full_unet":
            comps["unet"].requires_grad_(False)
            comps["text_encoder"].requires_grad_(False)
        torch.cuda.empty_cache()
        log(f"B {m}/{pid}/{tier} mean={mean:.3f} train={train_sec:.0f}s gen={gen_sec:.0f}s", log_path)


if __name__ == "__main__":
    main()
