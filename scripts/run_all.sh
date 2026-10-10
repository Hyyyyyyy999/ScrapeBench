#!/bin/bash
set -e
cd "$(dirname "$0")/.."
export PYTHONUNBUFFERED=1
STAGE=${1:-A}
case "$STAGE" in
  A)
    python3 -m scrapebench.runner.protection_run --config configs/full.yaml
    CUDA_VISIBLE_DEVICES=0 python3 -m scrapebench.runner.stage_a --config configs/full.yaml
    ;;
  B)
    CUDA_VISIBLE_DEVICES=1 python3 -m scrapebench.runner.stage_b --config configs/full.yaml
    ;;
  C)
    CUDA_VISIBLE_DEVICES=0 python3 -m scrapebench.runner.stage_c --config configs/full.yaml
    ;;
  REPORT)
    python3 -m scrapebench.runner.report --config configs/full.yaml
    ;;
  *)
    echo "usage: run_all.sh [A|B|C|REPORT]"
    exit 1
    ;;
esac
python3 -m scrapebench.runner.report --config configs/full.yaml || true
python3 -m scrapebench.auto_push "stage ${STAGE} results $(date +%Y%m%d-%H%M%S)" || true
echo "[run_all] stage ${STAGE} done"
