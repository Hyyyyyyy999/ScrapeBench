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
    os.makedirs("figures", exist_ok=True)
    os.makedirs("report", exist_ok=True)
    tiers = [t for t in TIER_ORDER if t in set(df["tier"])]
    pv = df.groupby(["stage", "method", "tier"])["mean_id"].agg(["mean", "count"]).reset_index()
    pv.to_csv(os.path.join(run_dir, "summary_mean.csv"), index=False)
    lo = df.groupby(["stage", "method", "tier"])["ci_lo"].mean().reset_index()
    hi = df.groupby(["stage", "method", "tier"])["ci_hi"].mean().reset_index()
    merged = pv.merge(lo, on=["stage", "method", "tier"]).merge(hi, on=["stage", "method", "tier"])
    merged.to_csv(os.path.join(run_dir, "summary_ci.csv"), index=False)
    for stage in sorted(df["stage"].unique()):
        sub = merged[merged["stage"] == stage]
        base = sub[(sub["method"] == "clean")].set_index("tier")["mean"]
        rows = []
        for m in sub["method"].unique():
            msub = sub[sub["method"] == m].set_index("tier")
            row = {"method": m}
            for t in tiers:
                row[t] = round(float(msub["mean"][t]), 4) if t in msub.index else np.nan
            rows.append(row)
        tab = pd.DataFrame(rows)
        tab.to_csv(os.path.join(run_dir, f"table_stage_{stage}.csv"), index=False)
        gap_rows = []
        for m in sub["method"].unique():
            if m == "clean":
                continue
            msub = sub[sub["method"] == m].set_index("tier")["mean"]
            row = {"method": m}
            base_t0 = base.get("t0", np.nan)
            for t in tiers:
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
            from .figures import plot_gap, plot_rr, plot_det
            sub_m = sub[sub["method"].isin(list(gtab["method"]) + ["clean"])]
            plot_gap(sub_m, tiers, stage, "figures")
            sig = plot_rr(sub_m, tiers, stage, "figures")
            plot_det(df, tiers, stage, "figures")
            with open(os.path.join(run_dir, f"rr_significance_{stage}.txt"), "w") as f:
                for m, s in sig.items():
                    f.write(f"{m}\t{s}\n")
    wil_rows = []
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
                                 stat=float(stat), p=float(p)))
    if wil_rows:
        wdf = pd.DataFrame(wil_rows)
        from ..metrics.stats import holm
        wdf["p_holm"] = holm(wdf["p"].values)
        wdf.to_csv(os.path.join(run_dir, "wilcoxon.csv"), index=False)
    with open(os.path.join("report", "report.md"), "w") as f:
        f.write(f"# ScrapeBench run {run_name}\n\nGenerated {pd.Timestamp.now()}\n\n")
        f.write("## Mean identity similarity by method and tier\n\n")
        f.write(merged.to_markdown(index=False))
        f.write("\n\nSee figures/ for collapse curves and runs/*/retention_stage_*.csv for RR tables.\n")
    log("report written", os.path.join(run_dir, "report.log"))


if __name__ == "__main__":
    main()
