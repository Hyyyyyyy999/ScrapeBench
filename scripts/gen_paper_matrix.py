import argparse
import os
import numpy as np
import pandas as pd

TIERS = ["t0", "t1_jpeg85", "t1_webp80", "t2_canvas_dpr1", "t3_agent_facecrop", "t4_sr_x2", "t5_i2i30"]
TCOL = ["T0", "J85", "W80", "T2", "T3", "T4", "T5"]
METHODS = ["clean", "random", "fsmg", "aspl", "fsmgj", "arcp"]
LABELS = {"clean": "Clean", "random": "Random", "fsmg": "FSMG", "aspl": "ASPL", "fsmgj": "FSMG-J", "arcp": "\\textbf{ARCP}"}
T3_CUT = "2026-10-12 22:00:00"
OIDS = {"celeb00025", "celeb00027", "celeb00028", "celeb00029", "celeb00030", "celeb00031"}
PILOT_RERUN_TIERS = {"t0", "t1_jpeg85", "t2_canvas_dpr1", "t5_i2i30"}


def drop_pilot_reruns(df):
    ts = pd.to_datetime(df["ts"], errors="coerce")
    mask = (df["pid"].isin(OIDS) & (ts >= T3_CUT) & df["tier"].isin(PILOT_RERUN_TIERS)
            & df["method"].isin(["clean", "fsmg", "fsmgj"]))
    mask = mask | ((df["method"] == "arcp") & (ts < pd.Timestamp("2026-10-13 00:00:00")))
    return df[~mask]


def fs(x):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "--"
    return f"{x:.3f}" if (abs(x) >= 1 or x < 0) else f"{x:.3f}"[1:]


def fsr(x):
    return str(int(round(x * 100))) if not np.isnan(x) else "--"


def load(path):
    df = pd.read_csv(path)
    df["mean_id"] = pd.to_numeric(df["mean_id"], errors="coerce")
    df["pos_rate"] = pd.to_numeric(df["pos_rate"], errors="coerce")
    df["ts"] = df["ts"].astype(str)
    a = df[(df.stage == "A") & (df.attack == "ipfaceid")]
    return a


def cells(a, met, tier):
    sub = a[(a.method == met) & (a.tier == tier)]
    if not len(sub):
        return np.nan, np.nan
    return sub.mean_id.mean(), sub.pos_rate.mean()


def paired_rr(a, met, tier, gap0, mpids=None):
    if met == "clean" or np.isnan(gap0) or abs(gap0) < 1e-6:
        return np.nan
    sub = a[(a.method == met) & (a.tier == tier)]
    csub = a[(a.method == "clean") & (a.tier == tier)]
    if mpids is not None:
        sub = sub[sub.pid.isin(mpids)]
        csub = csub[csub.pid.isin(mpids)]
    if not len(sub) or not len(csub):
        return np.nan
    return (csub.mean_id.mean() - sub.mean_id.mean()) / gap0


def pilot_frame(a):
    sub = a[(a.n_samples > 0) & (a.ts >= T3_CUT) & (a.pid.isin(OIDS))]
    return sub


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="full")
    ap.add_argument("--outdir", default="paper/tables_auto")
    args = ap.parse_args()
    a = load(os.path.join("runs", args.run, "results.csv"))
    prim = drop_pilot_reruns(a[a.mean_id.notna() & ~a.tier.isin({"t3_agent_full", "t3_agent_facecrop"})])
    pil = pilot_frame(a)
    os.makedirs(args.outdir, exist_ok=True)
    pv = prim.groupby(["method", "tier"])["mean_id"].mean()
    sim_rows, rr_rows = [], []
    for met in METHODS:
        sims, rrs = [], []
        gap0 = np.nan
        mpids = None
        if met != "clean":
            mpids = set(prim[prim.method == met]["pid"])
            cp0 = prim[(prim.method == "clean") & (prim.pid.isin(mpids)) & (prim.tier == "t0")]["mean_id"].mean()
            gap0 = cp0 - pv.get((met, "t0"), np.nan)
        for j, t in enumerate(TIERS):
            if t == "t3_agent_facecrop":
                frame = pil
            else:
                frame = prim
            m, p = cells(frame, met, t)
            sims.append("--" if np.isnan(m) else f"{fs(m)}/{fsr(p)}")
            if j == 0:
                rrs.append("1.00")
                continue
            if t == "t3_agent_facecrop":
                gp = gap0
                if met != "clean":
                    c0 = pil[(pil.method == "clean") & (pil.tier == "t0")]["mean_id"].mean()
                    m0 = pil[(pil.method == met) & (pil.tier == "t0")]["mean_id"].mean()
                    if not (np.isnan(c0) or np.isnan(m0)):
                        gp = c0 - m0
                r = paired_rr(pil, met, t, gp, mpids=OIDS)
            else:
                r = paired_rr(prim, met, t, gap0, mpids=mpids)
            rrs.append(fs(r))
        rvals = [abs(float(x)) for x in rrs[1:] if x != "--"]
        if rvals and max(rvals) > 10.0:
            rrs = ["1.00"] + ["--"] * (len(TIERS) - 1)
        name = LABELS[met] + ("" if met == "clean" else "$^{\\dagger}$")
        sim_rows.append(name + " & " + " & ".join(sims) + " \\\\")
        rr_rows.append(name + " & " + " & ".join(rrs) + " \\\\")
    open(os.path.join(args.outdir, "matrix_sim_body.tex"), "w").write("\n".join(sim_rows) + "\n\\bottomrule\n")
    open(os.path.join(args.outdir, "matrix_rr_body.tex"), "w").write("\n".join(rr_rows) + "\n\\bottomrule\n")
    print("matrix tables written")


if __name__ == "__main__":
    main()
