#!/usr/bin/env python3
"""Paired effect-size report with bootstrap CIs, RR and TOST."""
import argparse
import csv
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


def ci(values, rng, n_boot=10000):
    values = np.asarray(values, dtype=float)
    draws = values[rng.integers(0, len(values), (n_boot, len(values)))].mean(1)
    return np.quantile(draws, [0.025, 0.975])


def tost(values, bound):
    values = np.asarray(values, dtype=float)
    n, mean, sem = len(values), values.mean(), stats.sem(values)
    if n < 2 or sem == 0:
        return float("nan")
    p_lower = 1 - stats.t.cdf((mean + bound) / sem, n - 1)
    p_upper = stats.t.cdf((mean - bound) / sem, n - 1)
    return max(float(p_lower), float(p_upper))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--protected", default="arcp_v2")
    ap.add_argument("--sesoi", type=float, default=0.03)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    df = pd.read_csv(args.results)
    df = df[pd.to_numeric(df.n_samples, errors="coerce").fillna(0) > 0]
    df = df.sort_values("ts").drop_duplicates(
        ["stage", "pid", "method", "tier", "attack"], keep="last")
    clean = df[df.method == "clean"]
    prot = df[df.method == args.protected]
    merged = clean.merge(prot, on=["stage", "pid", "tier", "attack"], suffixes=("_clean", "_protected"))
    merged["gap"] = merged.mean_id_clean - merged.mean_id_protected
    rng = np.random.default_rng(20261015)
    rows = []
    for (stage, attack, tier), group in merged.groupby(["stage", "attack", "tier"]):
        gaps = group.gap.to_numpy(float)
        lo, hi = ci(gaps, rng)
        t0 = merged[(merged.stage == stage) & (merged.attack == attack) & (merged.tier == "t0")][["pid", "gap"]]
        paired = group[["pid", "gap"]].merge(t0, on="pid", suffixes=("", "_t0"))
        rr = np.nan
        dlo = dhi = np.nan
        change = np.nan
        if len(paired) and abs(paired.gap_t0.mean()) > 1e-12:
            rr = gaps.mean() / paired.gap_t0.mean()
            idx = rng.integers(0, len(paired), (10000, len(paired)))
            rr_draw = paired.gap.to_numpy()[idx].mean(1) / paired.gap_t0.to_numpy()[idx].mean(1)
            dlo, dhi = np.nanquantile(rr_draw, [0.025, 0.975])
            change = float((paired.gap - paired.gap_t0).mean())
        rows.append(dict(stage=stage, attack=attack, tier=tier, n_id=len(gaps),
                         gap=gaps.mean(), gap_ci_lo=lo, gap_ci_hi=hi, rr=rr,
                         rr_ci_lo=dlo, rr_ci_hi=dhi, change_from_t0=change,
                         tost_p=tost(gaps, args.sesoi), sesoi=args.sesoi))
    out = Path(args.out or Path(args.results).with_name(f"paired_{args.protected}.csv"))
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"wrote {out} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
