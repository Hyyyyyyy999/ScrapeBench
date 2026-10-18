#!/bin/bash
#SBATCH --job-name=sb4_summary
#SBATCH --partition=cpu
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --output=slurm/web4_summary_%j.out

set -euo pipefail
cd /mnt/beegfs/home/huangyue26/ScrapBench
source venv/bin/activate
IDS=celeb00001,celeb00002,celeb00003,celeb00004
METHODS=clean,gapdiff,metacloak,goodac,arcp_web_v4
python scripts/audit_web4_protection.py --ids "$IDS" \
  --methods gapdiff,metacloak,goodac,arcp_web_v4
python scripts/summarize_web40.py --run web4_validation --ids "$IDS" --methods "$METHODS"
python scripts/make_web4_visuals.py --run web4_validation --pid celeb00001 --methods "$METHODS"
