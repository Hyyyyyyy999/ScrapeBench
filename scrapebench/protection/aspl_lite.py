import torch
from PIL import Image
from .fsmg import train_surrogate, pgd_fsmg
from ..attack.train_utils import load_gallery, CLASS_PROMPT


def aspl_lite(comps, gallery_paths, out_dir, eps=8.0 / 255.0, alpha=1.0 / 255.0,
              outer_rounds=2, surrogate_steps=200, pgd_steps=100, resolution=512):
    import os
    os.makedirs(out_dir, exist_ok=True)
    imgs = load_gallery(gallery_paths, resolution)
    perturbed = list(imgs)
    for r in range(outer_rounds):
        train_surrogate(comps, perturbed, steps=surrogate_steps, prompt=CLASS_PROMPT, log_every=50)
        perturbed = pgd_fsmg(comps, imgs, eps=eps, alpha=alpha, steps=pgd_steps, prompt=CLASS_PROMPT)
        print(f"[aspl_lite] outer round {r + 1}/{outer_rounds} done", flush=True)
    for i, im in enumerate(perturbed):
        im.save(os.path.join(out_dir, f"{i:04d}.png"))
    return perturbed
