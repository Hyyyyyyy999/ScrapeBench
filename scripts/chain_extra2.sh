#!/bin/bash
cd /root/scrapebench || exit 1
IDS=celeb00025,celeb00027,celeb00028,celeb00029,celeb00030,celeb00031
while pgrep -f "chain_extra\.sh" > /dev/null; do sleep 120; done
echo "$(date '+%F %T') extra2: chain_extra done, starting InstantID" >> logs/extra2.log
for i in 1 2 3; do
  CUDA_VISIBLE_DEVICES=0 python3 -m scrapebench.runner.stage_a --config configs/full.yaml --methods clean,fsmg,fsmgj --ids $IDS --tiers t0,jpeg85,t2,t5 --attack instantid >> logs/full_instant.log 2>&1 && break
  echo "$(date '+%F %T') instant retry $i" >> logs/extra2.log; sleep 60
done
echo "$(date '+%F %T') extra2 done" >> logs/extra2.log
