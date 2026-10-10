import torch
import numpy as np
from PIL import Image


def pil_to_tensor(imgs, device, dtype):
    arr = np.stack([np.asarray(im.convert("RGB"), dtype=np.float32) for im in imgs]) / 127.5 - 1.0
    return torch.from_numpy(arr).permute(0, 3, 1, 2).to(device, dtype)


def tensor_to_pil(x):
    x = x.detach().float().clamp(-1, 1).cpu().permute(0, 2, 3, 1).numpy()
    return [Image.fromarray(((im + 1.0) * 127.5).clip(0, 255).astype(np.uint8)) for im in x]


def clamp_eps(x, orig, eps):
    return torch.maximum(torch.minimum(x, orig + eps), orig - eps)
