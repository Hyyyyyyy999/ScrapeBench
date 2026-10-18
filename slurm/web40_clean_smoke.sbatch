#!/bin/bash
#SBATCH -J sb40_smoke
#SBATCH -p rtx4090
#SBATCH --qos=emerg5
#SBATCH --gres=gpu:1
#SBATCH -c 4
#SBATCH --mem=20G
#SBATCH -t 08:00:00
#SBATCH -o /home/huangyue26/ScrapBench/slurm/web40_smoke_%j.out
set -euo pipefail
cd /home/huangyue26/ScrapBench
source venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONUNBUFFERED=1
IDS=celeb00008,celeb00009,celeb00011,celeb00023
python -m scrapebench.runner.stage_a --config configs/web40_single_intervention.yaml --methods clean --ids "$IDS" --tiers t0 --attack instantid --force
python -m scrapebench.runner.stage_a --config configs/web40_single_intervention.yaml --methods clean --ids "$IDS" --tiers t0 --attack ipfaceid --force
# This is a viability gate, not a result filter. Generated-face failures remain
# in FDFR/end-to-end ISM; the gate only prevents a completely broken reader.
python scripts/validate_clean_attack.py --results runs/web40_single_intervention/results.csv --ids "$IDS" --min-mean 0.25 --min-valid-fraction 0.75
