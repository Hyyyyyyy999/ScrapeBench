#!/bin/bash
#SBATCH -J sb1018_tex
#SBATCH -p cpu
#SBATCH -c 1
#SBATCH --mem=4G
#SBATCH -t 00:20:00
#SBATCH -o /mnt/beegfs/home/huangyue26/ScrapBench/slurm/review1018_paper_tables_%j.out
set -euo pipefail
cd /mnt/beegfs/home/huangyue26/ScrapBench
source venv/bin/activate
python scripts/write_review1018_paper_tables.py
