#!/bin/bash
#SBATCH --job-name=sb4_meta_eval
#SBATCH --partition=rtx4090
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=08:00:00
#SBATCH --array=0-1%2
#SBATCH --output=slurm/web4_meta_eval_%A_%a.out

set -euo pipefail
cd /mnt/beegfs/home/huangyue26/ScrapBench
source venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONUNBUFFERED=1
if (( SLURM_ARRAY_TASK_ID == 0 )); then ATTACK=instantid; else ATTACK=ipfaceid; fi
python -m scrapebench.runner.stage_a \
  --config configs/web40_single_intervention.yaml --run-name web4_validation \
  --methods metacloak --ids celeb00001,celeb00002,celeb00003,celeb00004 --attack "$ATTACK" \
  --tiers t0,t1_jpeg70,t2_canvas_dpr1,t3_agent_facecrop,t4_sr_x2,t5_i2i30,t6_sde50 --force
