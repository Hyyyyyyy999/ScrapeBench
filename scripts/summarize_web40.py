#!/usr/bin/env python3
"""Auditable Web40 summary from per-sample ledgers.

Missing detections contribute zero to end-to-end ISM/ISR and are also exposed
as FDFR.  All protection gaps and RR confidence intervals are bootstrapped over
paired identities, never over generated images.  A tier is rankable only when
the clean attack itself retains sufficient detection and identity strength.
"""

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np


TIER_ORDER = ("t0", "t1_jpeg70", "t2_canvas_dpr1", "t3_agent_facecrop",
              "t4_sr_x2", "t5_i2i30", "t6_sde30", "t6_sde35", "t6_sde40",
              "t6_sde50")


def read_cell(path: Path):
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    values = np.asarray([
        float(r["ism"]) if r.get("detected") and r.get("ism") is not None else np.nan
        for r in rows
    ], dtype=float)
    finite = np.isfinite(values)
    n = len(values)
    return {
        "rows": rows, "n": n, "detected": int(finite.sum()),
        "conditional": float(np.nanmean(values)) if finite.any() else math.nan,
        "e2e": float(np.nansum(values) / n) if n else math.nan,
        "fdfr": float(1.0 - finite.mean()) if n else math.nan,
        "isr": float(np.mean(np.where(finite, values >= 0.30, False))) if n else math.nan,
    }


def interval(values, seed, fn=np.mean, draws=10000):
    a = np.asarray(values, dtype=float)
    if len(a) < 2 or not np.isfinite(a).all():
        return math.nan, math.nan
    rng = np.random.default_rng(seed)
    sampled = a[rng.integers(0, len(a), (draws, len(a)))]
    stats = np.asarray([fn(row) for row in sampled], dtype=float)
    stats = stats[np.isfinite(stats)]
    return tuple(np.quantile(stats, (0.025, 0.975))) if len(stats) else (math.nan, math.nan)


def ratio(row):
    den = np.mean(row[:, 1])
    return np.mean(row[:, 0]) / den if abs(den) > 1e-12 else math.nan


def fmt(x):
    return "--" if not np.isfinite(x) else f"{x:.3f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="web40_single_intervention")
    ap.add_argument("--min-clean-detection", type=float, default=0.50)
    ap.add_argument("--min-clean-retention", type=float, default=0.50,
                    help="minimum clean E2E-ISM relative to clean T0")
    ap.add_argument("--methods", default=None,
                    help="comma-separated paper rows; old artifact methods are otherwise discovered")
    ap.add_argument("--ids", default=None,
                    help="comma-separated preregistered identities; excludes stale or exploratory cells")
    args = ap.parse_args()
    root = Path("runs") / args.run
    gen = root / "generations"
    cells = {}
    allowed_ids = set(args.ids.split(",")) if args.ids else None
    for ledger in gen.glob("*/*/*/*/samples.jsonl"):
        attack, method, tier, pid = ledger.parts[-5:-1]
        if allowed_ids is not None and pid not in allowed_ids:
            continue
        cells[(attack, method, tier, pid)] = read_cell(ledger)
    attacks = sorted({k[0] for k in cells})
    methods = (args.methods.split(",") if args.methods else sorted({k[1] for k in cells}))
    tiers = [t for t in TIER_ORDER if any(k[2] == t for k in cells)]
    seed = 20261017
    out_rows = []
    scenario_rows = []

    for attack in attacks:
        clean0 = [v["e2e"] for (a, m, t, _), v in cells.items()
                  if (a, m, t) == (attack, "clean", "t0")]
        clean0_mean = float(np.mean(clean0)) if clean0 else math.nan
        viability = {}
        for tier in tiers:
            cs = [v for (a, m, t, _), v in cells.items()
                  if (a, m, t) == (attack, "clean", tier)]
            clean_det = (sum(v["detected"] for v in cs) / sum(v["n"] for v in cs)) if cs else math.nan
            clean_e2e = float(np.mean([v["e2e"] for v in cs])) if cs else math.nan
            retention = clean_e2e / clean0_mean if np.isfinite(clean0_mean) and clean0_mean > 0 else math.nan
            viability[tier] = (clean_det >= args.min_clean_detection and
                               retention >= args.min_clean_retention)

        for method in methods:
            for tier in tiers:
                selected = {pid: v for (a, m, t, pid), v in cells.items()
                            if (a, m, t) == (attack, method, tier)}
                if not selected:
                    continue
                n = sum(v["n"] for v in selected.values())
                detected = sum(v["detected"] for v in selected.values())
                cond = (sum(v["conditional"] * v["detected"] for v in selected.values()
                            if np.isfinite(v["conditional"])) / detected) if detected else math.nan
                e2e = sum(v["e2e"] * v["n"] for v in selected.values()) / n
                fdfr = 1.0 - detected / n
                isr = sum(v["isr"] * v["n"] for v in selected.values()) / n
                paired = []
                if method != "clean":
                    for pid, value in selected.items():
                        ct = cells.get((attack, "clean", tier, pid))
                        c0 = cells.get((attack, "clean", "t0", pid))
                        p0 = cells.get((attack, method, "t0", pid))
                        if ct and c0 and p0:
                            paired.append((ct["e2e"] - value["e2e"], c0["e2e"] - p0["e2e"]))
                pair = np.asarray(paired, dtype=float)
                gap = float(pair[:, 0].mean()) if len(pair) else math.nan
                gap0 = float(pair[:, 1].mean()) if len(pair) else math.nan
                gap_lo, gap_hi = interval(pair[:, 0], seed) if len(pair) else (math.nan, math.nan)
                rr = gap / gap0 if np.isfinite(gap0) and abs(gap0) > 1e-12 else math.nan
                rr_lo, rr_hi = interval(pair, seed + 1, ratio) if len(pair) else (math.nan, math.nan)
                delta = gap - gap0 if len(pair) else math.nan
                delta_lo, delta_hi = interval(pair[:, 0] - pair[:, 1], seed + 2) if len(pair) else (math.nan, math.nan)
                seed += 3
                out_rows.append({
                    "attack": attack, "method": method, "tier": tier,
                    "rankable": viability[tier], "n_ids": len(selected), "n_samples": n,
                    "conditional_ism": cond, "e2e_ism": e2e, "fdfr": fdfr,
                    "isr_at_0.30": isr, "paired_n": len(pair), "paired_gap": gap,
                    "gap_ci_lo": gap_lo, "gap_ci_hi": gap_hi, "rr": rr,
                    "rr_ci_lo": rr_lo, "rr_ci_hi": rr_hi,
                    "gap_change_from_t0": delta,
                    "gap_change_ci_lo": delta_lo, "gap_change_ci_hi": delta_hi,
                })
                prompt_ids = sorted({int(r.get("prompt_id", 0))
                                     for v in selected.values() for r in v["rows"]})
                for prompt_id in prompt_ids:
                    rows = [r for v in selected.values() for r in v["rows"]
                            if int(r.get("prompt_id", 0)) == prompt_id]
                    vals = np.asarray([float(r["ism"]) if r.get("detected") and r.get("ism") is not None
                                       else np.nan for r in rows])
                    scenario_rows.append({
                        "attack": attack, "method": method, "tier": tier,
                        "prompt_id": prompt_id,
                        "prompt": rows[0].get("prompt", "") if rows else "",
                        "n": len(vals), "conditional_ism": float(np.nanmean(vals)) if np.isfinite(vals).any() else math.nan,
                        "e2e_ism": float(np.nansum(vals) / len(vals)) if len(vals) else math.nan,
                        "fdfr": float(1 - np.isfinite(vals).mean()) if len(vals) else math.nan,
                    })

    root.mkdir(parents=True, exist_ok=True)
    if not out_rows:
        raise SystemExit(f"no complete sample ledgers found under {gen}")
    with (root / "web40_full_summary.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=out_rows[0].keys())
        writer.writeheader(); writer.writerows(out_rows)
    with (root / "web40_by_scenario.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=scenario_rows[0].keys())
        writer.writeheader(); writer.writerows(scenario_rows)
    md = ["# Web40 paired summary", "",
          "Lower ISM/ISR is better. Higher paired gap/RR is better. `no` in Valid means the clean attack itself failed the preregistered viability gate, so methods must not be ranked in that column.", ""]
    for attack in attacks:
        md += [f"## {attack}", "", "| Defense | T | Valid | IDs | E2E ISM | FDFR | ISR | Gap [95% CI] | RR [95% CI] | ΔGap vs T0 |",
               "|---|---|---|---:|---:|---:|---:|---:|---:|---:|"]
        for r in (x for x in out_rows if x["attack"] == attack):
            gap = f"{fmt(r['paired_gap'])} [{fmt(r['gap_ci_lo'])},{fmt(r['gap_ci_hi'])}]"
            rr = f"{fmt(r['rr'])} [{fmt(r['rr_ci_lo'])},{fmt(r['rr_ci_hi'])}]"
            md.append(f"| {r['method']} | {r['tier']} | {'yes' if r['rankable'] else 'no'} | {r['n_ids']} | {fmt(r['e2e_ism'])} | {fmt(r['fdfr'])} | {fmt(r['isr_at_0.30'])} | {gap} | {rr} | {fmt(r['gap_change_from_t0'])} |")
        md.append("")
    (root / "web40_full_summary.md").write_text("\n".join(md) + "\n")
    print(f"wrote {len(out_rows)} aggregate and {len(scenario_rows)} scenario rows under {root}")


if __name__ == "__main__":
    main()
