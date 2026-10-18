#!/usr/bin/env python3
"""Gate expensive experiments on a working clean identity attack."""

import argparse
import csv
import math
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--ids", required=True)
    parser.add_argument("--min-mean", type=float, default=0.25)
    parser.add_argument("--min-valid-fraction", type=float, default=0.75)
    args = parser.parse_args()
    wanted = set(args.ids.split(","))
    latest = {}
    with args.results.open(newline="") as handle:
        for row in csv.DictReader(handle):
            if row["stage"] == "A" and row["method"] == "clean" and row["tier"] == "t0" and row["pid"] in wanted:
                latest[(row["pid"], row["attack"])] = row
    failed = []
    generations_root = args.results.parent / "generations"
    for attack in ("instantid", "ipfaceid"):
        rows = [row for (pid, name), row in latest.items() if name == attack]
        complete = [row for row in rows if int(float(row.get("n_samples") or 0)) > 0 and row.get("mean_id")]
        means = [float(row["mean_id"]) for row in complete if math.isfinite(float(row["mean_id"]))]
        detected = total = 0
        for pid in wanted:
            ledger = generations_root / attack / "clean" / "t0" / pid / "samples.jsonl"
            if not ledger.exists():
                continue
            for line in ledger.read_text().splitlines():
                sample = json.loads(line)
                total += 1
                detected += int(bool(sample.get("detected")))
        fraction = detected / total if total else 0.0
        mean = sum(means) / len(means) if means else math.nan
        print(f"{attack}: complete={len(complete)}/{len(wanted)} detected={detected}/{total} "
              f"detection_rate={fraction:.4f} conditional_mean_id={mean:.4f}")
        if len(complete) != len(wanted) or fraction < args.min_valid_fraction or not math.isfinite(mean) or mean < args.min_mean:
            failed.append(attack)
    if failed:
        raise SystemExit(f"clean attack gate failed: {','.join(failed)}")


if __name__ == "__main__":
    main()
