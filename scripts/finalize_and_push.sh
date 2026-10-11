#!/bin/bash
cd /root/scrapebench || exit 1
LOG=logs/finalize.log
MARK=logs/finalize_done
[ -f "$MARK" ] && echo "$(date '+%F %T') already done" >> "$LOG" && exit 0
last_count=-1
stable=0
while true; do
    sleep 300
    n=$(wc -l < runs/full/results.csv 2>/dev/null || echo 0)
    running=$(pgrep -fc "python3 -m scrapebench.runner" 2>/dev/null || true)
    if [ "$n" = "$last_count" ] && [ "${running:-0}" = "0" ]; then
        stable=$((stable+1))
    else
        stable=0
    fi
    last_count=$n
    echo "$(date '+%F %T') rows=$n running=${running:-0} stable=$stable" >> "$LOG"
    if [ "$stable" -ge 4 ]; then
        echo "$(date '+%F %T') finalize triggered at rows=$n" >> "$LOG"
        python3 -m scrapebench.runner.report --config configs/full.yaml >> "$LOG" 2>&1
        python3 -m scrapebench.auto_push "full-run results + figures $(date '+%m%d-%H%M')" >> "$LOG" 2>&1
        touch "$MARK"
        echo "$(date '+%F %T') finalize complete" >> "$LOG"
        exit 0
    fi
done
