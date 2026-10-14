import argparse
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ..config import load_config
from .results import log

TIER_ORDER = ["t0", "t1_jpeg95", "t1_jpeg85", "t1_jpeg75", "t1_jpeg65", "t1_webp80", "t1_platform",
              "t2_browser_dpr1", "t2_browser_dpr2", "t2_thumb_small", "t2_canvas_dpr1",
              "t3_agent_full", "t3_agent_facecrop", "t4_sr_x2", "t5_i2i30", "t5_i2i50",
              "t5_inversion", "mix20", "mix50", "purify50"]
EXCLUDE_TIERS = {"t3_agent_full", "t3_agent_facecrop"}
PILOT_IDS = {"celeb00025", "celeb00027", "celeb00028", "celeb00029", "celeb00030", "celeb00031"}
PILOT_CUT = "2026-10-12 22:00:00"
PILOT_RERUN_TIERS = {"t0", "t1_jpeg85", "t2_canvas_dpr1", "t5_i2i30"}
TRAPZ = getattr(np, "trapz", None) or np.trapezoid


def drop_pilot_reruns(df):
    ts = pd.to_datetime(df["ts"], errors="coerce")
    mask = (df["pid"].isin(PILOT_IDS) & (ts >= PILOT_CUT) & df["tier"].isin(PILOT_RERUN_TIERS)
            & df["method"].isin(["clean", "fsmg", "fsmgj"]))
    return df[~mask]


def pid_level_ci(df, stage, method, tier, n_boot=2000, seed=0):
    per_pid = df[(df["stage"] == stage) & (df["method"] == method) & (df["tier"] == tier)
                 & df["mean_id"].notna()].groupby("pid")["mean_id"].mean().dropna()
    vals = per_pid.values
    if len(vals) < 2:
        return float("nan"), (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(vals), size=(n_boot, len(vals)))
    means = vals[idx].mean(axis=1)
    lo, hi = np.quantile(means, [0.025, 0.975])
    return float(vals.mean()), (float(lo), float(hi))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    cfg = load_config(args.config)
    run_name = cfg["run"]["name"]
    run_dir = os.path.join("runs", run_name)
    res_path = os.path.join(run_dir, "results.csv")
    if not os.path.exists(res_path):
        print("no results yet")
        return
    df = pd.read_csv(res_path)
    df = df.dropna(subset=["mean_id"])
    df = df[~df.tier.isin(EXCLUDE_TIERS)]
    df = df[~((df["stage"] == "A") & (df["attack"] != "ipfaceid"))]
    df_raw = df.copy()
    df = drop_pilot_reruns(df)
    os.makedirs("figures", exist_ok=True)
    os.makedirs("report", exist_ok=True)
    tiers = [t for t in TIER_ORDER if t in set(df["tier"])]
    pv = df.groupby(["stage", "method", "tier"])["mean_id"].agg(["mean", "count"]).reset_index()
    pv.to_csv(os.path.join(run_dir, "summary_mean.csv"), index=False)
    pr = df.groupby(["stage", "method", "tier"])["pos_rate"].mean().reset_index()
    ci_rows = []
    for (stage, method, tier), _ in df.groupby(["stage", "method", "tier"]):
        mean, (lo, hi) = pid_level_ci(df, stage, method, tier)
        ci_rows.append({"stage": stage, "method": method, "tier": tier,
                        "pid_mean": round(mean, 4), "ci_lo": round(lo, 4), "ci_hi": round(hi, 4)})
    merged = pv.merge(pd.DataFrame(ci_rows)[["stage", "method", "tier", "ci_lo", "ci_hi"]],
                      on=["stage", "method", "tier"]).merge(pr, on=["stage", "method", "tier"])
    merged.to_csv(os.path.join(run_dir, "summary_ci.csv"), index=False)
    for stage in sorted(df["stage"].unique()):
        sub = merged[merged["stage"] == stage]
        tiers_s = [t for t in TIER_ORDER if t in set(df[df["stage"] == stage]["tier"])]
        if stage == "O":
            from .orders import ORDERS
            tiers_s = [t for t in ORDERS if t in set(df[df["stage"] == stage]["tier"])]
        base = sub[(sub["method"] == "clean")].set_index("tier")["mean"]
        rows = []
        for m in sub["method"].unique():
            msub = sub[sub["method"] == m].set_index("tier")
            row = {"method": m}
            for t in tiers_s:
                row[t] = round(float(msub["mean"][t]), 4) if t in msub.index else np.nan
            rows.append(row)
        tab = pd.DataFrame(rows)
        tab.to_csv(os.path.join(run_dir, f"table_stage_{stage}.csv"), index=False)
        if stage == "O":
            a0 = df_raw[(df_raw["stage"] == "A") & (df_raw["tier"] == "t0") & df_raw["mean_id"].notna()]
            pids_o = set(df[df["stage"] == "O"]["pid"])
            base_o = {}
            for m in ("fsmg", "random"):
                cm = a0[(a0["method"] == "clean") & (a0["pid"].isin(pids_o))]["mean_id"].mean()
                pm = a0[(a0["method"] == m) & (a0["pid"].isin(pids_o))]["mean_id"].mean()
                if not np.isnan(cm) and not np.isnan(pm):
                    base_o[m] = cm - pm
            gap_rows = []
            for m in sub["method"].unique():
                if m == "clean":
                    continue
                msub = sub[sub["method"] == m].set_index("tier")["mean"]
                row = {"method": m}
                for t in tiers_s:
                    row[t] = round(float((base[t] - msub[t]) / base_o[m]), 4) if t in msub.index and t in base.index and m in base_o else np.nan
                gap_rows.append(row)
            if gap_rows:
                pd.DataFrame(gap_rows).to_csv(os.path.join(run_dir, f"retention_stage_{stage}.csv"), index=False)
                from .order_fig import plot_order_rr
                plot_order_rr(pd.DataFrame(gap_rows), "figures")
            continue
        gap_rows = []
        for m in sub["method"].unique():
            if m == "clean":
                continue
            mpids = set(df[(df["stage"] == stage) & (df["method"] == m)]["pid"])
            csub_p = df[(df["stage"] == stage) & (df["method"] == "clean") & df["pid"].isin(mpids) & df["mean_id"].notna()]
            cpair = csub_p.groupby("tier")["mean_id"].mean()
            msub = sub[sub["method"] == m].set_index("tier")["mean"]
            base = cpair
            row = {"method": m}
            base_t0 = base.get("t0", np.nan)
            for t in tiers_s:
                if t not in msub.index or t not in base.index or np.isnan(base_t0):
                    row[t] = np.nan
                    continue
                delta_t = base[t] - msub[t]
                delta_0 = base["t0"] - msub["t0"]
                row[t] = round(float(delta_t / delta_0), 4) if abs(delta_0) > 1e-6 else np.nan
            gap_rows.append(row)
        if gap_rows:
            gtab = pd.DataFrame(gap_rows)
            gtab.to_csv(os.path.join(run_dir, f"retention_stage_{stage}.csv"), index=False)
            auc_rows = []
            for _, r in gtab.iterrows():
                seq = np.array([r[t] for t in tiers_s if t != "t0" and not np.isnan(r.get(t, np.nan))])
                if len(seq) < 2:
                    continue
                tier_list = [t for t in tiers_s if t != "t0" and not np.isnan(r.get(t, np.nan))]
                pids = sorted(set(df[(df["stage"] == stage) & (df["method"] == r["method"])]["pid"])
                              & set(df[(df["stage"] == stage) & (df["method"] == "clean")]["pid"]))
                pv_pid = {}
                cp_pid = {}
                for pid in pids:
                    g = df[(df["stage"] == stage) & (df["method"] == r["method"]) & (df["pid"] == pid) & df["mean_id"].notna()]
                    c = df[(df["stage"] == stage) & (df["method"] == "clean") & (df["pid"] == pid) & df["mean_id"].notna()]
                    pv_pid[pid] = g.groupby("tier")["mean_id"].mean()
                    cp_pid[pid] = c.groupby("tier")["mean_id"].mean()
                rng = np.random.default_rng(0)
                boots = []
                for _ in range(1000):
                    pick = rng.integers(0, len(pids), size=len(pids))
                    gsum = pd.concat([pv_pid[pids[i]] for i in pick]).groupby(level=0).mean()
                    csum = pd.concat([cp_pid[pids[i]] for i in pick]).groupby(level=0).mean()
                    if "t0" not in gsum.index or "t0" not in csum.index:
                        continue
                    denom = float(csum["t0"]) - float(gsum["t0"])
                    vals = np.array([
                        float("nan") if (t not in gsum.index or t not in csum.index or abs(denom) < 1e-6)
                        else (float(csum[t]) - float(gsum[t])) / denom
                        for t in tier_list
                    ])
                    if np.isnan(vals).any():
                        continue
                    # np.trapezoid was added after the NumPy version pinned by
                    # this project. np.trapz is equivalent for this 1-D AUC.
                    boots.append(TRAPZ(vals) / (len(vals) - 1))
                boots = np.array(boots)
                if boots.size == 0:
                    continue
                auc_rows.append({"method": r["method"], "auc": round(float(TRAPZ(seq) / (len(seq) - 1)), 4),
                                 "ci_lo": round(float(np.percentile(boots, 2.5)), 4),
                                 "ci_hi": round(float(np.percentile(boots, 97.5)), 4)})
            if auc_rows:
                pd.DataFrame(auc_rows).to_csv(os.path.join(run_dir, f"rr_auc_stage_{stage}.csv"), index=False)
                from .figures import plot_auc
                plot_auc(df, tiers_s, stage, "figures")
            from . import figures as F
            sub_m = sub[sub["method"].isin(list(gtab["method"]) + ["clean"])]
            F.plot_gap(df, tiers_s, stage, "figures")
            sig = F.plot_rr(df, tiers_s, stage, "figures")
            F.plot_det(df, tiers_s, stage, "figures")
            if stage == "B":
                from .figures import plot_family
                plot_family(df, "figures")
            with open(os.path.join(run_dir, f"rr_significance_{stage}.txt"), "w") as f:
                for m, s in sig.items():
                    f.write(f"{m}\t{s}\n")
    wil_rows = []
    from ..metrics.stats import cliffs_delta
    for (stage, tier), g in df.groupby(["stage", "tier"]):
        clean = g[g["method"] == "clean"].groupby("pid")["mean_id"].mean()
        for m in g["method"].unique():
            if m == "clean":
                continue
            prot = g[g["method"] == m].groupby("pid")["mean_id"].mean()
            common = clean.index.intersection(prot.index)
            if len(common) < 5:
                continue
            from scipy import stats
            stat, p = stats.wilcoxon(clean[common], prot[common])
            wil_rows.append(dict(stage=stage, tier=tier, method=m, n=len(common),
                                 stat=float(stat), p=float(p),
                                 cliffs_delta=round(cliffs_delta(clean[common].values, prot[common].values), 3)))
    if wil_rows:
        wdf = pd.DataFrame(wil_rows)
        from ..metrics.stats import holm
        wdf["p_holm"] = holm(wdf["p"].values)
        wdf.to_csv(os.path.join(run_dir, "wilcoxon.csv"), index=False)
    with open(os.path.join("report", "report.md"), "w") as f:
        f.write(f"# ScrapeBench run {run_name}\n\nGenerated {pd.Timestamp.now()}\n\n")
        f.write("## Mean identity similarity by method and tier\n\n")
        try:
            f.write(merged.to_markdown(index=False))
        except ImportError:
            # pandas delegates Markdown rendering to the optional `tabulate`
            # package. Keep report generation usable in the pinned runtime.
            f.write("```text\n")
            f.write(merged.to_string(index=False))
            f.write("\n```")
        f.write("\n\nSee figures/ for collapse curves and runs/*/retention_stage_*.csv for RR tables.\n")
    log("report written", os.path.join(run_dir, "report.log"))


if __name__ == "__main__":
    main()
