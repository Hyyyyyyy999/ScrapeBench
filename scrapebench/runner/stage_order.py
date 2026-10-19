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
from ..attack.train_utils import PROMPTS
from ..metrics.id_sim import IdScorer
from ..metrics.stats import bootstrap_ci_mean
from .results import ensure_csv, append_row, load_done, log, now
from .stage_a import list_galleries

from .orders import ORDERS


def compose(names):
    fns = [get_tier(t) for t in names]

    def chain(img):
        for f in fns:
            img = f(img)
        return img
    return chain


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--methods", default="fsmg,random,clean")
    ap.add_argument("--ids", default=None)
    ap.add_argument("--orders", default=None)
    ap.add_argument("--attack", choices=("ipfaceid", "instantid"), default="ipfaceid")
    ap.add_argument("--run-name", default=None)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    cfg = load_config(args.config)
    root = cfg["run"]["data_root"]
    run_name = args.run_name or cfg["run"]["name"]
    run_dir = os.path.join("runs", run_name)
    res_path = ensure_csv(os.path.join(run_dir, "results.csv"))
    log_path = os.path.join(run_dir, "stage_order.log")
    done = load_done(res_path)
    galleries = list_galleries(root)
    methods = args.methods.split(",")
    ids = args.ids.split(",") if args.ids else None
    if ids is None:
        ids = sorted({p for m, p in galleries if m == "fsmg"})[:6]
    n_per_prompt = max(1, cfg["run"]["samples_per_cell"] // len(PROMPTS))
    ref_per_id = cfg["run"].get("ref_per_id", 2)
    orders = args.orders.split(",") if args.orders else list(ORDERS)
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
    cells = [(m, p, o) for m in methods for p in ids for o in orders]
    failed = 0
    log(f"stage_order start cells={len(cells)} done={len(done)}", log_path)
    for m, pid, order in cells:
        if (m, pid) not in galleries:
            log(f"missing gallery {m}/{pid}", log_path)
            failed += 1
            continue
        key = ("O", pid, m, order, args.attack)
        if key in done and not args.force:
            continue
        paths = galleries[(m, pid)]
        ref_dir = os.path.join(root, "refs", pid)
        ref_paths = [os.path.join(ref_dir, f) for f in sorted(os.listdir(ref_dir))][:ref_per_id]
        ref_embs = scorer.ref_embeddings(pid, ref_paths)
        if not ref_embs:
            log(f"no refs {m}/{pid}", log_path)
            failed += 1
            continue
        fn = compose(ORDERS[order])
        imgs = [fn(Image.open(p).convert("RGB")) for p in paths]
        t0 = time.time()
        try:
            prompts = cfg.get("stage_a", {}).get("prompts", PROMPTS)
            gens = zs.generate(prompts, imgs, n_per_prompt=n_per_prompt,
                               steps=(atk_cfg.get("instantid_steps", 30) if args.attack == "instantid" else atk_cfg.get("steps", 30)),
                               guidance=atk_cfg.get("guidance", 5.0),
                               seed=cfg["run"].get("seed", 0))
        except RuntimeError as e:
            append_row(res_path, dict(
                run=run_name, stage="O", pid=pid, method=m, tier=order, attack=args.attack,
                n_gallery=len(paths), n_samples=0, mean_id="", ci_lo="", ci_hi="", p_lo="", p_hi="",
                pos_rate=0.0, gen_sec=round(time.time() - t0, 1), sec_per_img="", ts=now()))
            log(f"skip {m}/{pid}/{order}: {e}", log_path)
            failed += 1
            continue
        gen_sec = time.time() - t0
        sims = []
        dets = []
        output_dir = os.path.join(run_dir, "generations", args.attack + "_chain", m, order, pid)
        if args.force and os.path.isdir(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        sample_rows = []
        for idx, g in enumerate(gens):
            s, ok = scorer.best_sim(g, ref_embs)
            sims.append(s)
            dets.append(bool(ok))
            prompt_idx = idx // n_per_prompt
            filename = f"p{prompt_idx:02d}_s{idx:03d}.png"
            g.save(os.path.join(output_dir, filename))
            sample_rows.append({"pid": pid, "method": m, "order": order,
                                "attack": args.attack, "prompt_id": prompt_idx,
                                "prompt": prompts[min(prompt_idx, len(prompts)-1)],
                                "file": filename,
                                "ism": None if np.isnan(s) else round(float(s), 6),
                                "detected": bool(ok)})
        with open(os.path.join(output_dir, "samples.jsonl"), "w") as handle:
            for row in sample_rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        sims = np.array(sims, dtype=np.float64)
        mean, (lo, hi) = bootstrap_ci_mean(sims)
        tau = cfg["run"].get("tau", 0.30)
        append_row(res_path, dict(
            run=run_name, stage="O", pid=pid, method=m, tier=order, attack=args.attack,
            n_gallery=len(paths), n_samples=len(sims), mean_id=round(mean, 4),
            ci_lo=round(lo, 4), ci_hi=round(hi, 4), p_lo="", p_hi="",
            pos_rate=round(float(np.nanmean(sims >= tau)), 4),
            gen_sec=round(gen_sec, 1), sec_per_img=round(gen_sec / max(1, len(sims)), 2), ts=now(),
        ))
        log(f"O {m}/{pid}/{order} mean={mean:.3f} det={np.mean(dets):.2f} {gen_sec:.0f}s", log_path)
    if failed:
        log(f"stage_order incomplete failed_cells={failed}", log_path)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
