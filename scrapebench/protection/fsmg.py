import torch
import numpy as np
from PIL import Image
from .base import pil_to_tensor, tensor_to_pil, clamp_eps
from ..attack.train_utils import text_embed, encode_latents, add_lora, reset_lora, dreambooth_loss, CLASS_PROMPT

_ADAPTER_N = {"c": 0}


def train_surrogate(comps, images, steps=200, batch_size=4, lr=1e-4, rank=16, prompt=CLASS_PROMPT, log_every=50, jpeg_aware=0):
    unet = comps["unet"]
    _ADAPTER_N["c"] += 1
    opt = add_lora(unet, rank=rank, lr=lr, name=f"sur{_ADAPTER_N['c']}")
    unet.train()
    rng = np.random.default_rng(0)
    for step in range(steps):
        idx = rng.integers(0, len(images), size=min(batch_size, len(images)))
        batch = [images[i] for i in idx]
        loss = dreambooth_loss(comps, batch, prompt, jpeg_aware=jpeg_aware)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_([p for p in unet.parameters() if p.requires_grad], 1.0)
        opt.step()
        if log_every and (step + 1) % log_every == 0:
            print(f"[surrogate] step {step + 1}/{steps} loss {loss.item():.4f}", flush=True)
    unet.eval()
    return unet


@torch.enable_grad()
def pgd_fsmg(comps, images, eps=8.0 / 255.0, alpha=1.0 / 255.0, steps=100, prompt=CLASS_PROMPT, batch_all=True, jpeg_aware=0):
    vae, unet, sched = comps["vae"], comps["unet"], comps["scheduler"]
    device, dtype = comps["device"], comps["dtype"]
    orig = pil_to_tensor(images, device, dtype)
    x = orig.clone().detach().requires_grad_(True)
    emb = text_embed(comps, [prompt] * orig.shape[0])
    for step in range(steps):
        xa = x
        if jpeg_aware:
            from ..attack.diffjpeg import diff_jpeg
            xa = diff_jpeg((x + 1.0) / 2.0, quality=jpeg_aware) * 2.0 - 1.0
        lat = encode_latents(vae, xa)
        noise = torch.randn(lat.shape, device=device, dtype=dtype)
        t = torch.randint(20, 980, (lat.shape[0],), device=device)
        noisy = sched.add_noise(lat, noise, t)
        pred = unet(noisy, t, encoder_hidden_states=emb).sample
        loss = torch.nn.functional.mse_loss(pred.float(), noise.float(), reduction="mean")
        grad, = torch.autograd.grad(loss, x)
        with torch.no_grad():
            x.add_(alpha * grad.sign())
            x.clamp_(-1, 1)
            clamp_eps(x, orig, eps)
            x.clamp_(-1, 1)
        x.requires_grad_(True)
    return tensor_to_pil(x)
