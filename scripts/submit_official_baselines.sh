#!/bin/bash
set -euo pipefail
cd /home/huangyue26/ScrapBench
DATA_JOB=${1:?usage: submit_official_baselines.sh DATA_JOB_ID}
SETUP=$(sbatch --parsable --dependency="afterok:$DATA_JOB" slurm/revision_setup_baselines.sbatch)
GAP=$(sbatch --parsable --dependency="afterok:$SETUP" slurm/revision_gapdiff_protect.sbatch)
IDP=$(sbatch --parsable --dependency="afterok:$SETUP" slurm/revision_idprotector_protect.sbatch)
printf 'baseline_setup=%s\ngapdiff_protect=%s\nidprotector_protect=%s\n' "$SETUP" "$GAP" "$IDP"
