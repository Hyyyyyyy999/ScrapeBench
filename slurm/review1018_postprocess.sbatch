#!/bin/bash
#SBATCH -J sb1018_post
#SBATCH -p cpu
#SBATCH -c 2
#SBATCH --mem=8G
#SBATCH -t 01:00:00
#SBATCH -o /mnt/beegfs/home/huangyue26/ScrapBench/slurm/review1018_postprocess_%j.out
set -euo pipefail
cd /mnt/beegfs/home/huangyue26/ScrapBench
source venv/bin/activate
python scripts/audit_protection_quality.py
python scripts/write_review1018_paper_tables.py
python scripts/make_web40_qualitative.py
