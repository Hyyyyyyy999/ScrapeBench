import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OKABE = {"clean": "#0072B2", "random": "#E69F00", "fsmg": "#009E73", "aspl": "#D55E00",
         "mix20": "#CC79A7", "mix50": "#56B4E9", "purify50": "#000000"}
LS = {"clean": "-", "random": "--", "fsmg": "-", "aspl": "-", "mix20": "--", "mix50": "-.", "purify50": ":"}


def _tier_x(tiers):
    return np.arange(len(tiers))


def _err(sub, m, t):
    r = sub[(sub["method"] == m) & (sub["tier"] == t)]
    if r.empty:
        return np.nan
    return float((r["ci_hi"].iloc[0] - r["ci_lo"].iloc[0]) / 2)


def gap_series(sub, m, tiers, base):
    ys, es = [], []
    for t in tiers:
        rp = sub[(sub["method"] == m) & (sub["tier"] == t)]
        rc = sub[(sub["method"] == "clean") & (sub["tier"] == t)]
        if rp.empty or rc.empty:
            ys.append(np.nan)
            es.append(np.nan)
            continue
        gap = float(rc["mean"].iloc[0] - rp["mean"].iloc[0])
        e = float(np.hypot(_err(sub, "clean", t), _err(sub, m, t)))
        ys.append(gap)
        es.append(e)
    return np.array(ys), np.array(es)


def t0_significant(sub, m, tiers):
    if "t0" not in tiers:
        return False, 0.0
    g, e = gap_series(sub, m, ["t0"], sub)
    return bool(abs(g[0]) > max(0.02, 2 * e[0])), float(g[0])


def plot_gap(sub, tiers, stage, outdir):
    plt.figure(figsize=(7.2, 4.6))
    x = _tier_x(tiers)
    for m in [mm for mm in sub["method"].unique() if mm != "clean"]:
        ys, es = gap_series(sub, m, tiers, sub)
        plt.errorbar(x, ys, yerr=es, marker="o", ms=4, lw=1.8, capsize=2.5,
                     color=OKABE.get(m, None), ls=LS.get(m, "-"), label=m)
    rc = [float(sub[(sub["method"] == "clean") & (sub["tier"] == t)]["mean"].iloc[0]) if not sub[(sub["method"] == "clean") & (sub["tier"] == t)].empty else np.nan for t in tiers]
    plt.plot(x, np.zeros(len(tiers)), lw=0.8, color="gray")
    plt.xticks(x, tiers, rotation=45, ha="right")
    plt.ylabel("Protection gap $\\Delta(T)$ (identity sim.)")
    plt.title(f"Absolute protection gap across the funnel (stage {stage})")
    plt.grid(alpha=0.3, lw=0.5)
    plt.legend(ncol=2, fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, f"gap_stage_{stage}.png"), dpi=200)
    plt.close()


def plot_rr(sub, tiers, stage, outdir):
    sig = {}
    plt.figure(figsize=(7.2, 4.6))
    x = _tier_x(tiers)
    plotted = False
    for m in [mm for mm in sub["method"].unique() if mm != "clean"]:
        ok, g0 = t0_significant(sub, m, tiers)
        if not ok or abs(g0) < 1e-6:
            sig[m] = "n.s."
            continue
        ys, es = gap_series(sub, m, tiers, sub)
        rr = ys / g0
        rre = es / abs(g0)
        plt.errorbar(x, rr, yerr=rre, marker="o", ms=4, lw=1.8, capsize=2.5,
                     color=OKABE.get(m, None), ls=LS.get(m, "-"), label=m)
        sig[m] = "sig"
        plotted = True
    plt.axhline(1.0, color="gray", lw=0.8, ls="--")
    plt.axhline(0.0, color="gray", lw=0.8)
    plt.xticks(x, tiers, rotation=45, ha="right")
    plt.ylabel("Retention ratio RR(T)")
    plt.title(f"Protection retention under the web funnel (stage {stage})")
    plt.ylim(-0.6, 1.6)
    if plotted:
        plt.legend(fontsize=9)
    plt.grid(alpha=0.3, lw=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, f"collapse_stage_{stage}.png"), dpi=200)
    plt.close()
    return sig


def plot_det(df, tiers, stage, outdir):
    plt.figure(figsize=(7.2, 4.2))
    x = _tier_x(tiers)
    for m in df["method"].unique():
        ys = []
        for t in tiers:
            r = df[(df["stage"] == stage) & (df["method"] == m) & (df["tier"] == t)]
            ys.append(float(r["pos_rate"].mean()) if not r.empty else np.nan)
        plt.plot(x, ys, marker="s", ms=4, lw=1.6, color=OKABE.get(m, None),
                 ls=LS.get(m, "-"), label=m)
    plt.xticks(x, tiers, rotation=45, ha="right")
    plt.ylabel("Attack success rate (identity sim. $>\\tau$)")
    plt.title(f"Detection-failure view along the funnel (stage {stage})")
    plt.ylim(-0.02, 1.02)
    plt.grid(alpha=0.3, lw=0.5)
    plt.legend(fontsize=9, ncol=2)
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, f"detfail_stage_{stage}.png"), dpi=200)
    plt.close()
