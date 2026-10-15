#!/bin/bash
#SBATCH -J sb_rev_data
#SBATCH -p cpu
#SBATCH -c 4
#SBATCH --mem=24G
#SBATCH -t 08:00:00
#SBATCH -o /home/huangyue26/ScrapBench/slurm/revision_prepare_%j.out
set -euo pipefail
cd /home/huangyue26/ScrapBench
source venv/bin/activate
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY all_proxy
export HF_ENDPOINT=https://huggingface.co
export HF_HUB_ENABLE_HF_TRANSFER=0
export PYTHONUNBUFFERED=1
python scripts/fetch_celeba.py --out data --n-ids 100 --per-id 8 --max-scan 202599
python scripts/make_identity_split.py --data-root data --n 100
