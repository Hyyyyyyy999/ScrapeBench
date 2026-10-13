#!/bin/bash
#SBATCH -J sb_full_1gpu
#SBATCH -p rtx
#SBATCH --gres=gpu:1
#SBATCH -c 8
#SBATCH --mem=32G
#SBATCH -t 1-12:00:00
#SBATCH -o /home/huangyue26/ScrapBench/slurm/full_1gpu_%j.out

cd /home/huangyue26/ScrapBench || exit 1
source /home/huangyue26/ScrapBench/venv/bin/activate
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_ENABLE_HF_TRANSFER=0
export HF_HUB_OFFLINE=1
export PYTHONUNBUFFERED=1
mkdir -p logs slurm

IDS=celeb00025,celeb00027,celeb00028,celeb00029,celeb00030,celeb00031
METHODS=clean,fsmg,fsmgj
TIERS=t0,t1_jpeg85,t2_canvas_dpr1,t5_i2i30

echo "=== node $(hostname) ==="
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv

galleries_complete() {
  for id in ${IDS//,/ }; do
    for method in ${METHODS//,/ }; do
      count=$(find "data/protected/$method/$id" -maxdepth 1 -type f 2>/dev/null | wc -l)
      if [ "$count" -lt 8 ]; then
        echo "missing gallery $method/$id n=$count"
        return 1
      fi
    done
  done
  return 0
}

echo "=== protection: clean + FSMG + FSMG-J ==="
for attempt in 1 2 3; do
  python3 -m scrapebench.runner.protection_run \
    --config configs/full.yaml --methods "$METHODS" --ids "$IDS" \
    >> logs/prot_single.log 2>&1 || true
  galleries_complete && break
  echo "$(date '+%F %T') protection retry $attempt" >> logs/prot_single.log
done

if ! galleries_complete; then
  echo "=== galleries INCOMPLETE, aborting attack ==="
  exit 1
fi

echo "=== stage_a InstantID: resumable 6 x 3 x 4 grid ==="
attack_ok=0
for attempt in 1 2 3; do
  if python3 -m scrapebench.runner.stage_a \
    --config configs/full.yaml --methods "$METHODS" --ids "$IDS" \
    --tiers "$TIERS" --attack instantid \
    >> logs/instant_single.log 2>&1; then
    attack_ok=1
    break
  fi
  echo "$(date '+%F %T') InstantID retry $attempt" >> logs/instant_single.log
done

echo "=== summary ==="
python3 - <<'PY'
import csv

latest = {}
with open("runs/full/results.csv", newline="") as handle:
    for row in csv.DictReader(handle):
        if row["attack"] == "instantid":
            latest[(row["pid"], row["method"], row["tier"])] = row
complete = [row for row in latest.values() if int(row.get("n_samples") or 0) > 0]
print(f"instantid cells={len(latest)} with_samples={len(complete)} / 72")
for key in sorted(latest):
    row = latest[key]
    print(*key, "n=" + row["n_samples"], "mean=" + (row["mean_id"] or "NA"))
PY

[ "$attack_ok" -eq 1 ]
