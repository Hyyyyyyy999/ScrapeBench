#!/bin/bash
#SBATCH --job-name=sb_off_smoke
#SBATCH --partition=a800
#SBATCH --qos=a800-2
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=6
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=slurm/web40_official_smoke_%A.out

set -euo pipefail
: "${METHOD:?submit with METHOD=goodac or metacloak}"
cd /mnt/beegfs/home/huangyue26/ScrapBench
source venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONUNBUFFERED=1
python scripts/run_official_web40_protector.py --method "$METHOD" --pid celeb00001 --smoke
