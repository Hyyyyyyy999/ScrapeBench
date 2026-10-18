#!/bin/bash
#SBATCH -J sb40_protect
#SBATCH -p rtx4090
#SBATCH --qos=emerg5
#SBATCH --gres=gpu:1
#SBATCH -c 2
#SBATCH --mem=12G
#SBATCH -t 2-00:00:00
#SBATCH --array=0-29%6
#SBATCH -o /home/huangyue26/ScrapBench/slurm/web40_protect_%A_%a.out
set -euo pipefail
ROOT=/home/huangyue26/ScrapBench
GROUP=$((SLURM_ARRAY_TASK_ID % 3))
SHARD=$((SLURM_ARRAY_TASK_ID / 3))
IDS=$($ROOT/venv/bin/python -c "from pathlib import Path; x=[p.name for p in sorted(Path('$ROOT/data/web40/raw').iterdir()) if p.is_dir()]; print(','.join(x[$SHARD::10]))")
IFS=',' read -ra ID_ARRAY <<< "$IDS"
export PYTHONUNBUFFERED=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1

case "$GROUP" in
  0)
    cd "$ROOT"
    source venv/bin/activate
    python -m scrapebench.runner.protection_run --config configs/web40_single_intervention.yaml --methods arcp_web --ids "$IDS"
    ;;
  1)
    cd /home/huangyue26/GAP-Diff
    for PID in "${ID_ARRAY[@]}"; do
      OUT="$ROOT/data/web40/protected/gapdiff/$PID"
      [ "$(find "$OUT" -maxdepth 1 -type f 2>/dev/null | wc -l)" -ge 4 ] && continue
      mkdir -p "$OUT"
      /home/huangyue26/.conda/envs/gap-diff/bin/python "$ROOT/scripts/run_gapdiff_generate.py" \
        --repo /home/huangyue26/GAP-Diff \
        --generator-path /home/huangyue26/GAP-Diff/weights/model/G_per16_pretrain.pth \
        --source-path "$ROOT/data/web40/protected/clean/$PID" --save-path "$OUT" --noise-budget 16.0
    done
    ;;
  2)
    cd /home/huangyue26/IDProtector
    export PYTHONPATH="/home/huangyue26/IDProtector/pydeps:/home/huangyue26/IDProtector:${PYTHONPATH:-}"
    for PID in "${ID_ARRAY[@]}"; do
      OUT="$ROOT/data/web40/protected/idprotector/$PID"
      [ "$(find "$OUT" -maxdepth 1 -type f -name '*.png' 2>/dev/null | wc -l)" -ge 4 ] && continue
      mkdir -p "$OUT"
      /home/huangyue26/UMO/venv/UMO_UNO/bin/python scripts/protect_recursive.py \
        --input-root="$ROOT/data/web40/protected/clean/$PID" --output-root="$OUT" \
        --checkpoint=/home/huangyue26/IDProtector/protector_model.pt \
        --insightface-root=/home/huangyue26/IDProtector/generation_methods/InstantID \
        --epsilon=0.07 --det-thresholds 0.5 0.3 0.1 --on-detection-failure full-frame
    done
    ;;
esac
