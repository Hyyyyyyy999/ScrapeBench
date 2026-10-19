#!/bin/bash
#SBATCH -J sb1018_sum
#SBATCH -p cpu
#SBATCH -c 2
#SBATCH --mem=8G
#SBATCH -t 01:00:00
#SBATCH -o /mnt/beegfs/home/huangyue26/ScrapBench/slurm/review1018_summary_%j.out
set -euo pipefail
cd /mnt/beegfs/home/huangyue26/ScrapBench
source venv/bin/activate
python scripts/validate_review1018.py
python scripts/summarize_web40.py --run web40_single_intervention --methods clean,gapdiff,idprotector,gapdiff_8,idprotector_8,arcp_web_v4,arcp_web_v4_uniform,arcp_web_v4_no_texture,arcp_web_v4_no_coarse,arcp_web_v4_no_detail,arcp_web_v4_no_identity,arcp_web_v4_no_denoise
python scripts/compare_defense_gaps.py --run web40_single_intervention
python scripts/write_review1018_paper_tables.py
