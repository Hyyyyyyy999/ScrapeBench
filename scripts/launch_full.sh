#!/bin/bash
set -u
cd "$(dirname "$0")/.."
mkdir -p logs figures
FULL_IDS=$(python3 - <<'PY'
import os
ids = []
for p in sorted(os.listdir("data/raw")):
    g = os.path.join("data/raw", p)
    r = os.path.join("data/refs", p)
    if not os.path.isdir(g) or not os.path.isdir(r):
        continue
    ng = len([f for f in os.listdir(g) if f.lower().endswith((".jpg", ".png"))])
    nr = len(os.listdir(r))
    if ng >= 8 and nr >= 2:
        ids.append(p)
print(",".join(ids))
PY
)
NALL=$(echo "$FULL_IDS" | awk -F, '{print NF}')
NA=${NA:-$NALL}
IDS=$(echo "$FULL_IDS" | cut -d, -f1-$NA)
H1=$(echo "$IDS" | cut -d, -f1-20)
H2=$(echo "$IDS" | cut -d, -f21-$NA)
BIDS=$(echo "$IDS" | cut -d, -f1-12)
echo "full ids ($NALL avail, using $NA): $IDS"
echo "half1: $H1"
echo "half2: $H2"
echo "stageb/c ids: $BIDS"
PULL="git -c credential.helper= -c http.extraheader=AUTHORIZATION:\ basic\ $(echo -n x-access-token:$(cat /root/.scrapebench_pat) | base64 -w0)"
$PULL pull -q origin main
nohup bash -c "CUDA_VISIBLE_DEVICES=0 python3 -m scrapebench.runner.protection_run --config configs/full.yaml --methods clean,random --ids $H1 >> logs/full_prot0.log 2>&1 && CUDA_VISIBLE_DEVICES=0 python3 -m scrapebench.runner.stage_a --config configs/full.yaml --methods clean,random --ids $IDS >> logs/full_a0.log 2>&1 && CUDA_VISIBLE_DEVICES=0 python3 -m scrapebench.runner.stage_b --config configs/full.yaml --methods clean,random,fsmg --ids $BIDS >> logs/full_b0.log 2>&1" > /dev/null 2>&1 &
echo "gpu0 chain pid $!"
nohup bash -c "CUDA_VISIBLE_DEVICES=1 python3 -m scrapebench.runner.protection_run --config configs/full.yaml --methods fsmg,aspl --ids $H2 >> logs/full_prot1.log 2>&1 && CUDA_VISIBLE_DEVICES=1 python3 -m scrapebench.runner.stage_a --config configs/full.yaml --methods fsmg,aspl --ids $IDS >> logs/full_a1.log 2>&1 && CUDA_VISIBLE_DEVICES=1 python3 -m scrapebench.runner.stage_c --config configs/full.yaml --ids $BIDS >> logs/full_c1.log 2>&1" > /dev/null 2>&1 &
echo "gpu1 chain pid $!"
nohup bash scripts/watch_and_push.sh > logs/watch_push.log 2>&1 &
echo "watcher pid $!"
