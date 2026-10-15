#!/bin/bash
#SBATCH -J sb_idprotector
#SBATCH -p rtx4090
#SBATCH --gres=gpu:1
#SBATCH -c 1
#SBATCH --mem=8G
#SBATCH -t 1-00:00:00
#SBATCH --array=0-17%2
#SBATCH -o /home/huangyue26/ScrapBench/slurm/revision_idprotector_%A_%a.out
set -euo pipefail
cd /home/huangyue26/IDProtector
export PYTHONUNBUFFERED=1
ROOT=/home/huangyue26/ScrapBench
IDS=$($ROOT/venv/bin/python $ROOT/scripts/make_identity_split.py \
  --data-root "$ROOT/data/celeba_hq100" --out "$ROOT/protocol/celeba_hq100_split.json" \
  --print-set test --shard "$SLURM_ARRAY_TASK_ID" --num-shards 18)
IFS=',' read -ra ID_ARRAY <<< "$IDS"
for PID in "${ID_ARRAY[@]}"; do
  OUT=$ROOT/data/celeba_hq100/protected/idprotector/$PID
  if [ "$(find "$OUT" -maxdepth 1 -type f -name '*.png' 2>/dev/null | wc -l)" -ge 8 ]; then
    continue
  fi
  mkdir -p "$OUT"
  /home/huangyue26/UMO/venv/UMO_UNO/bin/python \
    scripts/protect_recursive.py \
    --input-root "$ROOT/data/celeba_hq100/raw/$PID" \
    --output-root "$OUT" \
    --checkpoint /home/huangyue26/IDProtector/protector_model.pt \
    --insightface-root /home/huangyue26/IDProtector/generation_methods/InstantID \
    --epsilon 0.07 --det-thresholds 0.5 --on-detection-failure error
done
