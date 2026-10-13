#!/bin/bash
#SBATCH -J sb_iid_fix
#SBATCH -p rtx
#SBATCH --gres=gpu:1
#SBATCH -c 8
#SBATCH --mem=32G
#SBATCH -t 02:00:00
#SBATCH -o /home/huangyue26/ScrapBench/slurm/iid_fix_%j.out

set -euo pipefail
cd /home/huangyue26/ScrapBench
source venv/bin/activate
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_ENABLE_HF_TRANSFER=0
export HF_HUB_OFFLINE=1
export PYTHONUNBUFFERED=1

python3 -m scrapebench.runner.stage_a \
  --config configs/full.yaml \
  --methods clean \
  --ids celeb00025 \
  --tiers t0 \
  --attack instantid \
  --force \
  >> logs/instant_correction.log 2>&1

python3 -m scrapebench.runner.report --config configs/full.yaml
python3 scripts/analyze_new_results.py --require-complete
