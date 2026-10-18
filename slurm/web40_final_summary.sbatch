#!/bin/bash
#SBATCH --job-name=sb40_summary
#SBATCH --partition=cpu
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --output=slurm/web40_final_summary_%j.out

set -euo pipefail
cd /mnt/beegfs/home/huangyue26/ScrapBench
source venv/bin/activate
python scripts/summarize_web40.py --run web40_single_intervention \
  --methods clean,gapdiff,metacloak,goodac,arcp_web_v4
