#!/bin/bash
set -euo pipefail
cd /home/huangyue26/ScrapBench
DATA_JOB=${1:?usage: submit_official_baselines.sh DATA_JOB_ID}
GAP=$(sbatch --parsable --dependency="afterok:$DATA_JOB" slurm/revision_gapdiff_protect.sbatch)
IDP=$(sbatch --parsable --dependency="afterok:$DATA_JOB" slurm/revision_idprotector_protect.sbatch)
printf 'gapdiff_protect=%s\nidprotector_protect=%s\n' "$GAP" "$IDP"
