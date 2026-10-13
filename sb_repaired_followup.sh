#!/bin/bash
#SBATCH -J sb_repaired
#SBATCH -p rtx
#SBATCH --gres=gpu:1
#SBATCH -c 8
#SBATCH --mem=32G
#SBATCH -t 1-12:00:00
#SBATCH -o /home/huangyue26/ScrapBench/slurm/repaired_%j.out

cd /home/huangyue26/ScrapBench || exit 1
source /home/huangyue26/ScrapBench/venv/bin/activate
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_ENABLE_HF_TRANSFER=0
export HF_HUB_OFFLINE=1
export PYTHONUNBUFFERED=1

IDS=celeb00025,celeb00027,celeb00028,celeb00029,celeb00030,celeb00031

echo "=== correct pre-protocol InstantID smoke cell at 30 steps ==="
python3 -m scrapebench.runner.stage_a \
  --config configs/full.yaml \
  --methods clean \
  --ids celeb00025 \
  --tiers t0 \
  --attack instantid \
  --force \
  >> logs/instant_correction.log 2>&1 || exit 1

echo "=== repaired T3 integrity pilot: 6 identities x 3 methods ==="
python3 -m scrapebench.runner.stage_a \
  --config configs/full.yaml \
  --methods clean,fsmg,fsmgj \
  --ids "$IDS" \
  --tiers t3_agent_facecrop \
  --attack ipfaceid \
  >> logs/t3_repaired.log 2>&1 || exit 1

echo "=== repaired Stage C: same-identity mixing + real purify50 ==="
python3 -m scrapebench.runner.stage_c \
  --config configs/full.yaml \
  --ids "$IDS" \
  >> logs/stage_c_repaired.log 2>&1 || exit 1

python3 -m scrapebench.runner.report --config configs/full.yaml
python3 scripts/analyze_new_results.py --require-complete
