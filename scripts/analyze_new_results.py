#!/usr/bin/env python3
"""Summarize the repaired/extended experiments without mixing attack families."""

import argparse
import csv
import math
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np


TIERS = ("t0", "t1_jpeg85", "t2_canvas_dpr1", "t5_i2i30")
METHODS = ("clean", "fsmg", "fsmgj")
PILOT_IDS = {"celeb00025", "celeb00027", "celeb00028", "celeb00029", "celeb00030", "celeb00031"}
LABELS = {
    "t0": "T0",
    "t1_jpeg85": "J85",
    "t2_canvas_dpr1": "T2",
    "t5_i2i30": "T5",
}
ORIGINAL_INSTANT = {
    ("clean", "t0"): 0.46,
    ("clean", "t1_jpeg85"): 0.46,
    ("clean", "t2_canvas_dpr1"): 0.43,
    ("fsmg", "t0"): 0.36,
    ("fsmg", "t1_jpeg85"): 0.33,
    ("fsmg", "t2_canvas_dpr1"): 0.23,
}
ORIGINAL_STAGE_C = {"mix20": 0.042, "mix50": 0.022, "purify50": 0.078}


def as_float(value):
    try:
        result = float(value)
    except (TypeError, ValueError):
        return math.nan
    return result


def latest_rows(path):
    latest = {}
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            key = (row["stage"], row["pid"], row["method"], row["tier"], row["attack"])
            latest[key] = row
    return latest


def detection_rates(paths):
    # The append-only stage logs contain the detector fraction even though the
    # legacy CSV schema does not.  Log lines carry no attack field, so the
    # rates are keyed by timestamp and joined to result rows on ``ts``; the
    # (stage, pid, method, tier) map is kept only as a last-resort fallback
    # for rows whose timestamp cannot be matched.  Last occurrence wins,
    # matching latest_rows.
    rates = {}
    pattern = re.compile(
        r"^\[(?P<ts>[0-9-]+ [0-9:.]+)\] (?P<stage>A|C) (?:(?P<method>[^/ ]+)/)?(?P<pid>celeb\d+)/(?P<tier>[^ ]+) "
        r"mean=(?:nan|[-+.0-9]+) det=(?P<det>[0-9.]+)"
    )
    for path in paths:
        if not path.exists():
            continue
        for line in path.read_text(errors="replace").splitlines():
            match = pattern.search(line)
            if not match:
                continue
            stage = match.group("stage")
            method = match.group("method") or "fsmg"
            det = float(match.group("det"))
            rates[(match.group("ts"), stage)] = det
            rates[(stage, match.group("pid"), method, match.group("tier"))] = det
    return rates


def det_for(row, rates):
    ts = row.get("ts") or ""
    stage = row["stage"]
    if (ts, stage) in rates:
        return rates[(ts, stage)]
    try:
        stamp = datetime.strptime(ts[:19], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        stamp = None
    if stamp is not None:
        best, best_gap = None, None
        for key, det in rates.items():
            if not (isinstance(key, tuple) and len(key) == 2 and isinstance(key[0], str) and key[1] == stage):
                continue
            try:
                other = datetime.strptime(key[0][:19], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
            gap = abs((other - stamp).total_seconds())
            if gap <= 5.0 and (best_gap is None or gap < best_gap):
                best, best_gap = det, gap
        if best is not None:
            return best
    key = (stage, row["pid"], row["method"], row["tier"])
    return rates.get(key, math.nan)


def bootstrap(values, seed=0, n_boot=10000):
    values = np.asarray([v for v in values if np.isfinite(v)], dtype=float)
    if not len(values):
        return math.nan, math.nan
    rng = np.random.default_rng(seed)
    draws = rng.choice(values, size=(n_boot, len(values)), replace=True).mean(axis=1)
    return tuple(np.quantile(draws, (0.025, 0.975)))


def fmt(value, digits=3):
    return "--" if not np.isfinite(value) else f"{value:.{digits}f}"


def summarize_cells(rows, detections):
    cells = {}
    for key, row in rows.items():
        stage, pid, method, tier, attack = key
        if int(row.get("n_samples") or 0) <= 0:
            continue
        conditional = as_float(row.get("mean_id"))
        det = det_for(row, detections)
        unconditional = conditional * det if np.isfinite(conditional) and np.isfinite(det) else (
            0.0 if np.isfinite(det) and det == 0 else math.nan
        )
        cells[key] = {
            "conditional": conditional,
            "det": det,
            "unconditional": unconditional,
            "success": as_float(row.get("pos_rate")),
            "n": int(row.get("n_samples") or 0),
        }
    return cells


def instant_table(cells):
    out = {}
    for method in METHODS:
        for tier in TIERS:
            selected = [v for (s, pid, m, t, a), v in cells.items()
                        if s == "A" and pid in PILOT_IDS and a == "instantid" and m == method and t == tier]
            cond = [v["conditional"] for v in selected]
            uncond = [v["unconditional"] for v in selected]
            det = [v["det"] for v in selected]
            succ = [v["success"] for v in selected]
            lo, hi = bootstrap(uncond)
            out[(method, tier)] = {
                "n_ids": len(selected),
                "conditional": float(np.nanmean(cond)) if np.isfinite(cond).any() else math.nan,
                "unconditional": float(np.nanmean(uncond)) if np.isfinite(uncond).any() else math.nan,
                "det": float(np.nanmean(det)) if np.isfinite(det).any() else math.nan,
                "success": float(np.nanmean(succ)) if np.isfinite(succ).any() else math.nan,
                "lo": lo,
                "hi": hi,
            }
    return out


def paired_gaps(cells, value_name):
    gaps = defaultdict(list)
    by = {(pid, method, tier): values for (stage, pid, method, tier, attack), values in cells.items()
          if stage == "A" and pid in PILOT_IDS and attack == "instantid"}
    for method in ("fsmg", "fsmgj"):
        for tier in TIERS:
            for pid in sorted({pid for pid, _, _ in by}):
                clean = by.get((pid, "clean", tier), {}).get(value_name, math.nan)
                protected = by.get((pid, method, tier), {}).get(value_name, math.nan)
                if np.isfinite(clean) and np.isfinite(protected):
                    gaps[(method, tier)].append(clean - protected)
    return gaps


def write_report(path, cells, summary):
    lines = ["# New and repaired ScrapeBench experiments", ""]
    instant = [v for k, v in cells.items() if k[0] == "A" and k[1] in PILOT_IDS and k[4] == "instantid" and k[2] in METHODS]
    lines += [f"InstantID generated cells: {len(instant)}/72.", ""]
    lines += ["## InstantID multi-identity aggregate", "",
              "| Method | Tier | IDs | Conditional ID | Detection | Unconditional ID | Success | 95% CI (uncond.) |",
              "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for method in METHODS:
        for tier in TIERS:
            x = summary[(method, tier)]
            lines.append(
                f"| {method} | {LABELS[tier]} | {x['n_ids']} | {fmt(x['conditional'])} | "
                f"{fmt(100*x['det'], 1)}% | {fmt(x['unconditional'])} | {fmt(100*x['success'], 1)}% | "
                f"[{fmt(x['lo'])}, {fmt(x['hi'])}] |"
            )
    for value_name, title in (("conditional", "Conditional-on-detection"),
                              ("unconditional", "Detection-failure-zero")):
        gaps = paired_gaps(cells, value_name)
        lines += ["", f"## {title} paired gaps and retention", "",
                  "| Method | Tier | Paired IDs | clean-protected gap | RR vs T0 |",
                  "|---|---:|---:|---:|---:|"]
        for method in ("fsmg", "fsmgj"):
            denom = np.mean(gaps[(method, "t0")]) if gaps[(method, "t0")] else math.nan
            for tier in TIERS:
                vals = gaps[(method, tier)]
                gap = float(np.mean(vals)) if vals else math.nan
                rr = gap / denom if np.isfinite(gap) and np.isfinite(denom) and abs(denom) > 1e-9 else math.nan
                lines.append(f"| {method} | {LABELS[tier]} | {len(vals)} | {fmt(gap)} | {fmt(rr)} |")
    lines += ["", "## Comparison with the paper's one-identity InstantID probe", "",
              "| Method | Tier | Original | New conditional | Difference |",
              "|---|---:|---:|---:|---:|"]
    for key, original in ORIGINAL_INSTANT.items():
        new = summary[key]["conditional"]
        lines.append(f"| {key[0]} | {LABELS[key[1]]} | {original:.3f} | {fmt(new)} | {fmt(new-original)} |")
    lines += ["", "## Repaired T3", "",
              "| Method | IDs | Conditional ID | Detection | Unconditional ID | Success |",
              "|---|---:|---:|---:|---:|---:|"]
    for method in METHODS:
        selected = [v for (s, pid, m, t, a), v in cells.items()
                    if s == "A" and pid in PILOT_IDS and a == "ipfaceid" and m == method and t == "t3_agent_facecrop"]
        def mean(name):
            vals = [v[name] for v in selected if np.isfinite(v[name])]
            return float(np.mean(vals)) if vals else math.nan
        lines.append(f"| {method} | {len(selected)} | {fmt(mean('conditional'))} | {fmt(100*mean('det'),1)}% | "
                     f"{fmt(mean('unconditional'))} | {fmt(100*mean('success'),1)}% |")
    lines += ["", "## Repaired Stage C", "",
              "| Condition | IDs | Original invalid mean | New conditional | Detection | Unconditional | Success |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    for tier in ("mix20", "mix50", "purify50"):
        selected = [v for (s, pid, _, t, a), v in cells.items() if s == "C" and pid in PILOT_IDS and t == tier]
        def mean(name):
            vals = [v[name] for v in selected if np.isfinite(v[name])]
            return float(np.mean(vals)) if vals else math.nan
        lines.append(f"| {tier} | {len(selected)} | {ORIGINAL_STAGE_C[tier]:.3f} | {fmt(mean('conditional'))} | "
                     f"{fmt(100*mean('det'),1)}% | {fmt(mean('unconditional'))} | {fmt(100*mean('success'),1)}% |")
    path.write_text("\n".join(lines) + "\n")


def write_csv_outputs(run_dir, cells, summary):
    with (run_dir / "new_experiment_cells.csv").open("w", newline="") as handle:
        fields = ["stage", "pid", "method", "tier", "attack", "n_samples",
                  "conditional_id", "detection_rate", "unconditional_id", "success_rate"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for key in sorted(cells):
            stage, pid, method, tier, attack = key
            value = cells[key]
            writer.writerow({
                "stage": stage, "pid": pid, "method": method, "tier": tier, "attack": attack,
                "n_samples": value["n"], "conditional_id": value["conditional"],
                "detection_rate": value["det"], "unconditional_id": value["unconditional"],
                "success_rate": value["success"],
            })
    with (run_dir / "instantid_summary.csv").open("w", newline="") as handle:
        fields = ["method", "tier", "n_ids", "conditional_id", "detection_rate",
                  "unconditional_id", "success_rate", "unconditional_ci_lo", "unconditional_ci_hi"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for method in METHODS:
            for tier in TIERS:
                value = summary[(method, tier)]
                writer.writerow({
                    "method": method, "tier": tier, "n_ids": value["n_ids"],
                    "conditional_id": value["conditional"], "detection_rate": value["det"],
                    "unconditional_id": value["unconditional"], "success_rate": value["success"],
                    "unconditional_ci_lo": value["lo"], "unconditional_ci_hi": value["hi"],
                })


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", default="runs/full")
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    run_dir = Path(args.run_dir)
    rows = latest_rows(run_dir / "results.csv")
    detections = detection_rates((run_dir / "stage_a.log", run_dir / "stage_c.log"))
    cells = summarize_cells(rows, detections)
    instant_count = sum(k[0] == "A" and k[1] in PILOT_IDS and k[4] == "instantid" and k[2] in METHODS for k in cells)
    t3_count = sum(k[0] == "A" and k[1] in PILOT_IDS and k[4] == "ipfaceid" and k[3] == "t3_agent_facecrop" and k[2] in METHODS for k in cells)
    stage_c_count = sum(k[0] == "C" and k[1] in PILOT_IDS and k[2] in METHODS for k in cells)
    if args.require_complete and (instant_count, t3_count, stage_c_count) != (72, 18, 18):
        raise SystemExit(f"incomplete: InstantID={instant_count}/72 T3={t3_count}/18 StageC={stage_c_count}/18")
    summary = instant_table(cells)
    output = run_dir / "new_experiments_report.md"
    write_report(output, cells, summary)
    write_csv_outputs(run_dir, cells, summary)
    print(f"wrote {output}: InstantID={instant_count}/72 T3={t3_count}/18 StageC={stage_c_count}/18")


if __name__ == "__main__":
    main()
