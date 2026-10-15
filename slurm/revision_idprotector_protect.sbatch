#!/bin/bash
#SBATCH -J sb_idprotector
#SBATCH -p a800
#SBATCH --gres=gpu:1
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 1-00:00:00
#SBATCH --array=0-17%6
#SBATCH -o /home/huangyue26/ScrapBench/slurm/revision_idprotector_%A_%a.out
set -euo pipefail
cd /home/huangyue26/ScrapBench/external/IDProtector
export PYTHONUNBUFFERED=1
ROOT=/home/huangyue26/ScrapBench
IDS=$($ROOT/venv/bin/python $ROOT/scripts/make_identity_split.py \
  --data-root "$ROOT/data/celeba_hq100" --out "$ROOT/protocol/celeba_hq100_split.json" \
  --print-set test --shard "$SLURM_ARRAY_TASK_ID" --num-shards 18)
IFS=',' read -ra ID_ARRAY <<< "$IDS"
for PID in "${ID_ARRAY[@]}"; do
  OUT=$ROOT/data/celeba_hq100/protected/idprotector/$PID
  if [ "$(find "$OUT" -maxdepth 1 -type f 2>/dev/null | wc -l)" -ge 8 ]; then
    continue
  fi
  mkdir -p "$OUT"
  /mnt/beegfs/home/huangyue26/ScrapBench/external/idprotector_env/bin/python \
    -m scripts.evaluation.perturb_get_metric \
    --in_channels 5 --epsilon 0.125490196 --clip_epsilon 1 \
    --clean_data_dir "$ROOT/data/celeba_hq100/raw/$PID" --save_dir "$OUT" \
    --path_to_state_dict protector_model.pt --metrics_save_path "$OUT/metrics.csv" \
    --batch_size 1 --cuda 0
done
