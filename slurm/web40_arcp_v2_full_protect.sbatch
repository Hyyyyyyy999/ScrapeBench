#!/bin/bash
#SBATCH --job-name=sb_arcpv2_fullp
#SBATCH --partition=rtx4090
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=06:00:00
#SBATCH --array=4-39%4
#SBATCH --output=slurm/web40_arcp_v2_full_protect_%A_%a.out

set -euo pipefail
cd /mnt/beegfs/home/huangyue26/ScrapBench
source venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONUNBUFFERED=1

mapfile -t IDS < <(find data/web40/raw -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)
PID="${IDS[$SLURM_ARRAY_TASK_ID]}"
python -m scrapebench.runner.protection_run \
  --config configs/web40_single_intervention.yaml \
  --methods arcp_web_v2 --ids "$PID"
