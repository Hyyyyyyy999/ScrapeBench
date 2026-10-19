#!/usr/bin/env python3
"""Render the completed Web40 ledger into LaTeX without hand-copied numbers."""
import csv
from pathlib import Path


def f(x):
    try: return f"{float(x):.3f}"
    except Exception: return "--"


root = Path("runs/web40_single_intervention")
rows = list(csv.DictReader((root / "web40_full_summary.csv").open()))
index = {(r["attack"], r["method"], r["tier"]): r for r in rows}
tiers = [("t0", "T0"), ("t1_jpeg70", "T1"), ("t2_canvas_dpr1", "T2"),
         ("t3_agent_facecrop", "T3"), ("t4_sr_x2", "T4"),
         ("t5_i2i30", "T5"), ("t6_sde35", "T6")]
methods = [("clean", "Clean"), ("gapdiff", "GAP-Diff"),
           ("idprotector", "IDProtector"), ("arcp_web_v4", "ARCP-Web")]
out = ["% Auto-generated from per-sample JSONL ledgers; do not edit by hand."]
for attack, title in (("instantid", "InstantID"), ("ipfaceid", "IP-Adapter-FaceID")):
    out += ["\\begin{table*}[t]", "\\centering",
            f"\\caption{{Forty-identity results for {title}. Lower E2E ISM/FDFR-adjusted identity similarity is better; higher paired gap is better. Parentheses give the identity-bootstrap 95\\% CI. A dagger marks a layer that fails the preregistered clean rankability gate.}}",
            f"\\label{{tab:web40-{attack}}}", "\\scriptsize",
            "\\setlength{\\tabcolsep}{2.8pt}", "\\begin{tabular}{llrrr}",
            "\\toprule",
            r"Layer & Defense & IDs & E2E ISM$\downarrow$ & Paired gap$\uparrow$ [95\% CI] \\",
            "\\midrule"]
    for tier, short in tiers:
        for method, label in methods:
            r = index.get((attack, method, tier))
            if not r: continue
            mark = "" if r.get("rankable", "False").lower() == "true" else "$^{\\dagger}$"
            gap = "--" if method == "clean" else f"{f(r['paired_gap'])} [{f(r['gap_ci_lo'])},{f(r['gap_ci_hi'])}]"
            out.append(f"{short}{mark} & {label} & {r['n_ids']} & {f(r['e2e_ism'])} & {gap} " + r"\\")
        out.append("\\addlinespace[1pt]")
    out += ["\\bottomrule", "\\end{tabular}", "\\end{table*}", ""]
Path("paper/tables").mkdir(parents=True, exist_ok=True)
Path("paper/tables/review1018_web40_auto.tex").write_text("\n".join(out) + "\n")
print("wrote paper/tables/review1018_web40_auto.tex")
