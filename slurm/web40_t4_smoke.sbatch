#!/bin/bash
#SBATCH -J sb40_t4gate
#SBATCH -p rtx4090
#SBATCH --qos=emerg5
#SBATCH --gres=gpu:1
#SBATCH -c 2
#SBATCH --mem=12G
#SBATCH -t 00:20:00
#SBATCH -o /home/huangyue26/ScrapBench/slurm/web40_t4gate_%j.out
set -euo pipefail
cd /home/huangyue26/ScrapBench
source venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONUNBUFFERED=1
python - <<'PY'
from PIL import Image
from scrapebench.funnel import get_tier
image = Image.open('data/web40/protected/clean/celeb00008/0000.png').convert('RGB')
output = get_tier('t4_sr_x2')(image)
assert output.size == (1024, 1024), output.size
print('T4 Real-ESRGAN gate passed:', output.size)
PY
