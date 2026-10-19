#!/bin/bash
#SBATCH -J sb1018_dbsmoke
#SBATCH -p rtx
#SBATCH --qos=emerg5
#SBATCH --gres=gpu:1
#SBATCH -c 4
#SBATCH --mem=48G
#SBATCH -t 02:00:00
#SBATCH -o /mnt/beegfs/home/huangyue26/ScrapBench/slurm/review1018_db_smoke_%j.out
set -euo pipefail
cd /mnt/beegfs/home/huangyue26/ScrapBench
source venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONUNBUFFERED=1
python -m scrapebench.runner.stage_b --config configs/web40_single_intervention.yaml \
  --run-name review1018_db_smoke --methods clean --ids celeb00001 --tiers t0 \
  --steps 2 --samples-per-prompt 1 --force
test -s runs/review1018_db_smoke/generations/dreambooth/clean/t0/celeb00001/samples.jsonl
