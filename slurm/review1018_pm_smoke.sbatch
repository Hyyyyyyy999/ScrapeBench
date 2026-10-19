#!/bin/bash
#SBATCH -J sb1018_pmsmoke
#SBATCH -p rtx
#SBATCH --qos=emerg5
#SBATCH --gres=gpu:1
#SBATCH -c 4
#SBATCH --mem=48G
#SBATCH -t 02:00:00
#SBATCH -o /mnt/beegfs/home/huangyue26/ScrapBench/slurm/review1018_pm_smoke_%j.out
set -euo pipefail
cd /mnt/beegfs/home/huangyue26/ScrapBench
source venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONUNBUFFERED=1
python scripts/run_photomaker_web40.py --method clean --pid celeb00001 --tier t0 --run-name review1018_pm_smoke --steps 2 --force
test -s runs/review1018_pm_smoke/generations/photomaker/clean/t0/celeb00001/samples.jsonl
