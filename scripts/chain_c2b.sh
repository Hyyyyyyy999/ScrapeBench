#!/bin/bash
cd /root/scrapebench || exit 1
while pgrep -f "chain_instant\.sh" > /dev/null || pgrep -f "runner.stage_a" > /dev/null; do sleep 120; done
echo "$(date '+%F %T') c2b: starting stage_c completion on GPU0" >> logs/c2b.log
for i in 1 2 3; do
  CUDA_VISIBLE_DEVICES=0 python3 -m scrapebench.runner.stage_c --config configs/full.yaml >> logs/c2b.log 2>&1 && break
  echo "$(date '+%F %T') c2b retry $i" >> logs/c2b.log; sleep 60
done
echo "$(date '+%F %T') c2b done" >> logs/c2b.log
