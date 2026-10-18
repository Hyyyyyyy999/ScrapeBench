#!/bin/bash
#SBATCH --job-name=sb_off_full
#SBATCH --partition=a800
#SBATCH --qos=a800-2
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=6
#SBATCH --mem=64G
#SBATCH --time=2-00:00:00
#SBATCH --array=0-39%2
#SBATCH --output=slurm/web40_official_full_%A_%a.out

set -euo pipefail
: "${METHOD:?submit with METHOD=goodac or metacloak}"
cd /mnt/beegfs/home/huangyue26/ScrapBench
source venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONUNBUFFERED=1
mapfile -t IDS < <(find data/web40/raw -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)
python scripts/run_official_web40_protector.py --method "$METHOD" --pid "${IDS[$SLURM_ARRAY_TASK_ID]}"
