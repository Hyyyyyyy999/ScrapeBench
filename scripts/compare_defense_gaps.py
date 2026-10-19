#!/usr/bin/env python3
"""Direct paired ARCP comparisons with identity bootstrap and Holm correction."""
import argparse
import csv
import json
from pathlib import Path

import numpy as np


def e2e(path):
    rows = [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
    vals = [float(r["ism"]) if r.get("detected") and r.get("ism") is not None else 0.0 for r in rows]
    return float(np.mean(vals))


def ci(values, rng, draws=10000):
    a = np.asarray(values, dtype=float)
    samples = a[rng.integers(0, len(a), (draws, len(a)))].mean(1)
    return np.quantile(samples, (0.025, 0.975))


def holm(p):
    order = np.argsort(p)
    out = np.ones(len(p)); running = 0.0; n = len(p)
    for rank, idx in enumerate(order):
        running = max(running, min(1.0, (n - rank) * p[idx]))
        out[idx] = running
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="web40_single_intervention")
    ap.add_argument("--target", default="arcp_web_v4")
    ap.add_argument("--comparators", default="gapdiff,idprotector,gapdiff_8,idprotector_8,arcp_web_v4_uniform,arcp_web_v4_no_texture,arcp_web_v4_no_coarse,arcp_web_v4_no_detail,arcp_web_v4_no_identity,arcp_web_v4_no_denoise")
    args = ap.parse_args()
    gen = Path("runs") / args.run / "generations"
    cells = {}
    for p in gen.glob("*/*/*/*/samples.jsonl"):
        attack, method, tier, pid = p.parts[-5:-1]
        cells[(attack, method, tier, pid)] = e2e(p)
    rows = []; rng = np.random.default_rng(20261018)
    attacks = sorted({x[0] for x in cells})
    tiers = ["t0", "t1_jpeg70", "t2_canvas_dpr1", "t3_agent_facecrop", "t4_sr_x2", "t5_i2i30", "t6_sde35"]
    for attack in attacks:
        for tier in tiers:
            for comparator in args.comparators.split(","):
                ids = sorted({pid for a, m, t, pid in cells if (a, m, t) == (attack, args.target, tier)} &
                             {pid for a, m, t, pid in cells if (a, m, t) == (attack, comparator, tier)})
                if not ids:
                    continue
                # Positive means ARCP has lower (better) end-to-end ISM.
                d = np.asarray([cells[(attack, comparator, tier, pid)] -
                                cells[(attack, args.target, tier, pid)] for pid in ids])
                lo, hi = ci(d, rng)
                try:
                    from scipy.stats import wilcoxon
                    p = float(wilcoxon(d, alternative="two-sided").pvalue) if np.any(d) else 1.0
                except Exception:
                    p = float("nan")
                rows.append({"attack": attack, "tier": tier, "target": args.target,
                             "comparator": comparator, "n_ids": len(ids),
                             "mean_e2e_advantage": float(d.mean()), "ci_lo": float(lo),
                             "ci_hi": float(hi), "wilcoxon_p": p})
    finite = [i for i, r in enumerate(rows) if np.isfinite(r["wilcoxon_p"])]
    adjusted = holm([rows[i]["wilcoxon_p"] for i in finite]) if finite else []
    for i, q in zip(finite, adjusted): rows[i]["holm_p"] = float(q)
    for r in rows: r.setdefault("holm_p", float("nan"))
    out = Path("runs") / args.run / "direct_gap_comparisons.csv"
    with out.open("w", newline="") as h:
        w = csv.DictWriter(h, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    md = ["# Direct paired ARCP-Web-v4 comparisons", "",
          "Positive advantage means lower end-to-end ISM for ARCP-Web-v4. Resampling unit is identity.", "",
          "| Reader | Layer | Comparator | IDs | Advantage [95% CI] | Holm p |", "|---|---|---|---:|---:|---:|"]
    for r in rows:
        md.append(f"| {r['attack']} | {r['tier']} | {r['comparator']} | {r['n_ids']} | {r['mean_e2e_advantage']:.3f} [{r['ci_lo']:.3f}, {r['ci_hi']:.3f}] | {r['holm_p']:.4g} |")
    out.with_suffix(".md").write_text("\n".join(md) + "\n")
    print(f"wrote {len(rows)} comparisons to {out}")


if __name__ == "__main__":
    main()
