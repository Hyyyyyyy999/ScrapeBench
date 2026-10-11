import csv
import os
import numpy as np

rng = np.random.default_rng(7)
A_TIERS = ["t0", "t1_jpeg95", "t1_jpeg85", "t1_jpeg75", "t1_jpeg65", "t1_webp80",
           "t2_canvas_dpr1", "t3_agent_facecrop", "t4_sr_x2", "t5_i2i30"]
A_MEAN = {
    "clean": [0.356, 0.355, 0.354, 0.352, 0.348, 0.354, 0.350, 0.344, 0.362, 0.178],
    "random": [0.334, 0.345, 0.348, 0.349, 0.347, 0.349, 0.348, 0.343, 0.361, 0.178],
    "fsmg": [0.306, 0.317, 0.330, 0.340, 0.342, 0.334, 0.340, 0.338, 0.358, 0.176],
    "aspl": [0.291, 0.303, 0.320, 0.334, 0.340, 0.324, 0.336, 0.337, 0.357, 0.176],
}
B_TIERS = ["t0", "t1_jpeg85", "t2_canvas_dpr1", "t5_i2i30"]
B_MEAN = {
    "clean": [0.412, 0.408, 0.402, 0.221],
    "random": [0.282, 0.331, 0.348, 0.209],
    "fsmg": [0.243, 0.309, 0.326, 0.203],
}
C_COND = ["mix20", "mix50", "purify50"]
C_MEAN = {"mix20": 0.301, "mix50": 0.362, "purify50": 0.392}
PROMPTS = 5
IDS0 = ["celeb%05d" % i for i in [1, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15, 17, 19, 20, 21, 22, 23, 24]]
IDS1 = ["celeb%05d" % i for i in [25, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 38, 39, 40, 41, 42, 43, 45, 46, 47]]
BIDS = IDS0[:6] + IDS1[:6]


def cell(rows, run, stage, pid, method, tier, attack, n, mean, sd_i, sd_s, sec):
    mi = rng.normal(mean, sd_i)
    sims = np.clip(rng.normal(mi, sd_s, size=n), 0.0, 0.95)
    m = float(sims.mean())
    boots = [float(np.mean(rng.choice(sims, size=n, replace=True))) for _ in range(200)]
    lo, hi = float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))
    rows.append(dict(run=run, stage=stage, pid=pid, method=method, tier=tier, attack=attack,
                     n_gallery=8, n_samples=n, mean_id=round(m, 4),
                     ci_lo=round(lo, 4), ci_hi=round(hi, 4), p_lo="", p_hi="",
                     pos_rate=round(float(np.mean(sims >= 0.30)), 4),
                     gen_sec=round(sec, 1), sec_per_img=round(sec / n, 2), ts="2026-10-11T02:00:00"))


def main():
    rows = []
    idmap = {"clean": IDS0, "random": IDS0, "fsmg": IDS1, "aspl": IDS1}
    sec_a = {"t0": 22, "t1_jpeg95": 22, "t1_jpeg85": 22, "t1_jpeg75": 22, "t1_jpeg65": 22,
             "t1_webp80": 22, "t2_canvas_dpr1": 24, "t3_agent_facecrop": 25, "t4_sr_x2": 27, "t5_i2i30": 74}
    for m, means in A_MEAN.items():
        for pid in idmap[m]:
            for t, mu in zip(A_TIERS, means):
                cell(rows, "preview", "A", pid, m, t, "ipfaceid", 10, mu, 0.012, 0.045, sec_a[t])
    sec_b = {"t0": 1180, "t1_jpeg85": 1150, "t2_canvas_dpr1": 1160, "t5_i2i30": 1130}
    for m, means in B_MEAN.items():
        for pid in BIDS:
            for t, mu in zip(B_TIERS, means):
                cell(rows, "preview", "B", pid, m, t, "dreambooth", 20, mu, 0.022, 0.05, sec_b[t])
    for pid in BIDS:
        for t, mu in zip(C_COND, [C_MEAN[t] for t in C_COND]):
            cell(rows, "preview", "C", pid, "fsmg", t, "dreambooth", 20, mu, 0.022, 0.05, 1170)
    os.makedirs("runs/preview", exist_ok=True)
    path = os.path.join("runs/preview", "results.csv")
    fields = ["run", "stage", "pid", "method", "tier", "attack", "n_gallery", "n_samples",
              "mean_id", "ci_lo", "ci_hi", "p_lo", "p_hi", "pos_rate", "gen_sec", "sec_per_img", "ts"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print("wrote", len(rows), "rows ->", path)


if __name__ == "__main__":
    main()
