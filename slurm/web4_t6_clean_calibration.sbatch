#!/bin/bash
#SBATCH --job-name=sb4_t6_cal
#SBATCH --partition=rtx4090
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --array=0-7%6
#SBATCH --output=slurm/web4_t6_cal_%A_%a.out

set -euo pipefail
cd /mnt/beegfs/home/huangyue26/ScrapBench
source venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONUNBUFFERED=1
TIERS=(t0 t6_sde30 t6_sde35 t6_sde40)
TIER=${TIERS[$((SLURM_ARRAY_TASK_ID / 2))]}
if (( SLURM_ARRAY_TASK_ID % 2 == 0 )); then ATTACK=instantid; else ATTACK=ipfaceid; fi
python -m scrapebench.runner.stage_a \
  --config configs/web40_single_intervention.yaml --run-name web4_t6_calibration \
  --methods clean --ids celeb00001,celeb00002,celeb00003,celeb00004 \
  --attack "$ATTACK" --tiers "$TIER" --force
