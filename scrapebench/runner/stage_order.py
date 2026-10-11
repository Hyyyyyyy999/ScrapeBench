import argparse
import os
import time
import numpy as np
from PIL import Image
from ..config import load_config
from ..funnel import get_tier
from ..attack.ip_adapter import ZeroShotFaceID
from ..attack.train_utils import PROMPTS
from ..metrics.id_sim import IdScorer
from ..metrics.stats import bootstrap_ci_mean
from .results import ensure_csv, append_row, load_done, log, now
from .stage_a import list_galleries

ORDERS = {
    "canonical": ["t1_jpeg85", "t2_canvas_dpr1", "t4_sr_x2", "t5_i2i30"],
    "sr_first": ["t4_sr_x2", "t1_jpeg85", "t2_canvas_dpr1"],
    "t5_first": ["t5_i2i30", "t1_jpeg85"],
    "jpeg_only": ["t1_jpeg85"],
    "deep_chain": ["t1_jpeg85", "t2_canvas_dpr1", "t4_sr_x2", "t5_i2i30", "t4_sr_x2"],
    "t5_only": ["t5_i2i30"],
}


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
    args = ap.parse_args()
    cfg = load_config(args.config)
    root = cfg["run"]["data_root"]
    run_name = cfg["run"]["name"]
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
    atk_cfg = cfg.get("attack", {})
    zs = ZeroShotFaceID(
        cfg["run"]["sd_model"],
        adapter_repo=atk_cfg.get("ip_adapter_repo", "h94/IP-Adapter-FaceID"),
        weight_name=atk_cfg.get("ip_adapter_weight", "ip-adapter-faceid_sd15.bin"),
        scale=atk_cfg.get("ip_adapter_scale", 0.8),
    )
    scorer = IdScorer(use_gpu=True)
    cells = [(m, p, o) for m in methods for p in ids for o in ORDERS]
    log(f"stage_order start cells={len(cells)} done={len(done)}", log_path)
    for m, pid, order in cells:
        if (m, pid) not in galleries:
            continue
        key = ("O", pid, m, order, "ipfaceid")
        if key in done:
            continue
        paths = galleries[(m, pid)]
        ref_dir = os.path.join(root, "refs", pid)
        ref_paths = [os.path.join(ref_dir, f) for f in sorted(os.listdir(ref_dir))][:ref_per_id]
        ref_embs = scorer.ref_embeddings(pid, ref_paths)
        if not ref_embs:
            log(f"no refs {m}/{pid}", log_path)
            continue
        fn = compose(ORDERS[order])
        imgs = [fn(Image.open(p).convert("RGB")) for p in paths]
        t0 = time.time()
        try:
            gens = zs.generate(PROMPTS, imgs, n_per_prompt=n_per_prompt,
                               steps=atk_cfg.get("steps", 30), guidance=atk_cfg.get("guidance", 5.0),
                               seed=cfg["run"].get("seed", 0))
        except RuntimeError as e:
            append_row(res_path, dict(
                run=run_name, stage="O", pid=pid, method=m, tier=order, attack="ipfaceid",
                n_gallery=len(paths), n_samples=0, mean_id="", ci_lo="", ci_hi="", p_lo="", p_hi="",
                pos_rate=0.0, gen_sec=round(time.time() - t0, 1), sec_per_img="", ts=now()))
            log(f"skip {m}/{pid}/{order}: {e}", log_path)
            continue
        gen_sec = time.time() - t0
        sims = []
        for g in gens:
            s, _ = scorer.best_sim(g, ref_embs)
            sims.append(s)
        sims = np.array(sims, dtype=np.float64)
        mean, (lo, hi) = bootstrap_ci_mean(sims)
        tau = cfg["run"].get("tau", 0.30)
        append_row(res_path, dict(
            run=run_name, stage="O", pid=pid, method=m, tier=order, attack="ipfaceid",
            n_gallery=len(paths), n_samples=len(sims), mean_id=round(mean, 4),
            ci_lo=round(lo, 4), ci_hi=round(hi, 4), p_lo="", p_hi="",
            pos_rate=round(float(np.nanmean(sims >= tau)), 4),
            gen_sec=round(gen_sec, 1), sec_per_img=round(gen_sec / max(1, len(sims)), 2), ts=now(),
        ))
        log(f"O {m}/{pid}/{order} mean={mean:.3f} {gen_sec:.0f}s", log_path)


if __name__ == "__main__":
    main()
