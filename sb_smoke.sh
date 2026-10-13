#!/bin/bash
#SBATCH -J sb_smoke
#SBATCH -p rtx
#SBATCH --gres=gpu:1
#SBATCH -c 8
#SBATCH --mem=32G
#SBATCH -t 01:00:00
#SBATCH -o /home/huangyue26/ScrapBench/slurm/smoke_%j.out

cd ~/ScrapBench
source ~/ScrapBench/venv/bin/activate
export HF_ENDPOINT=https://hf-mirror.com HF_HUB_ENABLE_HF_TRANSFER=0 PYTHONUNBUFFERED=1 HF_HUB_OFFLINE=1
echo "=== node $(hostname), gpu info ==="
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv

python3 -m scrapebench.runner.protection_run --config configs/full.yaml --methods clean --ids celeb00025
python3 -m scrapebench.runner.stage_a --config configs/full.yaml --methods clean --ids celeb00025 --tiers t0 --attack instantid
