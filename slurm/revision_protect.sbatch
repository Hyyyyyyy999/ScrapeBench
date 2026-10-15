#!/bin/bash
#SBATCH -J sb_rev_prot
#SBATCH -p rtx4090
#SBATCH --gres=gpu:1
#SBATCH -c 1
#SBATCH --mem=8G
#SBATCH -t 2-00:00:00
#SBATCH --array=0-9%2
#SBATCH -o /home/huangyue26/ScrapBench/slurm/revision_protect_%A_%a.out
set -euo pipefail
cd /home/huangyue26/ScrapBench
source venv/bin/activate
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_ENABLE_HF_TRANSFER=0
export HF_HUB_OFFLINE=1
export PYTHONUNBUFFERED=1
IDS=$(python scripts/make_identity_split.py --data-root data/celeba_hq100 \
  --out protocol/celeba_hq100_split.json --print-set test \
  --shard "$SLURM_ARRAY_TASK_ID" --num-shards 10)
python -m scrapebench.runner.protection_run --config configs/revision_single_tier.yaml --methods clean,arcp_v2 --ids "$IDS"
