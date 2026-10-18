#!/bin/bash
#SBATCH --job-name=sb_arcpv4_p
#SBATCH --partition=rtx4090
#SBATCH --qos=emerg5
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=05:00:00
#SBATCH --array=0-3%4
#SBATCH --output=slurm/web40_arcp_v4_protect_%A_%a.out

set -euo pipefail
cd /mnt/beegfs/home/huangyue26/ScrapBench
source venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONUNBUFFERED=1
export SCRAPEBENCH_ARCFACE_ONNX=/mnt/beegfs/home/huangyue26/IDProtector/generation_methods/InstantID/models/antelopev2/glintr100.onnx
export SCRAPEBENCH_ANTELOPE_ROOT=/mnt/beegfs/home/huangyue26/IDProtector/generation_methods/InstantID
mapfile -t IDS < <(find data/web40/raw -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)
python -m scrapebench.runner.protection_run \
  --config configs/web40_single_intervention.yaml \
  --methods arcp_web_v4 --ids "${IDS[$SLURM_ARRAY_TASK_ID]}"
