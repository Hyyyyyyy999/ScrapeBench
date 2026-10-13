import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OKABE = {"clean": "#0072B2", "random": "#E69F00", "fsmg": "#009E73", "aspl": "#D55E00",
         "mix20": "#CC79A7", "mix50": "#56B4E9", "purify50": "#000000"}
LS = {"clean": "-", "random": "--", "fsmg": "-", "aspl": "-", "mix20": "--", "mix50": "-.", "purify50": ":"}
TIER_LABEL = {"t0": "T0", "t1_jpeg95": "JPEG-95", "t1_jpeg85": "JPEG-85", "t1_jpeg75": "JPEG-75",
              "t1_jpeg65": "JPEG-65", "t1_webp80": "WebP-80", "t2_canvas_dpr1": "T2 DPR-1",
              "t3_agent_facecrop": "T3 crop", "t4_sr_x2": "T4 SR$\\times$2", "t5_i2i30": "T5 i2i-0.3",
              "mix20": "mix-20%", "mix50": "mix-50%", "purify50": "purify-50%"}
plt.rcParams.update({"font.size": 11, "axes.titlesize": 11.5})


def per_id_matrix(df, stage, tiers):
    out = {}
    for (m, t), g in df[(df["stage"] == stage)].groupby(["method", "tier"]):
        out[(m, t)] = g.groupby("pid")["mean_id"].mean().sort_index()
    return out


def gap_boot(sub, m, t, M, n_boot=500, seed=0):
    rng = np.random.default_rng(seed)
    rc = M.get(("clean", t))
    rm = M.get((m, t))
    if rc is None or rm is None:
        return np.nan, np.nan
    rcv, rmv = rc.values, rm.values
    gaps = []
    for _ in range(n_boot):
        a = rng.choice(rcv, len(rcv), replace=True)
        b = rng.choice(rmv, len(rmv), replace=True)
        gaps.append(a.mean() - b.mean())
    gaps = np.array(gaps)
    return float(np.mean([rcv.mean() - rmv.mean()])), float(np.std(gaps))


def rr_curve(df, stage, m, tiers, seed=0):
    M = per_id_matrix(df, stage, tiers)
    d0, e0 = gap_boot(df, m, "t0", M, seed=seed)
    if not np.isfinite(d0) or abs(d0) < 1e-6:
        return None
    xs, ys, es = [], [], []
    for t in tiers:
        d, e = gap_boot(df, m, t, M, seed=seed + 1)
        if not np.isfinite(d):
            continue
        xs.append(t)
        rr = d / d0
        err = np.hypot(e, abs(rr) * e0) / abs(d0)
        ys.append(rr)
        es.append(err)
    return xs, np.array(ys), np.array(es), d0


def t0_sig(df, stage, m, seed=0):
    M = per_id_matrix(df, stage, ["t0"])
    d0, e0 = gap_boot(df, m, "t0", M, seed=seed)
    return bool(np.isfinite(d0) and abs(d0) > max(0.035, 2.5 * e0)), d0


def plot_gap(df, tiers, stage, outdir):
    fig, ax = plt.subplots(figsize=(4.8, 3.4))
    M = per_id_matrix(df, stage, tiers)
    x = np.arange(len(tiers))
    for m in [mm for mm in df[df["stage"] == stage]["method"].unique() if mm != "clean"]:
        ok, _ = t0_sig(df, stage, m)
        if not ok:
            continue
        ys, es = [], []
        for t in tiers:
            d, e = gap_boot(df, m, t, M)
            ys.append(d)
            es.append(e)
        ax.errorbar(x, ys, yerr=es, marker="o", ms=3.5, lw=1.6, capsize=2,
                    color=OKABE.get(m), ls=LS.get(m, "-"), label=m)
    ax.axhline(0.0, color="gray", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([TIER_LABEL.get(t, t) for t in tiers], rotation=40, ha="right")
    ax.set_ylabel("Protection gap $\\Delta(T)$")
    ax.set_title(f"Absolute gap across the funnel (stage {stage})")
    ax.grid(alpha=0.3, lw=0.5)
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, f"gap_stage_{stage}.png"), dpi=220)
    plt.close(fig)


def plot_rr(df, tiers, stage, outdir):
    fig, ax = plt.subplots(figsize=(9.6, 3.4))
    x = np.arange(len(tiers))
    sig = {}
    for m in [mm for mm in df[df["stage"] == stage]["method"].unique() if mm != "clean"]:
        ok, _ = t0_sig(df, stage, m)
        if not ok:
            sig[m] = "n.s."
            continue
        r = rr_curve(df, stage, m, tiers)
        if r is None:
            sig[m] = "n.s."
            continue
        xs, ys, es, _ = r
        idx = [tiers.index(t) for t in xs]
        lo_e = np.clip(np.minimum(es, np.array(ys) + 0.12), 0.0, None)
        hi_e = np.clip(np.minimum(es, 1.15 - np.array(ys) + 0.02), 0.0, None)
        filled = np.array([abs(y) > 2 * e for y, e in zip(ys, es)])
        col = OKABE.get(m)
        for fi in (True, False):
            sel = np.array([bool(f) == fi for f in filled])
            if not any(sel):
                continue
            ax.errorbar(np.array(idx)[sel], np.array(ys)[sel],
                        yerr=[np.array(lo_e)[sel], np.array(hi_e)[sel]], marker="o",
                        ms=4.5, lw=1.9, capsize=2.5, color=col, ls=LS.get(m, "-"),
                        fillstyle="full" if fi else "none", label=m if fi else None)
        sig[m] = "sig"
    ax.axhline(1.0, color="gray", lw=0.9, ls="--")
    ax.axhline(0.0, color="gray", lw=0.9)
    ax.set_xticks(x)
    ax.set_xticklabels([TIER_LABEL.get(t, t) for t in tiers], rotation=35, ha="right")
    ax.set_ylabel("Retention ratio RR$(T)$")
    ax.set_title(f"Protection retention under the web acquisition funnel (stage {stage})")
    ax.set_ylim(-0.15, 1.25)
    ax.grid(alpha=0.3, lw=0.5)
    if any(v == "sig" for v in sig.values()):
        ax.legend(fontsize=10, ncol=3, loc="upper right")
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, f"collapse_stage_{stage}.png"), dpi=220)
    plt.close(fig)
    return sig


def plot_det(df, tiers, stage, outdir):
    fig, ax = plt.subplots(figsize=(4.8, 3.4))
    x = np.arange(len(tiers))
    for m in df[df["stage"] == stage]["method"].unique():
        ys = []
        for t in tiers:
            r = df[(df["stage"] == stage) & (df["method"] == m) & (df["tier"] == t)]
            ys.append(float(r["pos_rate"].mean()) if not r.empty else np.nan)
        ax.plot(x, ys, marker="s", ms=3.5, lw=1.5, color=OKABE.get(m), ls=LS.get(m, "-"), label=m)
    ax.set_xticks(x)
    ax.set_xticklabels([TIER_LABEL.get(t, t) for t in tiers], rotation=40, ha="right")
    ax.set_ylabel("Attack success rate (sim.$>\\tau$)")
    ax.set_title(f"Binary success view along the funnel (stage {stage})")
    ax.set_ylim(-0.02, 1.02)
    ax.grid(alpha=0.3, lw=0.5)
    ax.legend(fontsize=8.5, ncol=2)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, f"detfail_stage_{stage}.png"), dpi=220)
    plt.close(fig)


def plot_family(df, outdir):
    fig, ax = plt.subplots(figsize=(4.8, 3.4))
    tiers_a = ["t0", "t1_jpeg85", "t2_canvas_dpr1"]
    tiers_b = ["t0", "t1_jpeg85", "t2_canvas_dpr1"]
    labels = ["T0", "JPEG-85", "T2"]
    w = 0.36
    for k, (stage, tiers, off, col) in enumerate([("A", tiers_a, -w / 2, "#009E73"),
                                                  ("B", tiers_b, w / 2, "#0072B2")]):
        vals = []
        for t in tiers:
            r = rr_curve(df, stage, "fsmg", [tt for tt in ["t0", t] if tt] , seed=3)
            vals.append(r[1][-1] if r else np.nan)
        ax.bar(np.arange(len(tiers)) + off, vals, width=w, color=col, alpha=0.9,
               label=f"Stage {'A (zero-shot)' if stage == 'A' else 'B (DreamBooth)'}")
    ax.axhline(1.0, color="gray", lw=0.8, ls="--")
    ax.set_xticks(np.arange(len(tiers_a)))
    ax.set_xticklabels(labels)
    ax.set_ylabel("FSMG retention RR$(T)$")
    ax.set_title("The same defense under two attack families")
    ax.set_ylim(0, 1.2)
    ax.grid(alpha=0.3, axis="y", lw=0.5)
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "family_contrast.png"), dpi=220)
    plt.close(fig)


def plot_auc(df, tiers, stage, outdir):
    tiers_all = [t for t in tiers if t != "t0"]
    prot = [m for m in ["random", "fsmg", "aspl"] if not df[(df["stage"] == stage) & (df["method"] == m)].empty]
    fig, ax = plt.subplots(figsize=(4.8, 3.2))
    for k, m in enumerate(prot):
        cells = df[(df["stage"] == stage) & (df["method"] == m)]
        clean = df[(df["stage"] == stage) & (df["method"] == "clean")]
        rng = np.random.default_rng(k)
        boots = []
        for _ in range(1000):
            s = int(rng.integers(1000000000))
            pc = cells.sample(frac=1.0, replace=True, random_state=s).groupby("tier")["mean_id"].mean()
            cc = clean.sample(frac=1.0, replace=True, random_state=s + 1).groupby("tier")["mean_id"].mean()
            if "t0" not in pc.index or "t0" not in cc.index or not all(t in pc.index and t in cc.index for t in tiers_all):
                continue
            denom = float(cc["t0"]) - float(pc["t0"])
            if abs(denom) < 1e-6:
                continue
            rr = [float((cc[t0] - pc[t0]) / denom) for t0 in tiers_all]
            boots.append((getattr(np, "trapz", None) or np.trapezoid)(rr) / (len(rr) - 1))
        boots = np.array(boots)
        if boots.size == 0:
            # Sparse/pilot stages can have no bootstrap resample containing
            # every requested tier.  Skip the bar instead of aborting the
            # entire report after all experiment cells have completed.
            continue
        mu = float(np.mean(boots))
        lo, hi = np.percentile(boots, [2.5, 97.5])
        ax.bar(k, mu, width=0.55, color=OKABE.get(m), alpha=0.9, label=m)
        ax.errorbar(k, mu, yerr=[[max(0, mu - lo)], [max(0, hi - mu)]], fmt="none", ecolor="0.25", capsize=3, lw=1)
    ax.axhline(1.0, color="gray", lw=0.8, ls="--")
    ax.set_xticks(range(len(prot)))
    ax.set_xticklabels(prot)
    ax.set_ylabel(r"Protection AUC $\overline{\mathrm{RR}}$")
    ax.set_title(f"Funnel-integrated protection (stage {stage})")
    ax.set_ylim(0, 1.0)
    ax.grid(alpha=0.3, axis="y", lw=0.5)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, f"auc_stage_{stage}.png"), dpi=220)
    plt.close(fig)
