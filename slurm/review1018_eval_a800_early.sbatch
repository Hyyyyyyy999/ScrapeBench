#!/bin/bash
#SBATCH -J sb1018_earlyA
#SBATCH -p a800
#SBATCH --qos=a800-2
#SBATCH --gres=gpu:1
#SBATCH -c 4
#SBATCH --mem=64G
#SBATCH -t 08:00:00
#SBATCH -o /mnt/beegfs/home/huangyue26/ScrapBench/slurm/review1018_eval_early_%j.out
set -euo pipefail
cd /mnt/beegfs/home/huangyue26/ScrapBench
source venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONUNBUFFERED=1
mapfile -t IDS < <(find data/web40/raw -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)
FULL=(arcp_web_v4 gapdiff_8 idprotector_8)
BASE=(clean gapdiff idprotector)
# Run only the already-ready primary cells reserved for the A800 lane.  The
# dependent full A800 job is idempotent and will later skip these ledgers.
for ((G=10; G<480; G+=11)); do
  if (( G < 240 )); then
    MIDX=$((G / 80)); R=$((G % 80)); AIDX=$((R / 40)); PID=${IDS[$((R % 40))]}; METHOD=${FULL[$MIDX]}; TIERS=t0,t1_jpeg70,t2_canvas_dpr1,t3_agent_facecrop,t4_sr_x2,t5_i2i30,t6_sde35
  else
    X=$((G - 240)); MIDX=$((X / 80)); R=$((X % 80)); AIDX=$((R / 40)); PID=${IDS[$((R % 40))]}; METHOD=${BASE[$MIDX]}; TIERS=t6_sde35
  fi
  if (( AIDX == 0 )); then ATTACK=instantid; else ATTACK=ipfaceid; fi
  python -m scrapebench.runner.stage_a --config configs/web40_single_intervention.yaml --run-name web40_single_intervention --methods "$METHOD" --ids "$PID" --tiers "$TIERS" --attack "$ATTACK"
done
