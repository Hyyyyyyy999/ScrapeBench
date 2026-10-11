#!/bin/bash
cd /root/scrapebench || exit 1
while pgrep -f "queue1b\.sh" > /dev/null; do sleep 120; done
while pgrep -f "runner.stage_c" > /dev/null; do sleep 120; done
echo "$(date '+%F %T') order2: starting stage_order completion" >> logs/order2.log
for i in 1 2 3; do
  CUDA_VISIBLE_DEVICES=1 python3 -m scrapebench.runner.stage_order --config configs/full.yaml >> logs/order2.log 2>&1 && break
  echo "$(date '+%F %T') order2 retry $i" >> logs/order2.log; sleep 60
done
echo "$(date '+%F %T') order2 done" >> logs/order2.log
