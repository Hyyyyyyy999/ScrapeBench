#!/bin/bash
#SBATCH -J sb_rev_B
#SBATCH -p a800
#SBATCH --gres=gpu:1
#SBATCH -c 8
#SBATCH --mem=64G
#SBATCH -t 2-00:00:00
#SBATCH --array=0-17%8
#SBATCH -o /home/huangyue26/ScrapBench/slurm/revision_stage_b_%A_%a.out
set -euo pipefail
cd /home/huangyue26/ScrapBench
source venv/bin/activate
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_ENABLE_HF_TRANSFER=0
export HF_HUB_OFFLINE=1
export PYTHONUNBUFFERED=1
IDS=$(python scripts/make_identity_split.py --print-set test --shard "$SLURM_ARRAY_TASK_ID" --num-shards 18)
METHODS=${METHODS:-clean,arcp_v2}
python -m scrapebench.runner.stage_b --config configs/revision_single_tier.yaml \
  --methods "$METHODS" --ids "$IDS" --tiers t1_jpeg70
python scripts/summarize_gapdiff.py --run revision_single_tier
