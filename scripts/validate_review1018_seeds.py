#!/usr/bin/env python3
from pathlib import Path

ids = sorted(p.name for p in Path("data/web40/raw").iterdir() if p.is_dir())[:4]
methods = ("clean", "gapdiff", "idprotector", "arcp_web_v4")
tiers = ("t0", "t1_jpeg70", "t3_agent_facecrop", "t5_i2i30")
missing = []
for seed in (20261019, 20261020):
    root = Path(f"runs/web4_seed_{seed}/generations")
    for attack in ("instantid", "ipfaceid"):
        for method in methods:
            for tier in tiers:
                for pid in ids:
                    p = root / attack / method / tier / pid / "samples.jsonl"
                    if not p.is_file() or len([x for x in p.read_text().splitlines() if x.strip()]) != 4:
                        missing.append((seed, attack, method, tier, pid))
if missing: raise SystemExit(f"seed replication incomplete: {len(missing)}/256 cells missing")
print("PASS: 256 two-seed replication cells complete")
