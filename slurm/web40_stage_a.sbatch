#!/bin/bash
#SBATCH -J sb40_stageA
#SBATCH -p rtx
#SBATCH --qos=emerg5
#SBATCH --gres=gpu:1
#SBATCH -c 2
#SBATCH --mem=16G
#SBATCH -t 2-00:00:00
#SBATCH --array=0-79%6
#SBATCH -o /home/huangyue26/ScrapBench/slurm/web40_stage_a_%A_%a.out
set -euo pipefail
cd /home/huangyue26/ScrapBench
source venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONUNBUFFERED=1
GROUP=$((SLURM_ARRAY_TASK_ID % 8))
SHARD=$((SLURM_ARRAY_TASK_ID / 8))
case "$GROUP" in
  0) ATTACK=instantid; METHOD=clean ;;
  1) ATTACK=instantid; METHOD=gapdiff ;;
  2) ATTACK=instantid; METHOD=idprotector ;;
  3) ATTACK=instantid; METHOD=arcp_web ;;
  4) ATTACK=ipfaceid; METHOD=clean ;;
  5) ATTACK=ipfaceid; METHOD=gapdiff ;;
  6) ATTACK=ipfaceid; METHOD=idprotector ;;
  7) ATTACK=ipfaceid; METHOD=arcp_web ;;
esac
IDS=$(python -c "from pathlib import Path; x=[p.name for p in sorted(Path('data/web40/raw').iterdir()) if p.is_dir()]; print(','.join(x[$SHARD::10]))")
python -m scrapebench.runner.stage_a --config configs/web40_single_intervention.yaml \
  --methods "$METHOD" --ids "$IDS" \
  --tiers t0,t1_jpeg70,t2_canvas_dpr1,t3_agent_facecrop,t4_sr_x2,t5_i2i30,t6_sde50 \
  --attack "$ATTACK" --force
