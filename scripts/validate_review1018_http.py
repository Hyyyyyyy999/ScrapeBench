#!/usr/bin/env python3
import json
from pathlib import Path
root=Path("runs/web4_http_roundtrip/generations")
ids=sorted(p.name for p in Path("data/web40/raw").iterdir() if p.is_dir())[:4]
methods=("clean_http_roundtrip","gapdiff_http_roundtrip","idprotector_http_roundtrip","arcp_web_v4_http_roundtrip")
missing=[]
for a in ("instantid","ipfaceid"):
 for m in methods:
  for pid in ids:
   p=root/a/m/"t0"/pid/"samples.jsonl"
   rows=([json.loads(x) for x in p.read_text().splitlines() if x.strip()] if p.is_file() else [])
   if len(rows)!=4 or {int(row["prompt_id"]) for row in rows}!={0,1,2,3}: missing.append((a,m,pid))
if missing: raise SystemExit(f"HTTP closed loop incomplete: {len(missing)}/32 cells missing")
print("PASS: all 32 HTTP upload--scrape--generate cells complete")
