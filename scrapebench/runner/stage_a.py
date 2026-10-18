import argparse
import json
import os
import shutil
import time
import numpy as np
from PIL import Image
from ..config import load_config
from ..funnel import get_tier
from ..attack.ip_adapter import ZeroShotFaceID
from ..attack.instantid import ZeroShotInstantID
from ..attack.train_utils import GAPDIFF_PROMPTS
from ..metrics.id_sim import IdScorer
from ..metrics.stats import bootstrap_ci_mean
from .results import ensure_csv, append_row, load_done, log, FIELDS, now


def list_galleries(data_root):
    root = os.path.join(data_root, "protected")
    out = {}
    if not os.path.isdir(root):
        return out
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
    ap.add_argument("--attack", default="ipfaceid")
    ap.add_argument("--run-name", default=None,
                    help="override config run name so pilot results cannot mix with legacy runs")
    ap.add_argument("--force", action="store_true", help="rerun selected cells even when a successful row exists")
    args = ap.parse_args()
    cfg = load_config(args.config)
    root = cfg["run"]["data_root"]
    run_name = args.run_name or cfg["run"]["name"]
    run_dir = os.path.join("runs", run_name)
    os.makedirs(run_dir, exist_ok=True)
    res_path = ensure_csv(os.path.join(run_dir, "results.csv"))
    log_path = os.path.join(run_dir, "stage_a.log")
    done = load_done(res_path)
    galleries = list_galleries(root)
    methods = args.methods.split(",") if args.methods else cfg["stage_a"]["methods"]
    tiers = args.tiers.split(",") if args.tiers else cfg["stage_a"]["tiers"]
    ids = args.ids.split(",") if args.ids else cfg["stage_a"]["ids"]
    if ids == ["all"]:
        ids = sorted({p for _, p in galleries})
    ref_per_id = cfg["run"].get("ref_per_id", 2)
    atk_cfg = cfg.get("attack", {})
    if args.attack == "instantid":
        zs = ZeroShotInstantID(
            adapter_repo=atk_cfg.get("instantid_repo", "InstantX/InstantID"),
            controlnet_repo=atk_cfg.get("instantid_controlnet", "InstantX/InstantID"),
            scale=atk_cfg.get("ip_adapter_scale", 0.8),
        )
    else:
        zs = ZeroShotFaceID(
            cfg["run"]["sd_model"],
            adapter_repo=atk_cfg.get("ip_adapter_repo", "h94/IP-Adapter-FaceID"),
            weight_name=atk_cfg.get("ip_adapter_weight", "ip-adapter-faceid_sd15.bin"),
            scale=atk_cfg.get("ip_adapter_scale", 0.8),
        )
    scorer = IdScorer(use_gpu=True)
    ref_cache = {}
    failed = 0
    cells = [(m, p, t) for m in methods for p in ids for t in tiers]
    log(f"stage_a start cells={len(cells)} done={len(done)}", log_path)
    for m, pid, tier in cells:
        if (m, pid) not in galleries:
            log(f"missing gallery {m}/{pid}", log_path)
            failed += 1
            continue
        key = ("A", pid, m, tier, args.attack)
        if key in done and not args.force:
            continue
        paths = galleries[(m, pid)]
        ref_dir = os.path.join(root, "refs", pid)
        ref_paths = [os.path.join(ref_dir, f) for f in sorted(os.listdir(ref_dir))][:ref_per_id]
        if pid not in ref_cache:
            ref_cache[pid] = scorer.ref_embeddings(pid, ref_paths)
        ref_embs = ref_cache[pid]
        if not ref_embs:
            log(f"no refs {m}/{pid}", log_path)
            failed += 1
            continue
        tier_fn = get_tier(tier)
        imgs = [tier_fn(Image.open(p).convert("RGB")) for p in paths]
        t0 = time.time()
        try:
            # Both readers must see the identical preregistered scenario set;
            # earlier smoke runs used 2 prompts for InstantID and 5 for
            # IP-Adapter, which was suitable only for plumbing validation.
            prompts = cfg["stage_a"].get("prompts", GAPDIFF_PROMPTS)
            steps = (atk_cfg.get("instantid_steps", atk_cfg.get("steps", 30))
                     if args.attack == "instantid" else atk_cfg.get("steps", 30))
            gens = zs.generate(prompts, imgs, n_per_prompt=max(1, cfg["run"]["samples_per_cell"] // len(prompts)),
                               steps=steps, guidance=atk_cfg.get("guidance", 5.0),
                               seed=cfg["run"].get("seed", 0))
        except RuntimeError as e:
            append_row(res_path, dict(
                run=run_name, stage="A", pid=pid, method=m, tier=tier, attack=args.attack,
                n_gallery=len(paths), n_samples=0, mean_id="", ci_lo="", ci_hi="", p_lo="", p_hi="",
                pos_rate=0.0, gen_sec=round(time.time() - t0, 1), sec_per_img="", ts=now()))
            log(f"skip {m}/{pid}/{tier}: {e}", log_path)
            failed += 1
            continue
        gen_sec = time.time() - t0
        sims = []
        dets = []
        save_outputs = bool(cfg["stage_a"].get("save_outputs", False))
        output_dir = os.path.join(run_dir, "generations", args.attack, m, tier, pid)
        if save_outputs:
            if args.force and os.path.isdir(output_dir):
                shutil.rmtree(output_dir)
            os.makedirs(output_dir, exist_ok=True)
        sample_rows = []
        for idx, g in enumerate(gens):
            s, ok = scorer.best_sim(g, ref_embs)
            sims.append(s)
            dets.append(bool(ok))
            if save_outputs:
                prompt_idx = idx // max(1, cfg["run"]["samples_per_cell"] // len(prompts))
                filename = f"p{prompt_idx:02d}_s{idx:03d}.png"
                g.save(os.path.join(output_dir, filename))
                sample_rows.append({
                    "pid": pid, "method": m, "tier": tier, "attack": args.attack,
                    "prompt_id": prompt_idx, "prompt": prompts[min(prompt_idx, len(prompts) - 1)],
                    "file": filename, "ism": None if np.isnan(s) else round(float(s), 6),
                    "detected": bool(ok),
                })
        if save_outputs:
            with open(os.path.join(output_dir, "samples.jsonl"), "w") as handle:
                for row in sample_rows:
                    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        sims = np.array(sims, dtype=np.float64)
        mean, (lo, hi) = bootstrap_ci_mean(sims)
        det_rate = float(np.mean(dets))
        tau = cfg["run"].get("tau", 0.30)
        append_row(res_path, dict(
            run=run_name, stage="A", pid=pid, method=m, tier=tier, attack=args.attack,
            n_gallery=len(paths), n_samples=len(sims), mean_id=round(mean, 4),
            ci_lo=round(lo, 4), ci_hi=round(hi, 4), p_lo="", p_hi="",
            pos_rate=round(float(np.nanmean(sims >= tau)), 4),
            gen_sec=round(gen_sec, 1), sec_per_img=round(gen_sec / max(1, len(sims)), 2), ts=now(),
        ))
        log(f"A {m}/{pid}/{tier} mean={mean:.3f} det={det_rate:.2f} {gen_sec:.0f}s", log_path)
    if failed:
        log(f"stage_a incomplete failed_cells={failed}", log_path)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
