#!/bin/bash
#SBATCH -J sb_rev_A_all
#SBATCH -p rtx
#SBATCH --qos=emerg5
#SBATCH --gres=gpu:1
#SBATCH -c 1
#SBATCH --mem=10G
#SBATCH -t 2-00:00:00
#SBATCH --array=0-107%6
#SBATCH -o /home/huangyue26/ScrapBench/slurm/revision_stage_a_all_%A_%a.out
set -euo pipefail

cd /home/huangyue26/ScrapBench
source venv/bin/activate
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_ENABLE_HF_TRANSFER=0
export HF_HUB_OFFLINE=1
export PYTHONUNBUFFERED=1

# Six experiment groups x 18 identity shards.  Keeping them in one Slurm
# array makes %6 a true global concurrency limit instead of six independent
# per-array limits.
GROUP=$((SLURM_ARRAY_TASK_ID / 18))
SHARD=$((SLURM_ARRAY_TASK_ID % 18))
case "$GROUP" in
  0) ATTACK=ipfaceid; METHODS=clean ;;
  1) ATTACK=instantid; METHODS=clean ;;
  2) ATTACK=ipfaceid; METHODS=arcp_v2 ;;
  3) ATTACK=instantid; METHODS=arcp_v2 ;;
  4) ATTACK=ipfaceid; METHODS=gapdiff,idprotector ;;
  5) ATTACK=instantid; METHODS=gapdiff,idprotector ;;
  *) echo "invalid group: $GROUP" >&2; exit 2 ;;
esac

IDS=$(python scripts/make_identity_split.py --data-root data/celeba_hq100 \
  --out protocol/celeba_hq100_split.json --print-set test \
  --shard "$SHARD" --num-shards 18)

python -m scrapebench.runner.stage_a --config configs/revision_single_tier.yaml \
  --methods "$METHODS" --ids "$IDS" \
  --tiers t0,t1_jpeg70,t2_canvas_dpr1,t3_agent_facecrop,t4_sr_x2,t5_i2i30,t6_diffpure50 \
  --attack "$ATTACK"
