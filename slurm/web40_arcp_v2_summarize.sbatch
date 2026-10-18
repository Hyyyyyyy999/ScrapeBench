#!/bin/bash
#SBATCH --job-name=sb_arcpv2_sum
#SBATCH --partition=cpu
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=slurm/web40_arcp_v2_summarize_%j.out

set -euo pipefail
cd /mnt/beegfs/home/huangyue26/ScrapBench
source venv/bin/activate
python scripts/summarize_web40_v2.py
