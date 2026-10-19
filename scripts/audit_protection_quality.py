#!/usr/bin/env python3
"""Audit realized 8-bit distortion for completed Web40 protection galleries."""
import csv
from pathlib import Path
import numpy as np
from PIL import Image

root = Path("data/web40/protected")
methods = ("gapdiff", "idprotector", "gapdiff_8", "idprotector_8", "arcp_web_v4")
rows = []
for method in methods:
    for protected in sorted((root / method).glob("*/*.png")):
        clean = root / "clean" / protected.parent.name / protected.name
        if not clean.is_file(): raise SystemExit(f"missing clean pair for {protected}")
        a = np.asarray(Image.open(clean).convert("RGB"), dtype=np.float64)
        b = np.asarray(Image.open(protected).convert("RGB"), dtype=np.float64)
        d = b - a; mse = float(np.mean(d * d))
        rows.append({"method": method, "pid": protected.parent.name, "file": protected.name,
                     "linf": int(np.max(np.abs(d))),
                     "psnr": float("inf") if mse == 0 else 10 * np.log10(255 ** 2 / mse)})
for method in methods:
    if sum(r["method"] == method for r in rows) != 160:
        raise SystemExit(f"{method} is not complete at 160 images")
out = Path("runs/web40_single_intervention/protection_quality_audit.csv")
with out.open("w", newline="") as h:
    w = csv.DictWriter(h, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
summary = ["# Web40 protection-quality audit", "", "| Method | Images | Max L-inf | Mean PSNR (dB) |", "|---|---:|---:|---:|"]
for method in methods:
    x = [r for r in rows if r["method"] == method]
    summary.append(f"| {method} | {len(x)} | {max(r['linf'] for r in x)}/255 | {np.mean([r['psnr'] for r in x]):.2f} |")
out.with_suffix(".md").write_text("\n".join(summary) + "\n")
print(f"wrote {out}")
