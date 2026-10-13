#!/bin/bash
#SBATCH -J sb_t5_smoke
#SBATCH -p rtx
#SBATCH --gres=gpu:1
#SBATCH -c 8
#SBATCH --mem=32G
#SBATCH -t 01:00:00
#SBATCH -o /home/huangyue26/ScrapBench/slurm/t5_smoke_%j.out

cd /home/huangyue26/ScrapBench || exit 1
source /home/huangyue26/ScrapBench/venv/bin/activate
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_ENABLE_HF_TRANSFER=0
export HF_HUB_OFFLINE=1
export PYTHONUNBUFFERED=1

python3 -m scrapebench.runner.stage_a \
  --config configs/full.yaml \
  --methods clean \
  --ids celeb00025 \
  --tiers t5_i2i30 \
  --attack instantid
