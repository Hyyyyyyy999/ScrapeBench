#!/bin/bash
#SBATCH --job-name=sb_off_eval
#SBATCH --partition=rtx4090
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=08:00:00
#SBATCH --array=0-19%6
#SBATCH --output=slurm/web40_official_eval_%A_%a.out

set -euo pipefail
: "${METHOD:?submit with METHOD=goodac or metacloak}"
cd /mnt/beegfs/home/huangyue26/ScrapBench
source venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONUNBUFFERED=1
TASK=$SLURM_ARRAY_TASK_ID
SHARD=$((TASK / 2))
if (( TASK % 2 == 0 )); then ATTACK=instantid; else ATTACK=ipfaceid; fi
mapfile -t ALL_IDS < <(find data/web40/raw -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)
IDS=$(IFS=,; echo "${ALL_IDS[*]:$((SHARD * 4)):4}")
RUN_ARGS=()
if [[ -n "${RUN_NAME:-}" ]]; then RUN_ARGS+=(--run-name "$RUN_NAME"); fi
python -m scrapebench.runner.stage_a \
  --config configs/web40_single_intervention.yaml --methods "$METHOD" \
  --ids "$IDS" --attack "$ATTACK" "${RUN_ARGS[@]}" \
  --tiers t0,t1_jpeg70,t2_canvas_dpr1,t3_agent_facecrop,t4_sr_x2,t5_i2i30,t6_sde50 --force
