import argparse
import os
import numpy as np
import pandas as pd

TIERS = ["t0", "t1_jpeg95", "t1_jpeg85", "t1_jpeg75", "t1_jpeg65", "t1_webp80", "t2_canvas_dpr1",
         "t3_agent_facecrop", "t4_sr_x2", "t5_i2i30"]
TSHORT = {"t0": "to", "t1_jpeg95": "ja", "t1_jpeg85": "jb", "t1_jpeg75": "jc", "t1_jpeg65": "jd",
          "t1_webp80": "w", "t2_canvas_dpr1": "tb", "t3_agent_facecrop": "tc",
          "t4_sr_x2": "td", "t5_i2i30": "te"}
TIER_B = {"t0": "T0", "t1_jpeg85": "J85", "t2_canvas_dpr1": "T2", "t5_i2i30": "T5"}
MSHORT = {"clean": "cl", "random": "rn", "fsmg": "fg", "aspl": "as", "fsmgj": "fj", "arcp": "ac",
          "instantid": "in", "ipfaceid": "if"}
ORDERS = ["canonical", "jpeg_only", "sr_first", "t5_first", "t5_only", "deep_chain"]
OSHORT = {"canonical": "ca", "jpeg_only": "jo", "sr_first": "sf", "t5_first": "tf",
          "t5_only": "tvo", "deep_chain": "dc"}
OIDS = ["celeb00025", "celeb00027", "celeb00028", "celeb00029", "celeb00030", "celeb00031"]
PILOT_CUT = "2026-10-12 22:00:00"
PILOT_RERUN_TIERS = {"t0", "t1_jpeg85", "t2_canvas_dpr1", "t5_i2i30"}


def drop_pilot_reruns(df):
    ts = pd.to_datetime(df["ts"], errors="coerce")
    mask = (df["pid"].isin(OIDS) & (ts >= PILOT_CUT) & df["tier"].isin(PILOT_RERUN_TIERS)
            & df["method"].isin(["clean", "fsmg", "fsmgj"]))
    mask = mask | ((df["method"] == "arcp") & (ts < pd.Timestamp("2026-10-13 00:00:00")))
    return df[~mask]


def fs(x):
    if np.isnan(x):
        return "--"
    return f"{x:.3f}" if (abs(x) >= 1 or x < 0) else f"{x:.3f}"[1:]


def fsr(x):
    return str(int(round(x * 100))) if not np.isnan(x) else "--"


def fsq(x):
    return f"{x * 100:.1f}" if not np.isnan(x) else "--"


def build_macros(df, run_dir):
    m = {}

    def put(k, v):
        m[k] = v

    a = df[(df.stage == "A") & (df.attack == "ipfaceid") & (df.n_samples > 0)]
    a = drop_pilot_reruns(a)
    pv = a.groupby(["method", "tier"])["mean_id"].mean()
    ps = a.groupby(["method", "tier"])["pos_rate"].mean()
    for met in ["clean", "random", "fsmg", "aspl", "fsmgj", "arcp"]:
        for t in TIERS:
            put(f"nA{MSHORT[met]}{TSHORT[t]}", fs(pv.get((met, t), np.nan)))
            put(f"pA{MSHORT[met]}{TSHORT[t]}", fsr(ps.get((met, t), np.nan)))
    pair_clean = {}
    for met in ["random", "fsmg", "aspl", "fsmgj", "arcp"]:
        mpids = set(a[a.method == met]["pid"])
        csub = a[(a.method == "clean") & (a.pid.isin(mpids))]
        pc = csub.groupby("tier")["mean_id"].mean()
        pair_clean[met] = pc
        for t in TIERS:
            v = pc.get(t, np.nan)
            put(f"cA{MSHORT[met]}{TSHORT[t]}", fs(v))
            put(f"gA{MSHORT[met]}{TSHORT[t]}", fs(v - pv.get((met, t), np.nan)) if not np.isnan(v) else "--")
    gap = os.path.join(run_dir, "retention_stage_A.csv")
    if os.path.exists(gap):
        g = pd.read_csv(gap).set_index("method")
        for met in ["fsmg", "aspl", "random", "fsmgj", "arcp"]:
            for t in TIERS[1:]:
                put(f"rA{MSHORT[met]}{TSHORT[t]}", fs(g.loc[met].get(t, np.nan)) if met in g.index else "--")
        if "fsmg" in g.index:
            vals = [abs(float(g.loc[x].get("t5_i2i30", np.nan))) for x in ["fsmg", "aspl", "random", "fsmgj", "arcp"] if x in g.index and not np.isnan(g.loc[x].get("t5_i2i30", np.nan))]
            put("rAmaxte", fs(max(vals)) if vals else "--")
    auc = os.path.join(run_dir, "rr_auc_stage_A.csv")
    if os.path.exists(auc):
        au = pd.read_csv(auc).set_index("method")
        for met in ["random", "fsmg", "aspl", "fsmgj"]:
            if met in au.index:
                put(f"aA{MSHORT[met]}", f"{au.loc[met].auc:.3f}")
                put(f"lA{MSHORT[met]}", f"{au.loc[met].ci_lo:.3f}")
                put(f"hA{MSHORT[met]}", f"{au.loc[met].ci_hi:.3f}")
        if "arcp" in au.index:
            put(f"aA{MSHORT['arcp']}", f"{au.loc['arcp'].auc:.3f}")
            put(f"lA{MSHORT['arcp']}", f"{au.loc['arcp'].ci_lo:.3f}")
            put(f"hA{MSHORT['arcp']}", f"{au.loc['arcp'].ci_hi:.3f}")
    wpath = os.path.join(run_dir, "wilcoxon.csv")
    if os.path.exists(wpath):
        w = pd.read_csv(wpath)
        w = w[w.stage == "A"]
        for _, r in w.iterrows():
            p = r.p_holm
            put(f"wA{MSHORT.get(r.method, '')}{TSHORT.get(r.tier, '')}", (f"{p:.3f}" if p >= 0.001 else f"{p:.1e}"))
    b = df[df.stage == "B"]
    pvb = b.groupby(["method", "tier"])["mean_id"].mean()
    psb = b.groupby(["method", "tier"])["pos_rate"].mean()
    for met in ["clean", "random", "fsmg", "arcp"]:
        for t in TIER_B:
            put(f"nB{MSHORT[met]}{TSHORT[t]}", fs(pvb.get((met, t), np.nan)))
            put(f"pB{MSHORT[met]}{TSHORT[t]}", fsr(psb.get((met, t), np.nan)))
            put(f"qB{MSHORT[met]}{TSHORT[t]}", fsq(psb.get((met, t), np.nan)))
    gpath = os.path.join(run_dir, "retention_stage_B.csv")
    if os.path.exists(gpath):
        g = pd.read_csv(gpath).set_index("method")
        for met in ["random", "fsmg"]:
            for t in TIER_B:
                put(f"rB{MSHORT[met]}{TSHORT[t]}", fs(g.loc[met].get(t, np.nan)) if met in g.index else "--")
    bpath = os.path.join(run_dir, "rr_auc_stage_B.csv")
    if os.path.exists(bpath):
        bu = pd.read_csv(bpath).set_index("method")
        for met in ["random", "fsmg"]:
            if met in bu.index:
                put(f"aB{MSHORT[met]}", f"{bu.loc[met].auc:.3f}")
                put(f"lB{MSHORT[met]}", f"{bu.loc[met].ci_lo:.3f}")
                put(f"hB{MSHORT[met]}", f"{bu.loc[met].ci_hi:.3f}")
    c = df[df.stage == "C"]
    ref = a[(a.tier == "t0") & (a.pid.isin(set(c.pid)))] if len(c) else a[a.tier == "t0"]
    cmean = ref[ref.method == "clean"]["mean_id"].mean()
    d0 = cmean - ref[ref.method == "fsmg"]["mean_id"].mean()
    pvc = c.groupby("tier")["mean_id"].mean()
    psc = c.groupby("tier")["pos_rate"].mean()
    cmap = {"mixlo": "mix20", "mixhi": "mix50", "purif": "purify50"}
    for k, t in cmap.items():
        put(f"nC{k}", fs(pvc.get(t, np.nan)))
        put(f"pC{k}", fsr(psc.get(t, np.nan)))
        put(f"qC{k}", fsq(psc.get(t, np.nan)))
        rr = (cmean - pvc.get(t, np.nan)) / d0 if d0 and not np.isnan(pvc.get(t, np.nan)) else np.nan
        put(f"rC{k}", fs(rr))
    put("nCref", fs(cmean))
    go = None
    gopath = os.path.join(run_dir, "retention_stage_O.csv")
    if os.path.exists(gopath):
        go = pd.read_csv(gopath).set_index("method")
    for met in ["fsmg"]:
        for o in ORDERS:
            v = "--"
            if go is not None and met in go.index and o in go.columns and not np.isnan(go.loc[met][o]):
                v = f"{go.loc[met][o]:.2f}"
            put(f"rO{MSHORT[met]}{OSHORT[o]}", v)
    s = df[(df.stage == "A") & (df.pid.isin(OIDS)) & (df.tier.isin(TIER_B)) & (df.n_samples > 0)]
    for atk in ["ipfaceid", "instantid"]:
        su = s[s.attack == atk]
        pvs = su.groupby(["method", "tier"])["mean_id"].mean()
        pss = su.groupby(["method", "tier"])["pos_rate"].mean()
        for met in ["clean", "fsmg", "fsmgj"]:
            for t in TIER_B:
                put(f"n{MSHORT[atk].capitalize()}{MSHORT[met]}{TSHORT[t]}", fs(pvs.get((met, t), np.nan)))
                put(f"p{MSHORT[atk].capitalize()}{MSHORT[met]}{TSHORT[t]}", fsr(pss.get((met, t), np.nan)))
                put(f"q{MSHORT[atk].capitalize()}{MSHORT[met]}{TSHORT[t]}", fsq(pss.get((met, t), np.nan)))
    qpath = os.path.join(run_dir, "quality.csv")
    if os.path.exists(qpath):
        q = pd.read_csv(qpath).set_index("method")
        for met in ["fsmg", "random", "aspl", "arcp"]:
            if met in q.index:
                put(f"v{MSHORT[met]}", f"{q.loc[met]['psnr_db']:.1f}")
    for met in ["fsmg", "clean", "aspl", "arcp"]:
        d = a[(a.method == met) & (a.tier == "t5_i2i30")]
        v = (d["n_samples"] == 0).mean() if len(d) else np.nan
        put(f"iA{MSHORT[met]}", fsr(v))
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="full")
    args = ap.parse_args()
    run_dir = os.path.join("runs", args.run)
    df = pd.read_csv(os.path.join(run_dir, "results.csv"))
    df["mean_id"] = pd.to_numeric(df["mean_id"], errors="coerce")
    df["pos_rate"] = pd.to_numeric(df["pos_rate"], errors="coerce")
    m = build_macros(df, run_dir)
    os.makedirs("paper/sections", exist_ok=True)
    with open("paper/sections/numbers_auto.tex", "w") as f:
        for k, v in sorted(m.items()):
            f.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
    print(f"{len(m)} macros written")


if __name__ == "__main__":
    main()
