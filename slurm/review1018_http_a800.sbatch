#!/bin/bash
#SBATCH -J sb1018_httpAA
#SBATCH -p a800
#SBATCH --qos=a800-2
#SBATCH --gres=gpu:1
#SBATCH -c 4
#SBATCH --mem=48G
#SBATCH -t 04:00:00
#SBATCH -o /mnt/beegfs/home/huangyue26/ScrapBench/slurm/review1018_http_%j.out
set -euo pipefail
cd /mnt/beegfs/home/huangyue26/ScrapBench
source venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONUNBUFFERED=1
METHODS=(clean_http_roundtrip gapdiff_http_roundtrip idprotector_http_roundtrip arcp_web_v4_http_roundtrip); ATTACKS=(instantid ipfaceid)
mapfile -t IDS < <(find data/web40/raw -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)
for ((G=10; G<32; G+=11)); do M=${METHODS[$((G / 8))]}; R=$((G % 8)); A=${ATTACKS[$((R / 4))]}; PID=${IDS[$((R % 4))]}; python -m scrapebench.runner.stage_a --config configs/web40_single_intervention.yaml --run-name web4_http_roundtrip --methods "$M" --ids "$PID" --tiers t0 --attack "$A"; done
