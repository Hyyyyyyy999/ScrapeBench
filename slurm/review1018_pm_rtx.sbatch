#!/bin/bash
#SBATCH -J sb1018_pm
#SBATCH -p rtx
#SBATCH --qos=emerg5
#SBATCH --gres=gpu:1
#SBATCH -c 4
#SBATCH --mem=24G
#SBATCH -t 12:00:00
#SBATCH --array=0-101%10
#SBATCH -o /mnt/beegfs/home/huangyue26/ScrapBench/slurm/review1018_pm_%A_%a.out
set -euo pipefail
cd /mnt/beegfs/home/huangyue26/ScrapBench
source venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONUNBUFFERED=1
METHODS=(clean gapdiff idprotector arcp_web_v4); TIERS=(t0 t1_jpeg70 t2_canvas_dpr1 t3_agent_facecrop t4_sr_x2 t5_i2i30 t6_sde35)
mapfile -t IDS < <(find data/web40/raw -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)
G=$((SLURM_ARRAY_TASK_ID + SLURM_ARRAY_TASK_ID / 10)); M=${METHODS[$((G / 28))]}; R=$((G % 28)); PID=${IDS[$((R / 7))]}; T=${TIERS[$((R % 7))]}
python scripts/run_photomaker_web40.py --method "$M" --pid "$PID" --tier "$T" --steps 30
