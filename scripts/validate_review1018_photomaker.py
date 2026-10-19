#!/usr/bin/env python3
import json
from pathlib import Path
root = Path("runs/web4_photomaker/generations/photomaker")
ids = sorted(p.name for p in Path("data/web40/raw").iterdir() if p.is_dir())[:4]
methods = ("clean", "gapdiff", "idprotector", "arcp_web_v4")
tiers = ("t0", "t1_jpeg70", "t2_canvas_dpr1", "t3_agent_facecrop", "t4_sr_x2", "t5_i2i30", "t6_sde35")
missing=[]
for m in methods:
 for t in tiers:
  for pid in ids:
   p=root/m/t/pid/"samples.jsonl"
   rows=([json.loads(x) for x in p.read_text().splitlines() if x.strip()] if p.is_file() else [])
   if len(rows)!=4 or {int(row["prompt_id"]) for row in rows}!={0,1,2,3}: missing.append((m,t,pid))
if missing: raise SystemExit(f"PhotoMaker incomplete: {len(missing)}/112 cells missing")
print("PASS: all 112 PhotoMaker cells complete")
