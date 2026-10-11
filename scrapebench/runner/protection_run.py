import argparse
import os
import shutil
import numpy as np
from PIL import Image
from ..config import load_config
from ..attack.train_utils import load_sd15
from ..protection.fsmg import train_surrogate, pgd_fsmg
from ..protection.random_noise import make_random_noise
from ..metrics.quality import psnr
from .results import log


def list_galleries(data_root):
    out = {}
    root = os.path.join(data_root, "raw")
    if not os.path.isdir(root):
        return out
    for pid in sorted(os.listdir(root)):
        d = os.path.join(root, pid)
        if os.path.isdir(d):
            imgs = sorted(os.listdir(d))
            out[pid] = [os.path.join(d, i) for i in imgs if i.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))]
    return out


def generate_method(method, comps, gallery_paths, cfg, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    res = cfg["run"].get("resolution", 512)
    if method == "clean":
        for i, p in enumerate(gallery_paths):
            im = Image.open(p).convert("RGB")
            s = min(im.size)
            im = im.crop(((im.width - s) // 2, (im.height - s) // 2, (im.width + s) // 2, (im.height + s) // 2)).resize((res, res), Image.LANCZOS)
            im.save(os.path.join(out_dir, f"{i:04d}.png"))
        return None
    imgs = [Image.open(p).convert("RGB").resize((res, res), Image.LANCZOS) for p in gallery_paths]
    prot_cfg = cfg.get("protection", {})
    eps = prot_cfg.get("eps", 8.0) / 255.0
    if method == "random":
        outs = make_random_noise(imgs, eps=eps, seed=0)
    elif method == "fsmg":
        train_surrogate(comps, imgs, steps=prot_cfg.get("surrogate_steps", 200), batch_size=4, log_every=50)
        outs = pgd_fsmg(comps, imgs, eps=eps, alpha=prot_cfg.get("alpha", 1.0) / 255.0, steps=prot_cfg.get("pgd_steps", 100))
    elif method == "fsmgj":
        jq = int(prot_cfg.get("jpeg_aware", 85))
        train_surrogate(comps, imgs, steps=prot_cfg.get("surrogate_steps", 200), batch_size=4, log_every=50, jpeg_aware=jq)
        outs = pgd_fsmg(comps, imgs, eps=eps, alpha=prot_cfg.get("alpha", 1.0) / 255.0, steps=prot_cfg.get("pgd_steps", 100), jpeg_aware=jq)
    else:
        raise ValueError(f"unknown method {method}")
    for i, im in enumerate(outs):
        im.save(os.path.join(out_dir, f"{i:04d}.png"))
    return float(np.mean([psnr(a, b) for a, b in zip(imgs, outs)]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--methods", default=None)
    ap.add_argument("--ids", default=None)
    args = ap.parse_args()
    cfg = load_config(args.config)
    root = cfg["run"]["data_root"]
    methods = (args.methods.split(",") if args.methods else cfg.get("protection", {}).get("methods", ["clean", "random", "fsmg"]))
    galleries = list_galleries(root)
    ids = args.ids.split(",") if args.ids else sorted(galleries)
    need_model = any(m in ("fsmg", "aspl") for m in methods)
    comps = None
    if need_model:
        comps = load_sd15(cfg["run"]["sd_model"], fp16=cfg["run"].get("fp16", True))
        from ..protection.fsmg import reset_lora
    for m in methods:
        if m == "aspl":
            from ..protection.aspl_lite import aspl_lite
        for pid in ids:
            paths = galleries.get(pid)
            if not paths:
                continue
            n_refs = len(os.listdir(os.path.join(root, "refs", pid))) if os.path.isdir(os.path.join(root, "refs", pid)) else 0
            if n_refs < 2:
                log(f"skip {m}/{pid} refs={n_refs}", cfg["run"].get("log_file"))
                continue
            out_dir = os.path.join(root, "protected", m, pid)
            if os.path.isdir(out_dir) and len(os.listdir(out_dir)) >= len(paths):
                log(f"skip {m}/{pid}", cfg["run"].get("log_file"))
                continue
            if m == "aspl":
                p = cfg.get("protection", {})
                aspl_lite(comps, paths, out_dir, eps=p.get("eps", 8) / 255.0, alpha=p.get("alpha", 1.0) / 255.0,
                          outer_rounds=p.get("aspl_rounds", 2), surrogate_steps=p.get("surrogate_steps", 200),
                          pgd_steps=p.get("pgd_steps", 100))
                continue
            psnr_val = generate_method(m, comps, paths, cfg, out_dir)
            if psnr_val is not None:
                log(f"{m}/{pid} psnr={psnr_val:.2f}", cfg["run"].get("log_file"))
            if m == "fsmg" and comps is not None:
                reset_lora(comps["unet"])


if __name__ == "__main__":
    main()
