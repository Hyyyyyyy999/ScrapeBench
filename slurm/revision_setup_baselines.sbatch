#!/bin/bash
#SBATCH -J sb_rev_base_setup
#SBATCH -p cpu
#SBATCH -c 8
#SBATCH --mem=32G
#SBATCH -t 1-00:00:00
#SBATCH -o /home/huangyue26/ScrapBench/slurm/revision_setup_baselines_%j.out
set -euo pipefail
cd /home/huangyue26/ScrapBench
bash scripts/setup_official_baselines.sh
