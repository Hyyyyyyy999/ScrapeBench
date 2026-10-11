import os, sys, glob
sys.path.insert(0, "/root/scrapebench")
import torch
from PIL import Image, ImageDraw
from scrapebench.funnel import get_tier
from scrapebench.attack.ip_adapter import ZeroShotFaceID
torch.set_grad_enabled(False)
root = "/root/scrapebench"
zs = ZeroShotFaceID("runwayml/stable-diffusion-v1-5", adapter_repo="h94/IP-Adapter-FaceID",
                    weight_name="ip-adapter-faceid_sd15.bin", scale=0.8)
tiers = ["t0", "t2_canvas_dpr1", "t5_i2i30"]
rows = [("clean", "celeb00003"), ("fsmg", "celeb00027")]
W = 256
canvas = Image.new("RGB", ((W + 6) * 3 + 44, W * 2 + 34), (250, 247, 242))
d = ImageDraw.Draw(canvas)
labels = ["T0", "T2 DPR-1", "T5 regen 0.3"]
for r, (m, pid) in enumerate(rows):
    p = sorted(glob.glob(f"{root}/data/protected/{m}/{pid}/*.png"))[0]
    base = Image.open(p).convert("RGB")
    for c, t in enumerate(tiers):
        im = base if t == "t0" else get_tier(t)(base)
        try:
            gens = zs.generate(["a photo of sks person"], [im], n_per_prompt=2, steps=30, guidance=5.0, seed=0)
            for k, g in enumerate(gens):
                g = g.resize((W // 2, W // 2), Image.LANCZOS)
                canvas.paste(g, (44 + c * (W + 6) + (k % 2) * (W // 2), 28 + r * W + (k // 2) * (W // 2)))
        except RuntimeError:
            d.rectangle([44 + c * (W + 6), 28 + r * W, 44 + c * (W + 6) + W, 28 + r * W + W], fill=(225, 225, 225))
            d.text((44 + c * (W + 6) + 24, 28 + r * W + W // 2), "no face detected", fill=(120, 120, 120))
        if r == 0:
            d.text((44 + c * (W + 6) + 8, 8), labels[c], fill=(40, 40, 40))
    d.text((4, 28 + r * W + W // 2), m, fill=(40, 40, 40))
canvas.save(f"{root}/figures/qual_grid.png")
print("saved", canvas.size)
