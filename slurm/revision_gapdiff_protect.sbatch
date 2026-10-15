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
ROOT=/home/huangyue26/ScrapBench
cd /home/huangyue26/GAP-Diff
export PYTHONUNBUFFERED=1
IDS=$($ROOT/venv/bin/python $ROOT/scripts/make_identity_split.py \
  --data-root $ROOT/data/celeba_hq100 --out $ROOT/protocol/celeba_hq100_split.json --print-set test \
  --shard "$SLURM_ARRAY_TASK_ID" --num-shards 18)
IFS=',' read -ra ID_ARRAY <<< "$IDS"
for PID in "${ID_ARRAY[@]}"; do
  OUT=$ROOT/data/celeba_hq100/protected/gapdiff/$PID
  if [ "$(find "$OUT" -maxdepth 1 -type f 2>/dev/null | wc -l)" -ge 8 ]; then
    continue
  fi
  mkdir -p "$OUT"
  /home/huangyue26/.conda/envs/gap-diff/bin/python generate.py \
    --generator_path=/home/huangyue26/GAP-Diff/weights/model/G_per16_pretrain.pth \
    --source_path="$ROOT/data/celeba_hq100/raw/$PID" --save_path="$OUT" --noise_budget=16.0
done
