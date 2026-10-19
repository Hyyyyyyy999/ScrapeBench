#!/usr/bin/env python3
"""Fail closed unless the preregistered four-ID DreamBooth grid is complete."""
import json
from pathlib import Path

root = Path("runs/web40_single_intervention/generations/dreambooth")
ids = sorted(p.name for p in Path("data/web40/raw").iterdir() if p.is_dir())[:4]
methods = ("clean", "gapdiff", "idprotector", "arcp_web_v4")
tiers = ("t0", "t1_jpeg70", "t2_canvas_dpr1", "t3_agent_facecrop",
         "t4_sr_x2", "t5_i2i30", "t6_sde35")
missing = []
for method in methods:
    for pid in ids:
        for tier in tiers:
            p = root / method / tier / pid / "samples.jsonl"
            rows = ([json.loads(x) for x in p.read_text().splitlines() if x.strip()]
                    if p.is_file() else [])
            if len(rows) != 4 or {int(row["prompt_id"]) for row in rows} != {0, 1, 2, 3}:
                missing.append((method, tier, pid))
if missing:
    for x in missing[:30]: print("MISSING", "/".join(x))
    raise SystemExit(f"DreamBooth incomplete: {len(missing)}/112 cells missing")
print("PASS: all 112 DreamBooth cells have four-scenario ledgers")
