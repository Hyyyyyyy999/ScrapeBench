#!/bin/bash
#SBATCH -J sb_stage_o
#SBATCH -p rtx
#SBATCH --gres=gpu:1
#SBATCH -c 8
#SBATCH --mem=32G
#SBATCH -t 12:00:00
#SBATCH -o /home/huangyue26/ScrapBench/slurm/stage_o_%j.out

set -euo pipefail
cd /home/huangyue26/ScrapBench
source venv/bin/activate
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_ENABLE_HF_TRANSFER=0
export HF_HUB_OFFLINE=1
export PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=8

IDS=celeb00025,celeb00027,celeb00028,celeb00029,celeb00030,celeb00031

echo "=== complete random galleries ==="
python3 -m scrapebench.runner.protection_run \
  --config configs/full.yaml --methods random --ids "$IDS" \
  >> logs/stage_o_complete.log 2>&1

echo "=== matched T0 baselines for Stage O ==="
python3 -m scrapebench.runner.stage_a \
  --config configs/full.yaml --methods clean,random,fsmg --ids "$IDS" \
  --tiers t0 --attack ipfaceid \
  >> logs/stage_o_complete.log 2>&1

echo "=== full Stage O: 6 identities x 3 methods x 6 programs ==="
python3 -m scrapebench.runner.stage_order \
  --config configs/full.yaml --methods clean,random,fsmg --ids "$IDS" \
  >> logs/stage_o_complete.log 2>&1

python3 -m scrapebench.runner.report --config configs/full.yaml
python3 scripts/analyze_new_results.py --require-complete
