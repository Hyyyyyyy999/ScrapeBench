#!/bin/bash
# ScrapeBench InstantID stress-grid bootstrap v2 (login node, idempotent, resumable)
PROJ=/home/huangyue26/ScrapBench
VENV=$PROJ/venv
export PYTHONUNBUFFERED=1
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_ENABLE_HF_TRANSFER=0

step(){ echo; echo "===== [$(date '+%F %T')] $1 ====="; }

step "extract code"
mkdir -p $PROJ
tar xzf $PROJ/sb_code.tar.gz -C $PROJ
ls $PROJ

step "venv + deps (skip if already importable)"
if $VENV/bin/python -c "import torch,diffusers,transformers,insightface,peft,datasets" 2>/dev/null; then
  echo "deps already installed, skip pip"
else
  python3 -m venv $VENV
  $VENV/bin/pip install -U pip
  $VENV/bin/pip install \
    numpy==1.26.4 "cython==0.29.37" \
    torch torchvision \
    diffusers==0.29.2 transformers==4.44.2 accelerate peft safetensors huggingface_hub \
    insightface==0.7.3 onnxruntime opencv-python-headless \
    pandas scipy matplotlib pillow pyyaml tqdm datasets sentencepiece
fi
$VENV/bin/python -c "import torch,diffusers,transformers,insightface,peft,datasets;print('IMPORTS OK', torch.__version__, diffusers.__version__)"

step "instantid pipeline file"
mkdir -p ~/instantid_repo
rm -f ~/instantid_repo/pipeline_stable_diffusion_xl_instantid.py
if [ ! -s ~/instantid_repo/pipeline_stable_diffusion_xl_instantid.py ]; then
  curl -fsSL https://raw.githubusercontent.com/InstantID/InstantID/main/pipeline_stable_diffusion_xl_instantid.py \
    -o ~/instantid_repo/pipeline_stable_diffusion_xl_instantid.py \
  || git clone --depth 1 https://github.com/InstantID/InstantID ~/instantid_repo_tmp \
     && { cp ~/instantid_repo_tmp/pipeline_stable_diffusion_xl_instantid.py ~/instantid_repo/ 2>/dev/null; rm -rf ~/instantid_repo_tmp; }
fi
wc -l ~/instantid_repo/pipeline_stable_diffusion_xl_instantid.py
grep -c "class StableDiffusionXLInstantIDPipeline" ~/instantid_repo/pipeline_stable_diffusion_xl_instantid.py

step "insightface packs under ScrapBench/face_models"
PACK_ROOT=$PROJ/face_models
mkdir -p $PACK_ROOT/models && cd $PACK_ROOT
if [ -z "$(ls models/antelopev2/*.onnx 2>/dev/null | head -1)" ]; then
  curl -fsSL -o antelopev2.zip https://github.com/deepinsight/insightface/releases/download/model-zoo/antelopev2.zip
  $VENV/bin/python -c "import zipfile;zipfile.ZipFile('antelopev2.zip').extractall('models/antelopev2')"
  [ -d models/antelopev2/antelopev2 ] && { mv models/antelopev2/antelopev2/* models/antelopev2/; rmdir models/antelopev2/antelopev2; }
fi
if [ -z "$(ls models/buffalo_l/*.onnx 2>/dev/null | head -1)" ]; then
  curl -fsSL -o buffalo_l.zip https://github.com/deepinsight/insightface/releases/download/v0.7/buffalo_l.zip
  $VENV/bin/python -c "import zipfile;zipfile.ZipFile('buffalo_l.zip').extractall('models/buffalo_l')"
  [ -d models/buffalo_l/buffalo_l ] && { mv models/buffalo_l/buffalo_l/* models/buffalo_l/; rmdir models/buffalo_l/buffalo_l; }
fi
ls models/antelopev2 models/buffalo_l
if [ -d ~/.insightface ] && [ -n "$(ls -A ~/.insightface 2>/dev/null)" ]; then
  echo "~/.insightface not empty, copying packs into it"
  mkdir -p ~/.insightface/models
  cp -rn $PACK_ROOT/models/* ~/.insightface/models/
else
  rmdir ~/.insightface 2>/dev/null
  ln -sfn $PACK_ROOT ~/.insightface
  echo "symlink: ~/.insightface -> $PACK_ROOT"
fi
ls -la ~/.insightface/models/

step "InstantID weights via hf-mirror (shared HF cache)"
$VENV/bin/python - <<'PYEOF'
from huggingface_hub import snapshot_download
p = snapshot_download("InstantX/InstantID", allow_patterns=["ControlNetModel/*", "ip-adapter.bin"])
print("snapshot at", p)
PYEOF

step "fetch celeba data"
cd $PROJ
for i in 1 2 3; do
  $VENV/bin/python scripts/fetch_celeba.py --out data --n-ids 32 --max-scan 60000 && break
  echo "fetch retry $i"; sleep 30
done
echo "--- data counts ---"
for id in celeb00025 celeb00027 celeb00028 celeb00029 celeb00030 celeb00031; do
  echo "$id raw=$(ls data/raw/$id 2>/dev/null | wc -l) refs=$(ls data/refs/$id 2>/dev/null | wc -l)"
done

step "ALL DONE"
