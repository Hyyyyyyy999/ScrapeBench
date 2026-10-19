#!/bin/bash
#SBATCH -J sb1018_protA
#SBATCH -p a800
#SBATCH --qos=a800-2
#SBATCH --gres=gpu:1
#SBATCH -c 4
#SBATCH --mem=64G
#SBATCH -t 08:00:00
#SBATCH -o /mnt/beegfs/home/huangyue26/ScrapBench/slurm/review1018_protect_%j.out
set -euo pipefail
cd /mnt/beegfs/home/huangyue26/ScrapBench
source venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONUNBUFFERED=1
export SCRAPEBENCH_ARCFACE_ONNX=/mnt/beegfs/home/huangyue26/IDProtector/generation_methods/InstantID/models/antelopev2/glintr100.onnx
export SCRAPEBENCH_ANTELOPE_ROOT=/mnt/beegfs/home/huangyue26/IDProtector/generation_methods/InstantID
mapfile -t IDS < <(find data/web40/raw -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)
ABL=(arcp_web_v4_uniform arcp_web_v4_no_texture arcp_web_v4_no_coarse arcp_web_v4_no_detail arcp_web_v4_no_identity arcp_web_v4_no_denoise)
for G in 10 21 32 43 54; do
  if (( G < 36 )); then METHOD=arcp_web_v4; PID=${IDS[$((G + 4))]};
  else X=$((G - 36)); METHOD=${ABL[$((X / 4))]}; PID=${IDS[$((X % 4))]}; fi
  python -m scrapebench.runner.protection_run --config configs/web40_single_intervention.yaml --methods "$METHOD" --ids "$PID"
done
