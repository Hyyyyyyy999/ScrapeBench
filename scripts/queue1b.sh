#!/bin/bash
cd /root/scrapebench || exit 1
IDS1=celeb00025,celeb00027,celeb00028,celeb00029,celeb00030,celeb00031,celeb00032,celeb00033,celeb00034,celeb00035,celeb00036,celeb00038,celeb00039,celeb00040,celeb00041,celeb00042,celeb00043,celeb00045,celeb00046,celeb00047
while pgrep -f "runner.stage_c" > /dev/null; do sleep 180; done
echo "$(date '+%F %T') queue1b: stage_c done, running clean/random protections for IDS1" >> logs/chain1.log
for i in 1 2 3 4 5; do
  CUDA_VISIBLE_DEVICES=1 python3 -m scrapebench.runner.protection_run --config configs/full.yaml --methods clean,random --ids $IDS1 >> logs/full_prot1.log 2>&1 && break
  sleep 60
done
for i in 1 2 3 4 5 6 7 8; do
  CUDA_VISIBLE_DEVICES=1 python3 -m scrapebench.runner.stage_a --config configs/full.yaml --methods clean,random --ids $IDS1 >> logs/full_a1.log 2>&1 && break
  echo "$(date '+%F %T') queue1b stage_a retry $i" >> logs/chain1.log
  sleep 60
done
echo "$(date '+%F %T') queue1b done" >> logs/chain1.log
