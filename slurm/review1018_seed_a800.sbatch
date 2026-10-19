#!/bin/bash
#SBATCH -J sb1018_seedA
#SBATCH -p a800
#SBATCH --qos=a800-2
#SBATCH --gres=gpu:1
#SBATCH -c 4
#SBATCH --mem=48G
#SBATCH -t 10:00:00
#SBATCH -o /mnt/beegfs/home/huangyue26/ScrapBench/slurm/review1018_seed_%j.out
set -euo pipefail
cd /mnt/beegfs/home/huangyue26/ScrapBench
source venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONUNBUFFERED=1
SEEDS=(20261019 20261020); METHODS=(clean gapdiff idprotector arcp_web_v4); ATTACKS=(instantid ipfaceid); TIERS=(t0 t1_jpeg70 t3_agent_facecrop t5_i2i30)
mapfile -t IDS < <(find data/web40/raw -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)
for ((G=10; G<256; G+=11)); do
  SEED=${SEEDS[$((G / 128))]}; R=$((G % 128)); M=${METHODS[$((R / 32))]}; R=$((R % 32)); A=${ATTACKS[$((R / 16))]}; R=$((R % 16)); T=${TIERS[$((R / 4))]}; PID=${IDS[$((R % 4))]}
  python -m scrapebench.runner.stage_a --config configs/web40_single_intervention.yaml --run-name "web4_seed_${SEED}" --seed "$SEED" --methods "$M" --ids "$PID" --tiers "$T" --attack "$A"
done
