#!/bin/bash
cd /root/scrapebench || exit 1
echo "$(date '+%F %T') instant2: starting InstantID attack" >> logs/instant2.log
IDS=celeb00025,celeb00027,celeb00028,celeb00029,celeb00030,celeb00031
for i in 1 2 3; do
  CUDA_VISIBLE_DEVICES=0 python3 -m scrapebench.runner.stage_a --config configs/full.yaml --methods clean,fsmg,fsmgj --ids $IDS --tiers t0,t1_jpeg85,t2_canvas_dpr1,t5_i2i30 --attack instantid >> logs/instant2.log 2>&1 && break
  echo "$(date '+%F %T') instant2 retry $i" >> logs/instant2.log; sleep 60
done
echo "$(date '+%F %T') instant2 done" >> logs/instant2.log
