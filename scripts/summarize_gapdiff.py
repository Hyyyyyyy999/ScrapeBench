#!/usr/bin/env python3
"""Build a GAP-Diff Table-I-shaped CSV from saved DreamBooth generations."""
import argparse
import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image

from scrapebench.metrics.gapdiff import brisque, ser_fiq


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    args = ap.parse_args()
    root = Path("runs") / args.run / "generations" / "dreambooth"
    rows = []
    for manifest in sorted(root.glob("*/*/*/samples.jsonl")):
        method, tier, pid = manifest.parts[-4:-1]
        samples = [json.loads(line) for line in manifest.read_text().splitlines()]
        for prompt_id in sorted({row["prompt_id"] for row in samples}):
            group = [row for row in samples if row["prompt_id"] == prompt_id]
            detected = np.asarray([row["detected"] for row in group], dtype=bool)
            ism = np.asarray([np.nan if row["ism"] is None else row["ism"] for row in group])
            images = [Image.open(manifest.parent / row["file"]).convert("RGB") for row in group]
            try:
                bq = brisque(images)
            except RuntimeError:
                bq = float("nan")
            try:
                sfq = ser_fiq(images)
            except RuntimeError:
                sfq = float("nan")
            rows.append({
                "method": method, "tier": tier, "pid": pid,
                "prompt_id": prompt_id, "prompt": group[0]["prompt"],
                "n": len(group), "FDFR": 1.0 - float(detected.mean()),
                "ISM": float(np.nanmean(ism)) if detected.any() else float("nan"),
                "BRISQUE": bq, "SER-FIQ": sfq,
            })
    out = Path("runs") / args.run / "gapdiff_table_per_identity.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = ["method", "tier", "pid", "prompt_id", "prompt", "n", "FDFR", "ISM", "BRISQUE", "SER-FIQ"]
    with out.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {out} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
