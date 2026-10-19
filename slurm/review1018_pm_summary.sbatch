#!/bin/bash
#SBATCH -J sb1018_pmsum
#SBATCH -p cpu
#SBATCH -c 1
#SBATCH --mem=4G
#SBATCH -t 00:30:00
#SBATCH -o /mnt/beegfs/home/huangyue26/ScrapBench/slurm/review1018_pm_summary_%j.out
set -euo pipefail
cd /mnt/beegfs/home/huangyue26/ScrapBench
source venv/bin/activate
python scripts/validate_review1018_photomaker.py
