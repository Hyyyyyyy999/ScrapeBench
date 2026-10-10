#!/bin/bash
set -e
cd "$(dirname "$0")/.."
export PYTHONUNBUFFERED=1
python3 scripts/prepare_data.py --source demo --data-root data --per-id 8
python3 -m scrapebench.runner.protection_run --config configs/smoke.yaml --methods clean,random,fsmg
python3 -m scrapebench.runner.stage_a --config configs/smoke.yaml
python3 -m scrapebench.runner.report --config configs/smoke.yaml || true
python3 -m scrapebench.runner.stage_b --config configs/smoke.yaml
python3 -m scrapebench.runner.stage_c --config configs/smoke.yaml
python3 -m scrapebench.runner.report --config configs/smoke.yaml
python3 -m scrapebench.auto_push "smoke results $(date +%Y%m%d-%H%M%S)"
echo "[smoke] ALL DONE"
