#!/usr/bin/env python3
"""Audit realized upload distortion for the fixed four-identity pilot."""
import argparse
import csv
import math
from pathlib import Path

import numpy as np
from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", default="celeb00001,celeb00002,celeb00003,celeb00004")
    ap.add_argument("--methods", default="gapdiff,metacloak,goodac,arcp_web_v4")
    ap.add_argument("--output", default="runs/web4_validation/protection_quality.csv")
    args = ap.parse_args()
    rows = []
    for method in args.methods.split(","):
        for pid in args.ids.split(","):
            clean = sorted((Path("data/web40/protected/clean") / pid).glob("*"))
            protected = sorted((Path("data/web40/protected") / method / pid).glob("*"))
            if len(clean) != 4 or len(protected) != 4:
                continue
            linfs, psnrs = [], []
            for cpath, ppath in zip(clean, protected):
                c = np.asarray(Image.open(cpath).convert("RGB"), dtype=np.float32)
                p = np.asarray(Image.open(ppath).convert("RGB").resize((c.shape[1], c.shape[0])), dtype=np.float32)
                diff = p - c
                linfs.append(float(np.max(np.abs(diff))))
                mse = float(np.mean(diff * diff))
                psnrs.append(math.inf if mse == 0 else 10 * math.log10(255 * 255 / mse))
            rows.append({"method": method, "pid": pid, "images": 4,
                         "linf_px_max": max(linfs), "psnr_db_mean": np.mean(psnrs)})
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader(); writer.writerows(rows)
    for method in args.methods.split(","):
        subset = [r for r in rows if r["method"] == method]
        if subset:
            print(f"{method}: ids={len(subset)} linf_px={max(r['linf_px_max'] for r in subset):.0f} "
                  f"mean_psnr={np.mean([r['psnr_db_mean'] for r in subset]):.2f} dB")


if __name__ == "__main__":
    main()
