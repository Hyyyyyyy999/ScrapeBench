import csv
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

TIERS = ["t0", "t1_jpeg70", "t2_canvas_dpr1", "t3_agent_facecrop", "t4_sr_x2", "t5_i2i30", "t6_sde50"]
TLAB = ["T0", "T1", "T2", "T3", "T4", "T5", "T6"]
METHODS = ["gapdiff", "metacloak", "goodac", "arcp_web_v4"]
LABELS = {"gapdiff": "GAP-Diff", "metacloak": "MetaCloak", "goodac": "GoodAC", "arcp_web_v4": "ARCP-Web"}
COLORS = {"gapdiff": "#0072B2", "metacloak": "#E69F00", "goodac": "#009E73", "arcp_web_v4": "#D55E00"}
ATTACKS = ["instantid", "ipfaceid"]
ALAB = {"instantid": "InstantID (SDXL)", "ipfaceid": "IP-Adapter-FaceID (SD1.5)"}

rows = list(csv.DictReader(open("paper/web4_final_summary.csv")))
cells = {(r["attack"], r["method"], r["tier"]): r for r in rows}
clean_rank = {(r["attack"], r["tier"]): r["rankable"] == "True" for r in rows if r["method"] == "clean"}

pq = list(csv.DictReader(open("paper/web4_protection_quality.csv")))
psnr = defaultdict(list)
linf = defaultdict(list)
for r in pq:
    psnr[r["method"]].append(float(r["psnr_db_mean"]))
    linf[r["method"]].append(float(r["linf_px_max"]))

# Figure 1: paired gap with bootstrap CIs per reader x layer
fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9), sharey=False)
for ax, atk in zip(axes, ATTACKS):
    invalid = [k for k, t in enumerate(TIERS) if not clean_rank.get((atk, t), False)]
    for k in invalid:
        ax.axvspan(k - 0.5, k + 0.5, color="0.90", zorder=0)
    for mi, m in enumerate(METHODS):
        xs, ys, los, his = [], [], [], []
        for k, t in enumerate(TIERS):
            r = cells.get((atk, m, t))
            if r is None or r["rankable"] != "True" or not r["paired_gap"]:
                continue
            xs.append(k + (mi - 1.5) * 0.16)
            ys.append(float(r["paired_gap"]))
            los.append(float(r["paired_gap"]) - float(r["gap_ci_lo"]))
            his.append(float(r["gap_ci_hi"]) - float(r["paired_gap"]))
        lw = 2.4 if m == "arcp_web_v4" else 1.4
        ms = 7 if m == "arcp_web_v4" else 4.5
        ax.errorbar(xs, ys, yerr=[los, his], fmt="o", color=COLORS[m], label=LABELS[m],
                    capsize=2.2, elinewidth=1.0, ms=ms, lw=lw, zorder=5 if m == "arcp_web_v4" else 3)
    ax.axhline(0, color="0.35", lw=0.8, zorder=1)
    ax.set_xticks(range(len(TIERS)))
    ax.set_xticklabels(TLAB)
    ax.set_title(ALAB[atk], fontsize=10)
    ax.set_xlabel("acquisition layer", fontsize=9)
    ax.set_xlim(-0.5, len(TIERS) - 0.5)
    for k in invalid:
        ax.annotate("\u2020", (k, ax.get_ylim()[1] * 0.92), ha="center", fontsize=9, color="0.35")
axes[0].set_ylabel(r"paired gap $\Delta$ (clean $-$ protected)", fontsize=9)
axes[1].legend(fontsize=7.5, loc="lower right", framealpha=0.92)
for ax in axes:
    ax.tick_params(labelsize=8.5)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
fig.tight_layout()
fig.savefig("paper/figures/web4_gap_ci.png", dpi=300, bbox_inches="tight")
plt.close(fig)

# Figure 2: protection-quality Pareto
fig2, ax2 = plt.subplots(figsize=(3.5, 2.9))
marker = {"instantid": "o", "ipfaceid": "s"}
summary = defaultdict(dict)
for atk in ATTACKS:
    for m in METHODS:
        gaps = [float(cells[(atk, m, t)]["paired_gap"]) for t in TIERS
                if cells.get((atk, m, t)) and cells[(atk, m, t)]["rankable"] == "True" and cells[(atk, m, t)]["paired_gap"]]
        if gaps:
            summary[m][atk] = np.mean(gaps)
for m in METHODS:
    p = np.mean(psnl) if False else np.mean(psnr[m])
    l = np.max(linf[m])
    y = np.mean([v for v in summary[m].values()]) if len(summary[m]) == 2 else list(summary[m].values())[0]
    is_arcp = m == "arcp_web_v4"
    ax2.scatter(p, y, s=110 if is_arcp else 55, color=COLORS[m], zorder=5 if is_arcp else 3,
                edgecolor="black" if is_arcp else "none", linewidth=1.2 if is_arcp else 0)
    ax2.annotate(f"{LABELS[m]}\n({p:.1f} dB)", (p, y), textcoords="offset points",
                 xytext=(8, -4 if not is_arcp else -10), fontsize=7.2,
                 fontweight="bold" if is_arcp else "normal")
ax2.set_xlabel("mean upload PSNR (dB)", fontsize=9)
ax2.set_ylabel(r"mean paired gap $\Delta$ (rankable cells)", fontsize=9)
ax2.tick_params(labelsize=8)
for s in ("top", "right"):
    ax2.spines[s].set_visible(False)
fig2.tight_layout()
fig2.savefig("paper/figures/web4_pareto.png", dpi=300, bbox_inches="tight")
plt.close(fig2)

for m in METHODS:
    print(m, "PSNR", round(float(np.mean(psnr[m])), 2), "Linf", max(linf[m]), "gaps", {k: round(v, 3) for k, v in summary[m].items()})
print("figures written")
