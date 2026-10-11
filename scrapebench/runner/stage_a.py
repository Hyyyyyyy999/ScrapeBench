import argparse
import os
import time
import numpy as np
from PIL import Image
from ..config import load_config
from ..funnel import get_tier
from ..attack.ip_adapter import ZeroShotFaceID
from ..attack.instantid import ZeroShotInstantID
from ..attack.train_utils import PROMPTS
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
    args = ap.parse_args()
    cfg = load_config(args.config)
    root = cfg["run"]["data_root"]
    run_name = cfg["run"]["name"]
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
    n_per_prompt = max(1, cfg["run"]["samples_per_cell"] // len(PROMPTS))
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
    cells = [(m, p, t) for m in methods for p in ids for t in tiers]
    log(f"stage_a start cells={len(cells)} done={len(done)}", log_path)
    for m, pid, tier in cells:
        if (m, pid) not in galleries:
            log(f"missing gallery {m}/{pid}", log_path)
            continue
        key = ("A", pid, m, tier, args.attack)
        if key in done:
            continue
        paths = galleries[(m, pid)]
        ref_dir = os.path.join(root, "refs", pid)
        ref_paths = [os.path.join(ref_dir, f) for f in sorted(os.listdir(ref_dir))][:ref_per_id]
        if pid not in ref_cache:
            ref_cache[pid] = scorer.ref_embeddings(pid, ref_paths)
        ref_embs = ref_cache[pid]
        if not ref_embs:
            log(f"no refs {m}/{pid}", log_path)
            continue
        tier_fn = get_tier(tier)
        imgs = [tier_fn(Image.open(p).convert("RGB")) for p in paths]
        t0 = time.time()
        try:
            prompts = PROMPTS[:2] if args.attack == "instantid" else PROMPTS
            gens = zs.generate(prompts, imgs, n_per_prompt=max(1, cfg["run"]["samples_per_cell"] // len(prompts)),
                               steps=atk_cfg.get("steps", 30), guidance=atk_cfg.get("guidance", 5.0),
                               seed=cfg["run"].get("seed", 0))
        except RuntimeError as e:
            append_row(res_path, dict(
                run=run_name, stage="A", pid=pid, method=m, tier=tier, attack=args.attack,
                n_gallery=len(paths), n_samples=0, mean_id="", ci_lo="", ci_hi="", p_lo="", p_hi="",
                pos_rate=0.0, gen_sec=round(time.time() - t0, 1), sec_per_img="", ts=now()))
            log(f"skip {m}/{pid}/{tier}: {e}", log_path)
            continue
        gen_sec = time.time() - t0
        sims = []
        dets = []
        for g in gens:
            s, ok = scorer.best_sim(g, ref_embs)
            sims.append(s)
            dets.append(bool(ok))
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


if __name__ == "__main__":
    main()
