#!/usr/bin/env python3
"""Fail closed unless every preregistered 18 October cell has a sample ledger."""
import json
from pathlib import Path

RUN = Path("runs/web40_single_intervention/generations")
TIERS = ("t0", "t1_jpeg70", "t2_canvas_dpr1", "t3_agent_facecrop", "t4_sr_x2", "t5_i2i30", "t6_sde35")
FULL40 = ("arcp_web_v4", "gapdiff_8", "idprotector_8")
T6ONLY = ("clean", "gapdiff", "idprotector")
ABL = ("arcp_web_v4_uniform", "arcp_web_v4_no_texture", "arcp_web_v4_no_coarse",
       "arcp_web_v4_no_detail", "arcp_web_v4_no_identity", "arcp_web_v4_no_denoise")


def ids():
    return sorted(p.name for p in Path("data/web40/raw").iterdir() if p.is_dir())


def ok(attack, method, tier, pid):
    p = RUN / attack / method / tier / pid / "samples.jsonl"
    if not p.is_file():
        return False
    rows = [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
    return len(rows) == 4 and {int(row["prompt_id"]) for row in rows} == {0, 1, 2, 3}


missing = []
all_ids = ids()
for attack in ("instantid", "ipfaceid"):
    for method in FULL40:
        for tier in TIERS:
            missing += [(attack, method, tier, pid) for pid in all_ids if not ok(attack, method, tier, pid)]
    for method in T6ONLY:
        missing += [(attack, method, "t6_sde35", pid) for pid in all_ids if not ok(attack, method, "t6_sde35", pid)]
    for method in ABL:
        for tier in TIERS:
            missing += [(attack, method, tier, pid) for pid in all_ids[:4] if not ok(attack, method, tier, pid)]
if missing:
    for item in missing[:50]: print("MISSING", "/".join(item))
    raise SystemExit(f"incomplete: {len(missing)} preregistered cells missing")
print("PASS: all 2256 preregistered review-1018 cells have four-sample ledgers")
