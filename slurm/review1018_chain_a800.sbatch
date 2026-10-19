#!/bin/bash
#SBATCH -J sb1018_chainA
#SBATCH -p a800
#SBATCH --qos=a800-2
#SBATCH --gres=gpu:1
#SBATCH -c 4
#SBATCH --mem=48G
#SBATCH -t 08:00:00
#SBATCH -o /mnt/beegfs/home/huangyue26/ScrapBench/slurm/review1018_chain_%j.out
set -euo pipefail
cd /mnt/beegfs/home/huangyue26/ScrapBench
source venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONUNBUFFERED=1
METHODS=(clean gapdiff idprotector arcp_web_v4); ORDERS=(jpeg70_crop feed_crop cdn_feed_crop); ATTACKS=(instantid ipfaceid)
mapfile -t IDS < <(find data/web40/raw -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)
for ((G=10; G<96; G+=11)); do
  M=${METHODS[$((G / 24))]}; R=$((G % 24)); A=${ATTACKS[$((R / 12))]}; R=$((R % 12)); O=${ORDERS[$((R / 4))]}; PID=${IDS[$((R % 4))]}
  python -m scrapebench.runner.stage_order --config configs/web40_single_intervention.yaml --methods "$M" --ids "$PID" --orders "$O" --attack "$A"
done
