#!/bin/bash
#SBATCH --job-name=sb4_meta_tail
#SBATCH --partition=rtx
#SBATCH --nodelist=aias-compute-01
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --array=0-3%4
#SBATCH --output=slurm/web4_meta_tail_%A_%a.out

set -euo pipefail
cd /mnt/beegfs/home/huangyue26/ScrapBench
source venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONUNBUFFERED=1
IDS=(celeb00003 celeb00004 celeb00003 celeb00004)
if (( SLURM_ARRAY_TASK_ID < 2 )); then ATTACK=instantid; else ATTACK=ipfaceid; fi
python -m scrapebench.runner.stage_a \
  --config configs/web40_single_intervention.yaml --run-name web4_validation \
  --methods metacloak --ids "${IDS[$SLURM_ARRAY_TASK_ID]}" --attack "$ATTACK" \
  --tiers t0,t1_jpeg70,t2_canvas_dpr1,t3_agent_facecrop,t4_sr_x2,t5_i2i30,t6_sde50 --force
