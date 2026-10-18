#!/usr/bin/env python3
"""Fail closed when gallery/reference folders do not contain the same identity."""

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scrapebench.metrics.id_sim import IdScorer


def images(path: Path) -> list[Path]:
    return sorted(p for p in path.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--min-identity-mean", type=float, default=0.30)
    # GAP-Diff's released five-identity VGGFace2 subset contains profile/occluded
    # inputs; the official-style clean InstantID run detects 70% of them.  Keep
    # this as an explicit floor and report failures separately, rather than
    # silently filtering the hard inputs.
    parser.add_argument("--min-detection-rate", type=float, default=0.70)
    parser.add_argument("--require-every-identity", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    scorer = IdScorer(use_gpu=False)
    records = []
    for gallery_dir in sorted((args.data_root / "raw").iterdir()):
        if not gallery_dir.is_dir():
            continue
        ref_dir = args.data_root / "refs" / gallery_dir.name
        refs = scorer.ref_embeddings(gallery_dir.name, images(ref_dir)) if ref_dir.is_dir() else []
        scores = []
        attempted = 0
        for path in images(gallery_dir):
            attempted += 1
            score, detected = scorer.best_sim(Image.open(path).convert("RGB"), refs)
            if detected and math.isfinite(score):
                scores.append(score)
        records.append({
            "identity": gallery_dir.name,
            "attempted": attempted,
            "detected": len(scores),
            "detection_rate": len(scores) / attempted if attempted else 0.0,
            "mean_similarity": float(np.mean(scores)) if scores else None,
        })

    finite = [r["mean_similarity"] for r in records if r["mean_similarity"] is not None]
    attempted = sum(r["attempted"] for r in records)
    detected = sum(r["detected"] for r in records)
    report = {
        "data_root": str(args.data_root),
        "identities": len(records),
        "detection_rate": detected / attempted if attempted else 0.0,
        "mean_identity_similarity": float(np.mean(finite)) if finite else None,
        "thresholds": {
            "min_identity_mean": args.min_identity_mean,
            "min_detection_rate": args.min_detection_rate,
        },
        "records": records,
    }
    output = args.output or args.data_root / "identity_validation.json"
    output.write_text(json.dumps(report, indent=2) + "\n")
    mean = report["mean_identity_similarity"]
    per_identity_passed = all(
        r["mean_similarity"] is not None
        and r["mean_similarity"] >= args.min_identity_mean
        and r["detection_rate"] >= args.min_detection_rate
        for r in records
    )
    passed = (
        mean is not None
        and mean >= args.min_identity_mean
        and report["detection_rate"] >= args.min_detection_rate
        and (per_identity_passed or not args.require_every_identity)
    )
    print(json.dumps({**report, "passed": passed}, indent=2))
    if not passed:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
