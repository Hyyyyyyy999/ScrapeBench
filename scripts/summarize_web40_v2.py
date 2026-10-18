#!/usr/bin/env python3
"""Create the final 40-ID Stage-A table directly from sample ledgers."""

import csv
import json
import math
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "runs/web40_single_intervention/generations"
OUT = ROOT / "runs/web40_single_intervention"
ATTACKS = ("instantid", "ipfaceid")
METHODS = ("clean", "gapdiff", "idprotector", "arcp_web_v2")
TIERS = ("t0", "t1_jpeg70", "t2_canvas_dpr1", "t3_agent_facecrop",
         "t4_sr_x2", "t5_i2i30", "t6_sde50")


def read_cell(path):
    values = []
    for line in path.read_text(errors="replace").splitlines():
        row = json.loads(line)
        value = row.get("ism")
        values.append(float(value) if row.get("detected") and value is not None else math.nan)
    a = np.asarray(values, dtype=float)
    detected = np.isfinite(a)
    return {
        "n": len(a),
        "detected": int(detected.sum()),
        "sum": float(np.nansum(a)),
        "e2e": float(np.nansum(a) / len(a)),
        "isr": float(np.mean(np.where(detected, a >= 0.30, False))),
    }


def ci(values, seed):
    a = np.asarray(values, dtype=float)
    if len(a) < 2:
        return math.nan, math.nan
    rng = np.random.default_rng(seed)
    draws = a[rng.integers(0, len(a), (10000, len(a)))].mean(1)
    return tuple(np.quantile(draws, (0.025, 0.975)))


def fmt(value):
    return "--" if not np.isfinite(value) else f"{value:.3f}"


def main():
    cells = {}
    for attack in ATTACKS:
        for method in METHODS:
            for tier in TIERS:
                folder = GEN / attack / method / tier
                if not folder.exists():
                    continue
                for ledger in folder.glob("*/samples.jsonl"):
                    cells[(attack, method, tier, ledger.parent.name)] = read_cell(ledger)

    rows = []
    seed = 20261016
    for attack in ATTACKS:
        for method in METHODS:
            for tier in TIERS:
                selected = [(pid, value) for (a, m, t, pid), value in cells.items()
                            if (a, m, t) == (attack, method, tier)]
                n_samples = sum(v["n"] for _, v in selected)
                n_detected = sum(v["detected"] for _, v in selected)
                sim_sum = sum(v["sum"] for _, v in selected)
                cond = sim_sum / n_detected if n_detected else math.nan
                e2e = sim_sum / n_samples if n_samples else math.nan
                fdfr = 1.0 - n_detected / n_samples if n_samples else math.nan
                isr = (sum(v["isr"] * v["n"] for _, v in selected) / n_samples
                       if n_samples else math.nan)
                gaps, gaps0 = [], []
                if method != "clean":
                    for pid, value in selected:
                        clean = cells.get((attack, "clean", tier, pid))
                        clean0 = cells.get((attack, "clean", "t0", pid))
                        protected0 = cells.get((attack, method, "t0", pid))
                        if clean and clean0 and protected0:
                            gaps.append(clean["e2e"] - value["e2e"])
                            gaps0.append(clean0["e2e"] - protected0["e2e"])
                gap = float(np.mean(gaps)) if gaps else math.nan
                lo, hi = ci(gaps, seed) if gaps else (math.nan, math.nan)
                seed += 1
                denom = float(np.mean(gaps0)) if gaps0 else math.nan
                rr = gap / denom if np.isfinite(denom) and abs(denom) > 1e-12 else math.nan
                rows.append({
                    "attack": attack, "method": method, "tier": tier,
                    "n_ids": len(selected), "n_samples": n_samples,
                    "conditional_ism": cond, "e2e_ism": e2e, "fdfr": fdfr,
                    "isr_at_0.30": isr, "paired_n": len(gaps),
                    "paired_gap": gap, "gap_ci_lo": lo, "gap_ci_hi": hi, "rr": rr,
                })

    OUT.mkdir(parents=True, exist_ok=True)
    csv_path = OUT / "final_v2_summary.csv"
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    md = ["# Web40 final ARCP-Web-v2 summary", "",
          "ISM/ISR lower is better; paired gap and RR higher are better.", ""]
    for attack in ATTACKS:
        md += [f"## {attack}", "",
               "| Method | Tier | IDs | Cond. ISM | E2E ISM | FDFR | ISR@.30 | Gap [95% CI] | RR |",
               "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
        for row in (r for r in rows if r["attack"] == attack):
            gap_ci = "--" if not np.isfinite(row["paired_gap"]) else (
                f"{fmt(row['paired_gap'])} [{fmt(row['gap_ci_lo'])}, {fmt(row['gap_ci_hi'])}]")
            md.append(f"| {row['method']} | {row['tier']} | {row['n_ids']} | "
                      f"{fmt(row['conditional_ism'])} | {fmt(row['e2e_ism'])} | "
                      f"{fmt(row['fdfr'])} | {fmt(row['isr_at_0.30'])} | {gap_ci} | {fmt(row['rr'])} |")
        md.append("")
    (OUT / "final_v2_summary.md").write_text("\n".join(md) + "\n")
    print(f"wrote {csv_path} and {OUT / 'final_v2_summary.md'}")


if __name__ == "__main__":
    main()
