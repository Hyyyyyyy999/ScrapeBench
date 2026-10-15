#!/bin/bash
#SBATCH -J sb_gapdiff
#SBATCH -p a800
#SBATCH --gres=gpu:1
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 1-00:00:00
#SBATCH --array=0-17%6
#SBATCH -o /home/huangyue26/ScrapBench/slurm/revision_gapdiff_%A_%a.out
set -euo pipefail
cd /home/huangyue26/ScrapBench
export PYTHONUNBUFFERED=1
IDS=$(venv/bin/python scripts/make_identity_split.py --print-set test --shard "$SLURM_ARRAY_TASK_ID" --num-shards 18)
IFS=',' read -ra ID_ARRAY <<< "$IDS"
for PID in "${ID_ARRAY[@]}"; do
  OUT=/home/huangyue26/ScrapBench/data/protected/gapdiff/$PID
  if [ "$(find "$OUT" -maxdepth 1 -type f 2>/dev/null | wc -l)" -ge 8 ]; then
    continue
  fi
  mkdir -p "$OUT"
  external/gapdiff_env/bin/python external/GAP-Diff/generate.py \
    --generator_path=external/GAP-Diff/weights/model/G_per16_pretrain.pth \
    --source_path="data/raw/$PID" --save_path="$OUT" --noise_budget=16.0
done
