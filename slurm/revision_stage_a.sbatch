#!/bin/bash
#SBATCH -J sb_rev_A
#SBATCH -p rtx4090
#SBATCH --qos=emerg5
#SBATCH --gres=gpu:1
#SBATCH -c 1
#SBATCH --mem=10G
#SBATCH -t 2-00:00:00
#SBATCH --array=0-17%1
#SBATCH -o /home/huangyue26/ScrapBench/slurm/revision_stage_a_%A_%a.out
set -euo pipefail
cd /home/huangyue26/ScrapBench
source venv/bin/activate
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_ENABLE_HF_TRANSFER=0
export HF_HUB_OFFLINE=1
export PYTHONUNBUFFERED=1
IDS=$(python scripts/make_identity_split.py --data-root data/celeba_hq100 \
  --out protocol/celeba_hq100_split.json --print-set test \
  --shard "$SLURM_ARRAY_TASK_ID" --num-shards 18)
ATTACK=${ATTACK:-ipfaceid}
METHODS=${METHODS:-clean,arcp_v2}
python -m scrapebench.runner.stage_a --config configs/revision_single_tier.yaml \
  --methods "$METHODS" --ids "$IDS" \
  --tiers t0,t1_jpeg70,t2_canvas_dpr1,t3_agent_facecrop,t4_sr_x2,t5_i2i30,t6_diffpure50 \
  --attack "$ATTACK"
