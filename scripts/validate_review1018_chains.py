#!/usr/bin/env python3
from pathlib import Path

root = Path("runs/web40_single_intervention/generations")
ids = sorted(p.name for p in Path("data/web40/raw").iterdir() if p.is_dir())[:4]
methods = ("clean", "gapdiff", "idprotector", "arcp_web_v4")
orders = ("jpeg70_crop", "feed_crop", "cdn_feed_crop")
missing = []
for attack in ("instantid", "ipfaceid"):
    for method in methods:
        for order in orders:
            for pid in ids:
                p = root / (attack + "_chain") / method / order / pid / "samples.jsonl"
                if not p.is_file() or len([x for x in p.read_text().splitlines() if x.strip()]) != 4:
                    missing.append((attack, method, order, pid))
if missing: raise SystemExit(f"chain experiment incomplete: {len(missing)}/96 cells missing")
print("PASS: all 96 continuous-chain cells complete")
