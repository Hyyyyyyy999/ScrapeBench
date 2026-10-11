#!/bin/bash
cd /root/scrapebench || exit 1
L=logs/extra0.log
echo "$(date '+%F %T') extra0: stage_order start" >> $L
for i in 1 2 3 4 5; do
  CUDA_VISIBLE_DEVICES=0 python3 -m scrapebench.runner.stage_order --config configs/full.yaml >> $L 2>&1 && break
  echo "$(date '+%F %T') extra0 stage_order retry $i" >> $L
  sleep 60
done
echo "$(date '+%F %T') extra0: fsmgj protection start" >> $L
for i in 1 2 3; do
  CUDA_VISIBLE_DEVICES=0 python3 -m scrapebench.runner.protection_run --config configs/full.yaml --methods fsmgj --ids celeb00025,celeb00027,celeb00028,celeb00029,celeb00030,celeb00031 >> $L 2>&1 && break
  echo "$(date '+%F %T') extra0 fsmgj retry $i" >> $L
  sleep 60
done
for i in 1 2 3 4 5 6; do
  CUDA_VISIBLE_DEVICES=0 python3 -m scrapebench.runner.stage_a --config configs/full.yaml --methods fsmgj >> $L 2>&1 && break
  echo "$(date '+%F %T') extra0 stage_a retry $i" >> $L
  sleep 60
done
echo "$(date '+%F %T') extra0 done" >> $L
