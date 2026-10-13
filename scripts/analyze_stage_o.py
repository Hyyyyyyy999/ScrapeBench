#!/usr/bin/env python3
"""Validate and summarize the completed same-identity Stage-O grid."""

import argparse
import csv
import math
import re
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon


IDS = ("celeb00025", "celeb00027", "celeb00028", "celeb00029", "celeb00030", "celeb00031")
METHODS = ("clean", "random", "fsmg")
ORDERS = ("canonical", "jpeg_only", "sr_first", "t5_first", "t5_only", "deep_chain")


def latest_successful(path):
    rows = {}
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            key = (row["stage"], row["pid"], row["method"], row["tier"], row["attack"])
            if int(row.get("n_samples") or 0) > 0:
                rows[key] = row
    return rows


def detections(*paths):
    out = {}
    pat = re.compile(
        r"\] (?P<stage>A|O) (?P<method>[^/ ]+)/(?P<pid>celeb\d+)/(?P<tier>[^ ]+) "
        r"mean=(?:nan|[-+.0-9]+) det=(?P<det>[0-9.]+)"
    )
    for path in paths:
        if not path.exists():
            continue
        for line in path.read_text(errors="replace").splitlines():
            match = pat.search(line)
            if match:
                out[(match["stage"], match["pid"], match["method"], match["tier"])] = float(match["det"])
    return out


def metric(row, det):
    cond = float(row["mean_id"])
    return {
        "conditional": cond,
        "detection": det,
        "unconditional": cond * det if np.isfinite(cond) else (0.0 if det == 0 else math.nan),
        "success": float(row["pos_rate"]),
    }


def fmt(value, digits=3):
    return "--" if not np.isfinite(value) else f"{value:.{digits}f}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", default="runs/full")
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    run = Path(args.run_dir)
    rows = latest_successful(run / "results.csv")
    det = detections(run / "stage_a.log", run / "stage_order.log")

    cells = {}
    missing = []
    for pid in IDS:
        for method in METHODS:
            base_key = ("A", pid, method, "t0", "ipfaceid")
            if base_key not in rows or ("A", pid, method, "t0") not in det:
                missing.append(base_key)
            else:
                cells[base_key] = metric(rows[base_key], det[("A", pid, method, "t0")])
            for order in ORDERS:
                key = ("O", pid, method, order, "ipfaceid")
                if key not in rows or ("O", pid, method, order) not in det:
                    missing.append(key)
                else:
                    cells[key] = metric(rows[key], det[("O", pid, method, order)])
    if args.require_complete and missing:
        raise SystemExit(f"incomplete Stage O inputs: {len(missing)} missing; first={missing[:3]}")

    base_gap = {}
    for method in ("fsmg", "random"):
        vals = []
        for pid in IDS:
            c = cells.get(("A", pid, "clean", "t0", "ipfaceid"), {}).get("unconditional", math.nan)
            p = cells.get(("A", pid, method, "t0", "ipfaceid"), {}).get("unconditional", math.nan)
            if np.isfinite(c) and np.isfinite(p):
                vals.append(c - p)
        base_gap[method] = float(np.mean(vals)) if vals else math.nan

    summaries = []
    for order in ORDERS:
        by_method = {}
        for method in METHODS:
            values = [cells[("O", pid, method, order, "ipfaceid")] for pid in IDS
                      if ("O", pid, method, order, "ipfaceid") in cells]
            by_method[method] = {name: float(np.mean([v[name] for v in values]))
                                 for name in ("conditional", "detection", "unconditional", "success")}
            by_method[method]["n"] = len(values)
        entry = {"order": order, "methods": by_method}
        clean = {pid: cells[("O", pid, "clean", order, "ipfaceid")]["unconditional"] for pid in IDS
                 if ("O", pid, "clean", order, "ipfaceid") in cells}
        for method in ("fsmg", "random"):
            gaps = np.array([clean[pid] - cells[("O", pid, method, order, "ipfaceid")]["unconditional"]
                             for pid in IDS if pid in clean and ("O", pid, method, order, "ipfaceid") in cells])
            try:
                pvalue = float(wilcoxon(gaps).pvalue)
            except ValueError:
                pvalue = math.nan
            gap = float(np.mean(gaps)) if len(gaps) else math.nan
            entry[method] = {
                "gap": gap,
                "rr": gap / base_gap[method] if np.isfinite(base_gap[method]) and abs(base_gap[method]) > 1e-9 else math.nan,
                "p": pvalue,
            }
        summaries.append(entry)

    with (run / "stage_o_complete_summary.csv").open("w", newline="") as handle:
        fields = ["order", "method", "n_ids", "conditional_id", "detection_rate", "unconditional_id",
                  "success_rate", "paired_gap", "rr_vs_t0", "wilcoxon_p"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for entry in summaries:
            for method in METHODS:
                m = entry["methods"][method]
                effect = entry.get(method, {})
                writer.writerow({"order": entry["order"], "method": method, "n_ids": m["n"],
                                 "conditional_id": m["conditional"], "detection_rate": m["detection"],
                                 "unconditional_id": m["unconditional"], "success_rate": m["success"],
                                 "paired_gap": effect.get("gap", ""), "rr_vs_t0": effect.get("rr", ""),
                                 "wilcoxon_p": effect.get("p", "")})

    lines = ["# Completed Stage O", "", f"Validated cells: {len(cells)}/126 (18 matched T0 + 108 Stage O).", "",
             f"Matched T0 unconditional gaps: FSMG={fmt(base_gap['fsmg'])}, random={fmt(base_gap['random'])}.", "",
             "| Program | Clean uID / det | FSMG uID / det | FSMG gap | FSMG RR | Random gap | Random RR |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for entry in summaries:
        c, f = entry["methods"]["clean"], entry["methods"]["fsmg"]
        lines.append(f"| {entry['order']} | {fmt(c['unconditional'])} / {100*c['detection']:.1f}% | "
                     f"{fmt(f['unconditional'])} / {100*f['detection']:.1f}% | {fmt(entry['fsmg']['gap'])} | "
                     f"{fmt(entry['fsmg']['rr'])} | {fmt(entry['random']['gap'])} | {fmt(entry['random']['rr'])} |")
    (run / "stage_o_complete_report.md").write_text("\n".join(lines) + "\n")
    print(f"validated Stage O: cells={len(cells)}/126 missing={len(missing)}")


if __name__ == "__main__":
    main()
