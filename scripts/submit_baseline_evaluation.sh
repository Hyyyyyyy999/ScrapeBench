#!/bin/bash
set -euo pipefail
cd /home/huangyue26/ScrapBench
DEPENDENCY=${1:?usage: submit_baseline_evaluation.sh SLURM_DEPENDENCY}
A_IP=$(sbatch --parsable --dependency="afterok:$DEPENDENCY" \
  --export=ALL,ATTACK=ipfaceid,METHODS=gapdiff,idprotector slurm/revision_stage_a.sbatch)
A_INSTANT=$(sbatch --parsable --dependency="afterok:$DEPENDENCY" \
  --export=ALL,ATTACK=instantid,METHODS=gapdiff,idprotector slurm/revision_stage_a.sbatch)
B=$(sbatch --parsable --dependency="afterok:$DEPENDENCY" \
  --export=ALL,METHODS=gapdiff,idprotector slurm/revision_stage_b_gapdiff.sbatch)
printf 'baseline_stage_a_ipfaceid=%s\nbaseline_stage_a_instantid=%s\nbaseline_stage_b=%s\n' "$A_IP" "$A_INSTANT" "$B"
