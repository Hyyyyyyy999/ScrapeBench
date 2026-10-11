#!/bin/bash
cd /root/scrapebench || exit 1
echo "$(date '+%F %T') fix: starting fsmgj protection" >> logs/fix.log
for i in 1 2 3; do
  CUDA_VISIBLE_DEVICES=0 python3 -m scrapebench.runner.protection_run --config configs/full.yaml --methods fsmgj --ids celeb00025,celeb00027,celeb00028,celeb00029,celeb00030,celeb00031 >> logs/fix.log 2>&1 && break
  echo "$(date '+%F %T') fix fsmgj retry $i" >> logs/fix.log; sleep 30
done
for i in 1 2 3; do
  CUDA_VISIBLE_DEVICES=0 python3 -m scrapebench.runner.stage_a --config configs/full.yaml --methods fsmgj >> logs/fix.log 2>&1 && break
  echo "$(date '+%F %T') fix stage_a retry $i" >> logs/fix.log; sleep 30
done
IDS=celeb00025,celeb00027,celeb00028,celeb00029,celeb00030,celeb00031
for i in 1 2 3; do
  CUDA_VISIBLE_DEVICES=0 python3 -m scrapebench.runner.stage_a --config configs/full.yaml --methods clean,fsmg,fsmgj --ids $IDS --tiers t0,t1_jpeg85,t2_canvas_dpr1,t5_i2i30 --attack instantid >> logs/fix.log 2>&1 && break
  echo "$(date '+%F %T') fix instantid retry $i" >> logs/fix.log; sleep 30
done
echo "$(date '+%F %T') fix done" >> logs/fix.log
