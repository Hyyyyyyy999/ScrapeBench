#!/bin/bash
cd /root/scrapebench || exit 1
while pgrep -f "queue1b\.sh" > /dev/null; do sleep 120; done
echo "$(date '+%F %T') c2: queue1b done, finishing stage_c" >> logs/c2.log
for i in 1 2 3; do
  CUDA_VISIBLE_DEVICES=1 python3 -m scrapebench.runner.stage_c --config configs/full.yaml >> logs/full_c2.log 2>&1 && break
  echo "$(date '+%F %T') c2 retry $i" >> logs/c2.log; sleep 60
done
echo "$(date '+%F %T') c2 done" >> logs/c2.log
