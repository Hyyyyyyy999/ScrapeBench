#!/bin/bash
#SBATCH -J sb40_gapfix
#SBATCH -p rtx4090
#SBATCH --qos=emerg5
#SBATCH --gres=gpu:1
#SBATCH -c 2
#SBATCH --mem=12G
#SBATCH -t 08:00:00
#SBATCH --array=0-9%6
#SBATCH -o /home/huangyue26/ScrapBench/slurm/web40_gapfix_%A_%a.out
set -euo pipefail
ROOT=/home/huangyue26/ScrapBench
REPO=/home/huangyue26/GAP-Diff
SHARD=$SLURM_ARRAY_TASK_ID
IDS=$(/home/huangyue26/.conda/envs/gap-diff/bin/python -c "from pathlib import Path; x=[p.name for p in sorted(Path('$ROOT/data/web40/raw').iterdir()) if p.is_dir()]; print(','.join(x[$SHARD::10]))")
IFS=',' read -ra ID_ARRAY <<< "$IDS"
export PYTHONUNBUFFERED=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
cd "$ROOT"
for PID in "${ID_ARRAY[@]}"; do
  OUT="$ROOT/data/web40/protected/gapdiff/$PID"
  [ "$(find "$OUT" -maxdepth 1 -type f -name '*.png' 2>/dev/null | wc -l)" -ge 4 ] && continue
  mkdir -p "$OUT"
  /home/huangyue26/.conda/envs/gap-diff/bin/python scripts/run_gapdiff_generate.py \
    --repo "$REPO" \
    --generator-path "$REPO/weights/model/G_per16_pretrain.pth" \
    --source-path "$ROOT/data/web40/protected/clean/$PID" \
    --save-path "$OUT" \
    --noise-budget 16.0
done
