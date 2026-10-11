import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from .figures import OKABE


ORDER_LABEL = {
    "canonical": "T1>T2>T3>T4>T5",
    "jpeg_only": "JPEG-85 only",
    "sr_first": "SR before transcode",
    "t5_first": "regen before transcode",
    "t5_only": "regen only",
    "deep_chain": "full deep chain",
}


def plot_order_rr(gtab, outdir):
    orders = [c for c in gtab.columns if c != "method"]
    methods = [m for m in gtab["method"] if m != "clean"]
    fig, ax = plt.subplots(figsize=(7.0, 2.4))
    width = 0.8 / max(1, len(methods))
    x = np.arange(len(orders))
    for i, m in enumerate(methods):
        vals = [float(gtab[gtab["method"] == m][t].iloc[0]) if t in gtab.columns else np.nan for t in orders]
        vals = [v if not np.isnan(v) else 0.0 for v in vals]
        ax.bar(x + (i - (len(methods) - 1) / 2) * width, vals, width * 0.92,
               color=OKABE.get(m), alpha=0.92, label=m)
    ax.axhline(1.0, color="#444444", lw=1.0, ls="--")
    ax.axhline(0.0, color="#999999", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([ORDER_LABEL.get(t, t) for t in orders], fontsize=8)
    ax.set_ylabel("RR")
    ax.set_title("Protection retention under acquisition programs (Stage O)", fontsize=10)
    ax.legend(frameon=False, fontsize=8, ncol=len(methods))
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "order_rr.png"), dpi=200)
    plt.close(fig)
