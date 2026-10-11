#!/bin/bash
cd /root/scrapebench || exit 1
LOG=logs/supervisor.log
IDS0=celeb00001,celeb00003,celeb00004,celeb00005,celeb00006,celeb00007,celeb00008,celeb00010,celeb00011,celeb00012,celeb00013,celeb00014,celeb00015,celeb00017,celeb00019,celeb00020,celeb00021,celeb00022,celeb00023,celeb00024
IDS1=celeb00025,celeb00027,celeb00028,celeb00029,celeb00030,celeb00031,celeb00032,celeb00033,celeb00034,celeb00035,celeb00036,celeb00038,celeb00039,celeb00040,celeb00041,celeb00042,celeb00043,celeb00045,celeb00046,celeb00047
BIDS=celeb00001,celeb00003,celeb00004,celeb00005,celeb00006,celeb00007,celeb00025,celeb00027,celeb00028,celeb00029,celeb00030,celeb00031
rows() {
python3 - <<'PY'
import csv
from collections import Counter
try:
    rows = list(csv.DictReader(open("runs/full/results.csv")))
except Exception:
    rows = []
c = Counter((r["stage"], r["method"]) for r in rows)
print(c.get(("A","clean"),0)+c.get(("A","random"),0), c.get(("B","clean"),0)+c.get(("B","random"),0)+c.get(("B","fsmg"),0), c.get(("A","fsmg"),0)+c.get(("A","aspl"),0), c.get(("C","fsmg"),0))
PY
}
prev0=-1; prevb=-1; prev1=-1; prevc=-1
probe0=0; probeb=0; probe1=0; probec=0
p0=0; pb=0; p1=0; pc=0
a0done=0; bdone=0; a1done=0; cdone=0
last=0
while true; do
    sleep 150
    read R0 RB R1 RC <<< "$(rows)"
    now=$(date +%s); gap=$(( now - last ))
    A0_RUN=$(pgrep -fc "runner.stage_a.*clean,random" 2>/dev/null || echo 0)
    B_RUN=$(pgrep -fc "runner.stage_b" 2>/dev/null || echo 0)
    A1_RUN=$(pgrep -fc "runner.stage_a.*fsmg,aspl" 2>/dev/null || echo 0)
    C_RUN=$(pgrep -fc "runner.stage_c" 2>/dev/null || echo 0)
    if [ $a0done = 0 ]; then
        if [ "$A0_RUN" -gt 0 ]; then prev0=$R0; stall=0
        elif [ "$R0" = "$prev0" ]; then
            probe0=$((probe0+1))
            if [ $probe0 = 1 ] && [ $p0 -lt 10 ]; then
                echo "$(date '+%F %T') stall probe gpu0 stage_a rows=$R0" >> "$LOG"
                CUDA_VISIBLE_DEVICES=0 nohup python3 -m scrapebench.runner.stage_a --config configs/full.yaml --methods clean,random --ids $IDS0 >> logs/full_a0.log 2>&1 &
                p0=$((p0+1)); last=$now
            elif [ $probe0 -ge 3 ]; then
                a0done=1; echo "$(date '+%F %T') gpu0 stage_a complete rows=$R0" >> "$LOG"
            fi
        else
            prev0=$R0; probe0=0
        fi
    elif [ $bdone = 0 ]; then
        if [ "$B_RUN" -gt 0 ]; then prevb=$RB
        elif [ "$RB" = "$prevb" ]; then
            probeb=$((probeb+1))
            if [ $probeb = 1 ] && [ $pb -lt 10 ]; then
                echo "$(date '+%F %T') stall probe gpu0 stage_b rows=$RB" >> "$LOG"
                CUDA_VISIBLE_DEVICES=0 nohup python3 -m scrapebench.runner.stage_b --config configs/full.yaml --ids $BIDS >> logs/full_b0.log 2>&1 &
                pb=$((pb+1)); last=$now
            elif [ $probeb -ge 3 ]; then
                bdone=1; echo "$(date '+%F %T') gpu0 stage_b complete rows=$RB" >> "$LOG"
            fi
        else
            prevb=$RB; probeb=0
        fi
    fi
    if [ $a1done = 0 ]; then
        if [ "$A1_RUN" -gt 0 ]; then prev1=$R1
        elif [ "$R1" = "$prev1" ]; then
            probe1=$((probe1+1))
            if [ $probe1 = 1 ] && [ $p1 -lt 10 ]; then
                echo "$(date '+%F %T') stall probe gpu1 stage_a rows=$R1" >> "$LOG"
                CUDA_VISIBLE_DEVICES=1 nohup python3 -m scrapebench.runner.stage_a --config configs/full.yaml --methods fsmg,aspl --ids $IDS1 >> logs/full_a1.log 2>&1 &
                p1=$((p1+1)); last=$now
            elif [ $probe1 -ge 3 ]; then
                a1done=1; echo "$(date '+%F %T') gpu1 stage_a complete rows=$R1" >> "$LOG"
            fi
        else
            prev1=$R1; probe1=0
        fi
    elif [ $cdone = 0 ]; then
        if [ "$C_RUN" -gt 0 ]; then prevc=$RC
        elif [ "$RC" = "$prevc" ]; then
            probec=$((probec+1))
            if [ $probec = 1 ] && [ $pc -lt 10 ]; then
                echo "$(date '+%F %T') stall probe gpu1 stage_c rows=$RC" >> "$LOG"
                CUDA_VISIBLE_DEVICES=1 nohup python3 -m scrapebench.runner.stage_c --config configs/full.yaml --ids $BIDS >> logs/full_c1.log 2>&1 &
                pc=$((pc+1)); last=$now
            elif [ $probec -ge 3 ]; then
                cdone=1; echo "$(date '+%F %T') gpu1 stage_c complete rows=$RC" >> "$LOG"
            fi
        else
            prevc=$RC; probec=0
        fi
    fi
    if [ $a0done = 1 ] && [ $bdone = 1 ] && [ $a1done = 1 ] && [ $cdone = 1 ]; then
        echo "$(date '+%F %T') all stages complete" >> "$LOG"
        exit 0
    fi
done
