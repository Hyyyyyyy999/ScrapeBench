#!/bin/bash
set -euo pipefail
cd /home/huangyue26/ScrapBench
mkdir -p slurm logs
PREP=$(sbatch --parsable slurm/revision_prepare.sbatch)
PROT=$(sbatch --parsable --dependency="afterok:$PREP" slurm/revision_protect.sbatch)
A_IP=$(sbatch --parsable --dependency="afterok:$PROT" --export=ALL,ATTACK=ipfaceid slurm/revision_stage_a.sbatch)
A_INSTANT=$(sbatch --parsable --dependency="afterok:$PROT" --export=ALL,ATTACK=instantid slurm/revision_stage_a.sbatch)
B=$(sbatch --parsable --dependency="afterok:$PROT" slurm/revision_stage_b_gapdiff.sbatch)
printf 'prepare=%s\nprotect=%s\nstage_a_ipfaceid=%s\nstage_a_instantid=%s\nstage_b_gapdiff=%s\n' "$PREP" "$PROT" "$A_IP" "$A_INSTANT" "$B"
