#!/bin/bash
cd /root/scrapebench || exit 1
GPU=$1; TAG=$2; METHODS=$3; IDS=$4; NEXT=$5
LOG=logs/chain$TAG.log
echo "$(date '+%F %T') chain$TAG start gpu=$GPU methods=$METHODS" >> "$LOG"
for i in $(seq 1 30); do
    CUDA_VISIBLE_DEVICES=$GPU python3 -m scrapebench.runner.stage_a --config configs/full.yaml --methods $METHODS --ids $IDS >> logs/full_a$TAG.log 2>&1
    rc=$?
    [ $rc = 0 ] && break
    echo "$(date '+%F %T') stage_a attempt $i rc=$rc; retry 60s" >> "$LOG"
    sleep 60
done
echo "$(date '+%F %T') stage_a finished" >> "$LOG"
if [ -n "$NEXT" ]; then
    for i in $(seq 1 30); do
        CUDA_VISIBLE_DEVICES=$GPU python3 -m scrapebench.runner.$NEXT --config configs/full.yaml --ids $6 >> logs/full_${NEXT:6:1}$TAG.log 2>&1
        rc=$?
        [ $rc = 0 ] && break
        echo "$(date '+%F %T') $NEXT attempt $i rc=$rc; retry 60s" >> "$LOG"
        sleep 60
    done
    echo "$(date '+%F %T') $NEXT finished" >> "$LOG"
fi
echo "$(date '+%F %T') chain$TAG done" >> "$LOG"
