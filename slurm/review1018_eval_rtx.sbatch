#!/bin/bash
#SBATCH -J sb1018_eval
#SBATCH -p rtx
#SBATCH --qos=emerg5
#SBATCH --gres=gpu:1
#SBATCH -c 2
#SBATCH --mem=20G
#SBATCH -t 10:00:00
#SBATCH --array=0-479%10
#SBATCH -o /mnt/beegfs/home/huangyue26/ScrapBench/slurm/review1018_eval_%A_%a.out
set -euo pipefail
cd /mnt/beegfs/home/huangyue26/ScrapBench
source venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONUNBUFFERED=1
mapfile -t IDS < <(find data/web40/raw -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)
FULL=(arcp_web_v4 gapdiff_8 idprotector_8)
BASE=(clean gapdiff idprotector)
ABL=(arcp_web_v4_uniform arcp_web_v4_no_texture arcp_web_v4_no_coarse arcp_web_v4_no_detail arcp_web_v4_no_identity arcp_web_v4_no_denoise)
# 528 work items; RTX receives the 480 positions not reserved for every 11th A800 item.
G=$((SLURM_ARRAY_TASK_ID + SLURM_ARRAY_TASK_ID / 10))
if (( G < 240 )); then
  MIDX=$((G / 80)); R=$((G % 80)); AIDX=$((R / 40)); PID=${IDS[$((R % 40))]}; METHOD=${FULL[$MIDX]}; TIERS=t0,t1_jpeg70,t2_canvas_dpr1,t3_agent_facecrop,t4_sr_x2,t5_i2i30,t6_sde35
elif (( G < 480 )); then
  X=$((G - 240)); MIDX=$((X / 80)); R=$((X % 80)); AIDX=$((R / 40)); PID=${IDS[$((R % 40))]}; METHOD=${BASE[$MIDX]}; TIERS=t6_sde35
else
  X=$((G - 480)); MIDX=$((X / 8)); R=$((X % 8)); AIDX=$((R / 4)); PID=${IDS[$((R % 4))]}; METHOD=${ABL[$MIDX]}; TIERS=t0,t1_jpeg70,t2_canvas_dpr1,t3_agent_facecrop,t4_sr_x2,t5_i2i30,t6_sde35
fi
if (( AIDX == 0 )); then ATTACK=instantid; else ATTACK=ipfaceid; fi
python -m scrapebench.runner.stage_a --config configs/web40_single_intervention.yaml --run-name web40_single_intervention --methods "$METHOD" --ids "$PID" --tiers "$TIERS" --attack "$ATTACK"
