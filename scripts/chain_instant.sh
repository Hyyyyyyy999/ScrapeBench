#!/bin/bash
cd /root/scrapebench || exit 1
while pgrep -f "chain_order2\.sh" > /dev/null; do sleep 120; done
echo "$(date '+%F %T') instant: starting InstantID attack" >> logs/instant.log
IDS=celeb00025,celeb00027,celeb00028,celeb00029,celeb00030,celeb00031
for i in 1 2 3; do
  CUDA_VISIBLE_DEVICES=0 python3 -m scrapebench.runner.stage_a --config configs/full.yaml --methods clean,fsmg,fsmgj --ids $IDS --tiers t0,t1_jpeg85,t2_canvas_dpr1,t5_i2i30 --attack instantid >> logs/instant.log 2>&1 && break
  echo "$(date '+%F %T') instant retry $i" >> logs/instant.log; sleep 60
done
echo "$(date '+%F %T') instant done" >> logs/instant.log
