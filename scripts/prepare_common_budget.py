#!/usr/bin/env python3
"""Project released protected galleries to a strict 8-bit L_inf budget.

The projected rows supplement, rather than replace, the official-default rows.
Projection is performed against the uniformly ingested clean PNG for each ID.
"""
import argparse
import csv
from pathlib import Path

import numpy as np
from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="data/web40")
    ap.add_argument("--budget", type=int, default=8)
    ap.add_argument("--methods", default="gapdiff,idprotector")
    args = ap.parse_args()
    root = Path(args.root)
    rows = []
    ids = sorted(p.name for p in (root / "raw").iterdir() if p.is_dir())
    for method in args.methods.split(","):
        target = f"{method}_{args.budget}"
        for pid in ids:
            clean_files = sorted((root / "protected" / "clean" / pid).glob("*.png"))
            source_files = sorted((root / "protected" / method / pid).glob("*.png"))
            if len(clean_files) != 4 or len(source_files) != 4:
                raise SystemExit(f"expected four clean/source PNGs for {method}/{pid}")
            out_dir = root / "protected" / target / pid
            out_dir.mkdir(parents=True, exist_ok=True)
            for clean_path, source_path in zip(clean_files, source_files):
                clean = np.asarray(Image.open(clean_path).convert("RGB"), dtype=np.int16)
                source = np.asarray(Image.open(source_path).convert("RGB"), dtype=np.int16)
                if clean.shape != source.shape:
                    raise SystemExit(f"shape mismatch: {clean_path} vs {source_path}")
                projected = np.clip(source, clean - args.budget, clean + args.budget)
                projected = np.clip(projected, 0, 255).astype(np.uint8)
                Image.fromarray(projected, "RGB").save(out_dir / clean_path.name)
                delta = projected.astype(np.float64) - clean.astype(np.float64)
                mse = float(np.mean(delta * delta))
                rows.append({"method": target, "pid": pid, "file": clean_path.name,
                             "linf": int(np.max(np.abs(delta))),
                             "psnr": float("inf") if mse == 0 else 10 * np.log10(255 ** 2 / mse)})
    report = Path("runs/web40_single_intervention/common_budget_audit.csv")
    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader(); writer.writerows(rows)
    print(f"wrote {len(rows)} projected images and {report}")


if __name__ == "__main__":
    main()
