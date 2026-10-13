import argparse
import os
import numpy as np
import pandas as pd

TIERS = ["t0", "t1_jpeg95", "t1_jpeg85", "t1_jpeg75", "t1_jpeg65", "t1_webp80", "t2_canvas_dpr1",
         "t4_sr_x2", "t5_i2i30"]
TCOL = {"t0": "T0", "t1_jpeg95": "J95", "t1_jpeg85": "J85", "t1_jpeg75": "J75", "t1_jpeg65": "J65",
        "t1_webp80": "W80", "t2_canvas_dpr1": "T2",
        "t4_sr_x2": "T4", "t5_i2i30": "T5"}
TSHORT = {"t0": "to", "t1_jpeg95": "ja", "t1_jpeg85": "jb", "t1_jpeg75": "jc", "t1_jpeg65": "jd",
          "t1_webp80": "w", "t2_canvas_dpr1": "tb",
          "t4_sr_x2": "td", "t5_i2i30": "te"}
TIER_B = {"t0": "T0", "t1_jpeg85": "J85", "t2_canvas_dpr1": "T2", "t5_i2i30": "T5"}
MSHORT = {"clean": "cl", "random": "rn", "fsmg": "fg", "aspl": "as", "fsmgj": "fj", "instantid": "in", "ipfaceid": "if"}
OIDS = ["celeb00025", "celeb00027", "celeb00028", "celeb00029", "celeb00030", "celeb00031"]
PILOT_CUT = "2026-10-12 22:00:00"
PILOT_RERUN_TIERS = {"t0", "t1_jpeg85", "t2_canvas_dpr1", "t5_i2i30"}


def drop_pilot_reruns(df):
    ts = pd.to_datetime(df["ts"], errors="coerce")
    mask = (df["pid"].isin(OIDS) & (ts >= PILOT_CUT) & df["tier"].isin(PILOT_RERUN_TIERS)
            & df["method"].isin(["clean", "fsmg", "fsmgj"]))
    return df[~mask]


def fs(x):
    if np.isnan(x):
        return "--"
    return f"{x:.3f}" if (abs(x) >= 1 or x < 0) else f"{x:.3f}"[1:]


def fsr(x):
    return str(int(round(x * 100))) if not np.isnan(x) else "--"


def cell(sim, sr):
    return f"{fs(sim)}/{fsr(sr)}"


def bold_grid(pv, tiers, methods, skip_t5=True):
    best = {}
    for t in tiers:
        vals = {m: pv.get((m, t), np.nan) for m in methods}
        vv = {m: v for m, v in vals.items() if not np.isnan(v)}
        best[t] = min(vv, key=vv.get) if vv and not (skip_t5 and t == "t5_i2i30") else None
    return best


def stage_a_body(df, run_dir):
    a = df[(df.stage == "A") & (df.attack == "ipfaceid")]
    a = drop_pilot_reruns(a)
    pv = a.groupby(["method", "tier"])["mean_id"].mean()
    ps = a.groupby(["method", "tier"])["pos_rate"].mean()
    methods = ["clean", "random", "fsmg", "aspl", "fsmgj"]
    best = bold_grid(pv, TIERS, methods)
    lines = []
    for m in methods:
        cells = []
        for t in TIERS:
            c = cell(pv.get((m, t), np.nan), ps.get((m, t), np.nan))
            if best.get(t) == m:
                c = f"\\textbf{{{c}}}"
            cells.append(c)
        name = {"clean": "clean", "random": "random", "fsmg": "FSMG", "aspl": "ASPL", "fsmgj": "FSMG-J"}[m]
        lines.append(f"{name} & " + " & ".join(cells) + r" \\")
    auc_path = os.path.join(run_dir, "rr_auc_stage_A.csv")
    if os.path.exists(auc_path):
        au = pd.read_csv(auc_path).set_index("method")
        parts = []
        for m, label in [("random", "random"), ("fsmg", "FSMG"), ("aspl", "ASPL"), ("fsmgj", "FSMG-J")]:
            if m in au.index:
                r = au.loc[m]
                parts.append(f"{label} ${r.auc:.3f}\\,[{r.ci_lo:.3f},{r.ci_hi:.3f}]$")
        if parts:
            lines.append(r"\midrule")
            lines.append(r"\multicolumn{9}{@{}l}{$\overline{\mathrm{RR}}$ (95\% CI): " + " \\quad ".join(parts) + r"} \\")
    return "\n".join(lines) + "\n"


def stage_b_body(df, run_dir):
    b = df[(df.stage == "B")]
    pv = b.groupby(["method", "tier"])["mean_id"].mean()
    ps = b.groupby(["method", "tier"])["pos_rate"].mean()
    tiers = list(TIER_B)
    methods = ["clean", "random", "fsmg"]
    best = bold_grid(pv, tiers, methods, skip_t5=False)
    q = pd.DataFrame(columns=["psnr", "lpips"])
    qpath = os.path.join(run_dir, "quality.csv")
    if os.path.exists(qpath):
        q = pd.read_csv(qpath).set_index("method")
    lines = []
    for m in methods:
        cells = []
        for t in tiers:
            c = cell(pv.get((m, t), np.nan), ps.get((m, t), np.nan))
            if best.get(t) == m:
                c = f"\\textbf{{{c}}}"
            cells.append(c)
        name = {"clean": "clean", "random": "random", "fsmg": "FSMG"}[m]
        lines.append(f"{name} & " + " & ".join(cells) + r" \\")
    return "\n".join(lines) + "\n"


def stage_o_body(df, run_dir):
    spath = os.path.join(run_dir, "stage_o_complete_summary.csv")
    orders = ["canonical", "jpeg_only", "sr_first", "t5_first", "t5_only", "deep_chain"]
    if not os.path.exists(spath):
        return "\n".join(" & ".join(["--"] * 6) + r" \\" for _ in orders) + "\n"
    s = pd.read_csv(spath)
    idx = s.set_index(["order", "method"])
    lines = []
    for o in orders:
        def val(method, col):
            try:
                v = idx.loc[(o, method), col]
            except KeyError:
                return "--"
            return "--" if pd.isna(v) else f"{v:.3f}" if abs(v) >= 1 or v < 0 else f"{v:.3f}"[1:]
        c, fg, rd = idx.loc[(o, "clean")], idx.loc[(o, "fsmg")], idx.loc[(o, "random")]
        lines.append(f"{o.replace(chr(95), chr(92)+chr(95))} & {val('clean','unconditional_id')} / {c.detection_rate*100:.1f} & "
                     f"{val('fsmg','unconditional_id')} / {fg.detection_rate*100:.1f} & {val('fsmg','paired_gap')} & "
                     f"{val('fsmg','rr_vs_t0')} & {val('random','rr_vs_t0')} \\\\")
    return "\n".join(lines) + "\n"


def stress_body(df):
    tiers = ["t0", "t1_jpeg85", "t2_canvas_dpr1", "t5_i2i30"]
    sub = df[(df.stage == "A") & (df.attack == "ipfaceid") & (df.n_samples > 0)]
    sub = drop_pilot_reruns(sub)
    mpids = set(sub[sub.method == "fsmgj"]["pid"])
    sub = sub[sub.pid.isin(mpids)]
    pv = sub.groupby(["method", "tier"])["mean_id"].mean()
    ps = sub.groupby(["method", "tier"])["pos_rate"].mean()
    lines = []
    for m in ["clean", "fsmg", "fsmgj"]:
        cells = [cell(pv.get((m, t), np.nan), ps.get((m, t), np.nan)) for t in tiers]
        label = {"clean": "clean", "fsmg": "FSMG", "fsmgj": "FSMG-J"}[m]
        lines.append(f"{label} & " + " & ".join(cells) + r" \\")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="full")
    ap.add_argument("--results", default=None)
    args = ap.parse_args()
    run_dir = os.path.join("runs", args.run)
    res = args.results or os.path.join(run_dir, "results.csv")
    df = pd.read_csv(res)
    df["mean_id"] = pd.to_numeric(df["mean_id"], errors="coerce")
    df["pos_rate"] = pd.to_numeric(df["pos_rate"], errors="coerce")
    out = "paper/tables_auto"
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, "stageA_body.tex"), "w").write(stage_a_body(df, run_dir) + "\\bottomrule\n")
    open(os.path.join(out, "stageB_body.tex"), "w").write(stage_b_body(df, run_dir) + "\\bottomrule\n")
    open(os.path.join(out, "stageO_body.tex"), "w").write(stage_o_body(df, run_dir) + "\\bottomrule\n")
    open(os.path.join(out, "stress_body.tex"), "w").write(stress_body(df) + "\\bottomrule\n")
    print("tables written")


if __name__ == "__main__":
    main()
