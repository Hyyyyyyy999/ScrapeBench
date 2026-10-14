"""Generate the two main-text figures for the ScrapeBench paper.

Figure 1 (fig:overview replacement): rendered acquisition-funnel overview,
replacing the previous typographic minipage diagram with the same label.
Figure 2 (fig:rr): Stage-A retention-ratio collapse curves from
runs/full/retention_stage_A.csv.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGDIR = os.path.join(ROOT, "paper", "figures")
os.makedirs(FIGDIR, exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["DejaVu Serif"],
    "mathtext.fontset": "dejavuserif",
    "axes.linewidth": 0.6,
})


def funnel_overview():
    fig, ax = plt.subplots(figsize=(3.35, 2.95), dpi=300)
    ax.set_xlim(0, 3.35)
    ax.set_ylim(0, 2.83)
    ax.axis("off")

    boxes = [
        ("T0", "Defender publishes protected gallery",
         r"$\|\delta\|_\infty \leq 16/255$"),
        ("T1", "Platform transcode: JPEG · WebP re-encode",
         "$\\approx$5 ms/img"),
        ("T2", "Browser & thumbnail render (DPR 1–2)",
         "$\\approx$40 ms/img"),
        ("T3", "Agent capture: screenshot + face crop",
         "<200 ms/img"),
        ("T4", "Restoration: SR ×2 · denoise",
         "$\\approx$1.0 s/img"),
        ("T5", "Regeneration: img2img · DDIM",
         "$\\approx$3.5 s/img"),
        ("T6", "Adaptive: mixing · purification",
         "budgeted"),
        ("P", "Adversary readers: DreamBooth ·\nIP-Adapter · InstantID",
         None),
    ]

    bh, gap = 0.30, 0.05
    bw = 3.27
    x0 = 0.04
    top = 2.79
    for i, (tag, desc, budget) in enumerate(boxes):
        y = top - (i + 1) * bh - i * gap
        is_endpoint = tag in ("T0", "P")
        face = "#e8eef7" if is_endpoint else "#f2f2f2"
        edge = "#1f4e79" if is_endpoint else "#4d4d4d"
        ax.add_patch(FancyBboxPatch(
            (x0, y), bw, bh, boxstyle="round,pad=0.01,rounding_size=0.03",
            linewidth=0.8, edgecolor=edge, facecolor=face))
        ax.text(x0 + 0.17, y + bh / 2, tag, ha="center", va="center",
                fontsize=6.5, fontweight="bold", color=edge)
        ds = 5.8 if len(desc) > 44 else 6.5
        cy = y + bh - 0.105 if "\n" not in desc else y + bh / 2 - 0.02
        ax.text(x0 + bw / 2, cy, desc, ha="center", va="center",
                fontsize=ds, linespacing=1.15)
        if budget is not None:
            ax.text(x0 + bw - 0.08, y + 0.038, budget, ha="right",
                    va="bottom", fontsize=5.4, color="#444444")
        if i < len(boxes) - 1:
            ax.add_patch(FancyArrowPatch(
                (x0 + bw / 2, y - 0.005), (x0 + bw / 2, y - gap + 0.005),
                arrowstyle="-|>", mutation_scale=6, linewidth=0.8,
                color="#4d4d4d", shrinkA=0, shrinkB=0))

    fig.savefig(os.path.join(FIGDIR, "funnel_overview.png"),
                bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def rr_curves():
    csv = os.path.join(ROOT, "runs", "full", "retention_stage_A.csv")
    df = pd.read_csv(csv).set_index("method")
    tiers = ["t0", "t1_jpeg95", "t1_jpeg85", "t1_jpeg75", "t1_jpeg65",
             "t1_webp80", "t2_canvas_dpr1", "t4_sr_x2", "t5_i2i30"]
    labels = ["T0", "J95", "J85", "J75", "J65", "W80", "T2", "T4", "T5"]

    series = [
        ("fsmg", "FSMG", "#1f4e79", "-", "o"),
        ("aspl", "ASPL-lite", "#c0392b", "--", "s"),
        ("fsmgj", "FSMG-J", "#2e7d32", ":", "^"),
        ("random", "Random control", "#6a1b9a", "-.", "D"),
    ]

    fig, ax = plt.subplots(figsize=(3.35, 1.95), dpi=300)
    x = range(len(tiers))
    t5 = len(tiers) - 1
    ax.axvspan(t5 - 0.5, t5 + 0.5, color="#f5d5d5", alpha=0.5, zorder=0)
    ax.axhline(1.0, color="#888888", linewidth=0.7, linestyle=(0, (4, 3)),
               zorder=1)
    ax.text(0.15, 1.035, "no loss ($\\mathrm{RR}=1$)", fontsize=5.6,
            color="#555555")

    for key, label, color, ls, marker in series:
        y = [df.loc[key, t] for t in tiers]
        ax.plot(x, y, ls, marker=marker, color=color, linewidth=1.1,
                markersize=3.0, label=label, zorder=3)

    ax.text(t5, 0.75, "clean baseline\ncollapses", ha="center", va="center",
            fontsize=5.6, color="#8a2a2a", linespacing=1.2)

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=6.5)
    ax.set_ylabel("retention ratio RR($T$)", fontsize=7)
    ax.set_ylim(0, 2.65)
    ax.set_xlim(-0.5, len(tiers) - 0.5)
    ax.tick_params(axis="y", labelsize=6.5, length=2, width=0.5)
    ax.tick_params(axis="x", length=2, width=0.5)
    ax.grid(axis="y", linewidth=0.3, color="#dddddd", zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(fontsize=6.0, loc="lower left", frameon=True, framealpha=0.9,
              borderpad=0.3, handlelength=2.2, labelspacing=0.25)
    fig.tight_layout(pad=0.3)
    fig.savefig(os.path.join(FIGDIR, "rr_stage_A.png"),
                bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


if __name__ == "__main__":
    funnel_overview()
    rr_curves()
    print("figures written to", FIGDIR)
