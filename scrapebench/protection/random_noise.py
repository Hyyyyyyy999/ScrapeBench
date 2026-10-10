import torch
import numpy as np
from PIL import Image
from .base import pil_to_tensor, tensor_to_pil


def make_random_noise(imgs, eps=8.0 / 255.0, seed=0):
    rng = np.random.default_rng(seed)
    out = []
    for im in imgs:
        arr = np.asarray(im.convert("RGB"), dtype=np.float32) / 255.0
        arr = arr + rng.uniform(-eps, eps, size=arr.shape)
        out.append(Image.fromarray((arr * 255.0).clip(0, 255).astype(np.uint8)))
    return out
