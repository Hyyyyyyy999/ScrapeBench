#!/bin/bash
#SBATCH --job-name=sb_arcpv4_g
#SBATCH --partition=rtx4090
#SBATCH --qos=emerg5
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --array=0-1%2
#SBATCH --output=slurm/web40_arcp_v4_gate_%A_%a.out

set -euo pipefail
cd /mnt/beegfs/home/huangyue26/ScrapBench
source venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONUNBUFFERED=1
mapfile -t ALL_IDS < <(find data/web40/raw -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)
IDS=$(IFS=,; echo "${ALL_IDS[*]:0:4}")
if [[ "$SLURM_ARRAY_TASK_ID" -eq 0 ]]; then ATTACK=instantid; else ATTACK=ipfaceid; fi
python -m scrapebench.runner.stage_a \
  --config configs/web40_single_intervention.yaml \
  --methods arcp_web_v4 --ids "$IDS" --attack "$ATTACK" \
  --tiers t0,t1_jpeg70,t2_canvas_dpr1,t3_agent_facecrop,t4_sr_x2,t5_i2i30,t6_sde50 --force
