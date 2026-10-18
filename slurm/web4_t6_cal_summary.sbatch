#!/bin/bash
#SBATCH --job-name=sb4_t6_sum
#SBATCH --partition=cpu
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=slurm/web4_t6_cal_summary_%j.out

set -euo pipefail
cd /mnt/beegfs/home/huangyue26/ScrapBench
source venv/bin/activate
python scripts/summarize_web40.py --run web4_t6_calibration \
  --ids celeb00001,celeb00002,celeb00003,celeb00004 --methods clean
