#!/bin/bash
#SBATCH -J sb_rev_data
#SBATCH -p cpu
#SBATCH -c 4
#SBATCH --mem=24G
#SBATCH -t 08:00:00
#SBATCH -o /home/huangyue26/ScrapBench/slurm/revision_prepare_%j.out
set -euo pipefail
cd /home/huangyue26/ScrapBench
export PYTHONUNBUFFERED=1
venv/bin/python scripts/prepare_celeba_hq100.py \
  --archive /mnt/beegfs/home/huangyue26/anti-dreambooth/data/celeba-hq/CelebA-HQ.tar.gz \
  --mapping data/metadata/CelebA-HQ-to-CelebA-mapping.txt \
  --identities data/metadata/identity_CelebA.txt \
  --out data/celeba_hq100 --n-ids 100 --gallery 8 --refs 2
venv/bin/python scripts/make_identity_split.py --data-root data/celeba_hq100 \
  --out protocol/celeba_hq100_split.json --n 100
