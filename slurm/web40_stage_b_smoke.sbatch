#!/bin/bash
#SBATCH --job-name=sb_db_smoke
#SBATCH --partition=rtx4090
#SBATCH --qos=emerg5
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=6
#SBATCH --mem=48G
#SBATCH --time=02:00:00
#SBATCH --output=slurm/web40_stage_b_smoke_%j.out

set -euo pipefail
cd /mnt/beegfs/home/huangyue26/ScrapBench
source venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONUNBUFFERED=1
python -m scrapebench.runner.stage_b \
  --config configs/web40_single_intervention.yaml \
  --methods clean --ids celeb00001 --tiers t0 --steps 2 \
  --samples-per-prompt 1 --force
