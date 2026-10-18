#!/bin/bash
#SBATCH -J sb40_idfix
#SBATCH -p rtx4090
#SBATCH --qos=emerg5
#SBATCH --gres=gpu:1
#SBATCH -c 2
#SBATCH --mem=12G
#SBATCH -t 08:00:00
#SBATCH --array=0-9%6
#SBATCH -o /home/huangyue26/ScrapBench/slurm/web40_idfix_%A_%a.out
set -euo pipefail
ROOT=/home/huangyue26/ScrapBench
SHARD=$SLURM_ARRAY_TASK_ID
IDS=$(/home/huangyue26/UMO/venv/UMO_UNO/bin/python -c "from pathlib import Path; x=[p.name for p in sorted(Path('$ROOT/data/web40/raw').iterdir()) if p.is_dir()]; print(','.join(x[$SHARD::10]))")
IFS=',' read -ra ID_ARRAY <<< "$IDS"
export PYTHONUNBUFFERED=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
cd /home/huangyue26/IDProtector
export PYTHONPATH="/home/huangyue26/IDProtector/pydeps:/home/huangyue26/IDProtector:${PYTHONPATH:-}"
for PID in "${ID_ARRAY[@]}"; do
  OUT="$ROOT/data/web40/protected/idprotector/$PID"
  /home/huangyue26/UMO/venv/UMO_UNO/bin/python scripts/protect_recursive.py \
    --input-root="$ROOT/data/web40/protected/clean/$PID" --output-root="$OUT" \
    --checkpoint=/home/huangyue26/IDProtector/protector_model.pt \
    --insightface-root=/home/huangyue26/IDProtector/generation_methods/InstantID \
    --epsilon=0.07 --det-thresholds 0.5 0.3 0.1 \
    --on-detection-failure full-frame --overwrite
done
