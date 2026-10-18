#!/bin/bash
set -u

ROOT=/mnt/beegfs/home/huangyue26/ScrapBench
cd "$ROOT" || exit 1

# The controller occasionally disappears from DNS.  Retry submission only;
# this loop does not poll experiment outputs or consume a GPU.
while true; do
  PROTECT_OUT=$(sbatch --dependency=afterany:141023 slurm/web40_arcp_v2_protect.sbatch 2>&1)
  PROTECT_STATUS=$?
  if [[ $PROTECT_STATUS -eq 0 ]]; then
    break
  fi
  echo "$(date --iso-8601=seconds) protect submission deferred: $PROTECT_OUT"
  sleep 60
done

PROTECT_JOB=${PROTECT_OUT##* }
echo "$(date --iso-8601=seconds) $PROTECT_OUT"

while true; do
  GATE_OUT=$(sbatch --dependency="afterok:${PROTECT_JOB}" slurm/web40_arcp_v2_gate.sbatch 2>&1)
  GATE_STATUS=$?
  if [[ $GATE_STATUS -eq 0 ]]; then
    break
  fi
  echo "$(date --iso-8601=seconds) gate submission deferred: $GATE_OUT"
  sleep 60
done

echo "$(date --iso-8601=seconds) $GATE_OUT"
