#!/bin/bash
#SBATCH -J sb1018_seed
#SBATCH -p rtx
#SBATCH --qos=emerg5
#SBATCH --gres=gpu:1
#SBATCH -c 2
#SBATCH --mem=20G
#SBATCH -t 10:00:00
#SBATCH --array=0-232%10
#SBATCH -o /mnt/beegfs/home/huangyue26/ScrapBench/slurm/review1018_seed_%A_%a.out
set -euo pipefail
cd /mnt/beegfs/home/huangyue26/ScrapBench
source venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONUNBUFFERED=1
SEEDS=(20261019 20261020); METHODS=(clean gapdiff idprotector arcp_web_v4); ATTACKS=(instantid ipfaceid); TIERS=(t0 t1_jpeg70 t3_agent_facecrop t5_i2i30)
mapfile -t IDS < <(find data/web40/raw -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)
G=$((SLURM_ARRAY_TASK_ID + SLURM_ARRAY_TASK_ID / 10))
SEED=${SEEDS[$((G / 128))]}; R=$((G % 128)); M=${METHODS[$((R / 32))]}; R=$((R % 32)); A=${ATTACKS[$((R / 16))]}; R=$((R % 16)); T=${TIERS[$((R / 4))]}; PID=${IDS[$((R % 4))]}
python -m scrapebench.runner.stage_a --config configs/web40_single_intervention.yaml --run-name "web4_seed_${SEED}" --seed "$SEED" --methods "$M" --ids "$PID" --tiers "$T" --attack "$A"
