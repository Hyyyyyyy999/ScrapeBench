#!/bin/bash
#SBATCH -J sb1018_httpA
#SBATCH -p rtx
#SBATCH --qos=emerg5
#SBATCH --gres=gpu:1
#SBATCH -c 2
#SBATCH --mem=20G
#SBATCH -t 04:00:00
#SBATCH --array=0-29%10
#SBATCH -o /mnt/beegfs/home/huangyue26/ScrapBench/slurm/review1018_http_%A_%a.out
set -euo pipefail
cd /mnt/beegfs/home/huangyue26/ScrapBench
source venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONUNBUFFERED=1
METHODS=(clean_http_roundtrip gapdiff_http_roundtrip idprotector_http_roundtrip arcp_web_v4_http_roundtrip); ATTACKS=(instantid ipfaceid)
mapfile -t IDS < <(find data/web40/raw -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)
G=$((SLURM_ARRAY_TASK_ID + SLURM_ARRAY_TASK_ID / 10)); M=${METHODS[$((G / 8))]}; R=$((G % 8)); A=${ATTACKS[$((R / 4))]}; PID=${IDS[$((R % 4))]}
python -m scrapebench.runner.stage_a --config configs/web40_single_intervention.yaml --run-name web4_http_roundtrip --methods "$M" --ids "$PID" --tiers t0 --attack "$A"
