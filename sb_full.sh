#!/bin/bash
#SBATCH -J sb_full
#SBATCH -p rtx
#SBATCH --gres=gpu:2
#SBATCH -c 8
#SBATCH --mem=32G
#SBATCH -t 1-12:00:00
#SBATCH -o /home/huangyue26/ScrapBench/slurm/full_%j.out

cd ~/ScrapBench
source ~/ScrapBench/venv/bin/activate
export HF_ENDPOINT=https://hf-mirror.com HF_HUB_ENABLE_HF_TRANSFER=0 PYTHONUNBUFFERED=1 HF_HUB_OFFLINE=1
mkdir -p logs slurm
IDS=celeb00025,celeb00027,celeb00028,celeb00029,celeb00030,celeb00031
echo "=== node $(hostname) ==="; nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv

wait_galleries(){
  for round in 1 2 3; do
    miss=0
    for id in ${IDS//,/ }; do
      for m in clean fsmg fsmgj; do
        n=$(ls data/protected/$m/$id 2>/dev/null | wc -l)
        [ "$n" -lt 8 ] && { miss=1; echo "missing gallery $m/$id n=$n"; }
      done
    done
    [ "$miss" = 0 ] && return 0
    echo "=== protection retry $round ==="
    if [ $((round % 2)) = 1 ]; then
      CUDA_VISIBLE_DEVICES=0 python3 -m scrapebench.runner.protection_run --config configs/full.yaml --methods clean,fsmg --ids $IDS >> logs/prot_w0.log 2>&1
    else
      CUDA_VISIBLE_DEVICES=1 python3 -m scrapebench.runner.protection_run --config configs/full.yaml --methods fsmgj --ids $IDS >> logs/prot_w1.log 2>&1
    fi
  done
  return 1
}

echo "=== protection split: gpu0 clean+fsmg, gpu1 fsmgj ==="
CUDA_VISIBLE_DEVICES=0 python3 -m scrapebench.runner.protection_run --config configs/full.yaml --methods clean,fsmg --ids $IDS > logs/prot_w0.log 2>&1 &
P0=$!
CUDA_VISIBLE_DEVICES=1 python3 -m scrapebench.runner.protection_run --config configs/full_w1.yaml --methods fsmgj --ids $IDS > logs/prot_w1.log 2>&1 &
P1=$!
wait $P0 || echo "prot worker0 exited nonzero"
wait $P1 || echo "prot worker1 exited nonzero"

if wait_galleries; then echo "=== galleries complete ==="; else echo "=== galleries INCOMPLETE, aborting attack ==="; exit 1; fi

run_worker(){
  local gpu=$1; local ids=$2; local cfg=$3; local tag=$4
  for i in 1 2 3; do
    CUDA_VISIBLE_DEVICES=$gpu python3 -m scrapebench.runner.stage_a --config $cfg \
      --methods clean,fsmg,fsmgj --ids $ids --tiers t0,t1_jpeg85,t2_canvas_dpr1,t5_i2i30 \
      --attack instantid >> logs/instant_${tag}.log 2>&1 && return 0
    echo "$(date '+%F %T') worker $tag retry $i" >> logs/instant_${tag}.log
    sleep 60
  done
  return 1
}

echo "=== stage_a instantid: 2 workers ==="
run_worker 0 celeb00025,celeb00027,celeb00028 configs/full.yaml w0 &
P0=$!
run_worker 1 celeb00029,celeb00030,celeb00031 configs/full_w1.yaml w1 &
P1=$!
wait $P0 || echo "attack worker0 failed"
wait $P1 || echo "attack worker1 failed"

echo "=== summary ==="
python3 - <<'EOF'
import csv
tot = {}
for f, run in (("runs/full/results.csv", "full"), ("runs/full_w1/results.csv", "full_w1")):
    try:
        for r in csv.DictReader(open(f)):
            if r["attack"] == "instantid":
                tot[(run, r["pid"], r["method"], r["tier"])] = r
    except FileNotFoundError:
        pass
ok = [v for v in tot.values() if v["n_samples"] not in ("0", "")]
print(f"instantid cells={len(tot)} with_samples={len(ok)} / 72")
for k in sorted(tot):
    r = tot[k]
    print(k[1], k[2], k[3], "n=" + r["n_samples"], "mean=" + (r["mean_id"] or "NA"))
EOF
