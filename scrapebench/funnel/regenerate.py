import torch
import numpy as np
from PIL import Image

T5_TRANSFORMS = {}
_REGEN = {}


def _get_regen():
    import os
    model_id = os.environ.get("SCRAPEBENCH_SD", "stable-diffusion-v1-5/stable-diffusion-v1-5")
    if model_id not in _REGEN:
        _REGEN[model_id] = Regenerator(model_id)
    return _REGEN[model_id]


def register(names):
    def deco(fn):
        for n in names:
            T5_TRANSFORMS[n] = fn
        return fn
    return deco


@register(["t5_i2i30"])
def _t5_i2i30(img):
    return _get_regen().i2i([img], strength=0.3)[0]


@register(["t5_i2i50"])
def _t5_i2i50(img):
    return _get_regen().i2i([img], strength=0.5)[0]


@register(["t5_inversion"])
def _t5_inv(img):
    return _get_regen().inversion_regen([img], eta=0.1)[0]


class Regenerator:
    def __init__(self, model_id, device="cuda"):
        from diffusers import StableDiffusionImg2ImgPipeline
        self.pipe = StableDiffusionImg2ImgPipeline.from_pretrained(model_id, torch_dtype=torch.float16, safety_checker=None).to(device)
        self.pipe.set_progress_bar_config(disable=True)
        self.device = device

    @torch.no_grad()
    def i2i(self, images, strength=0.3, steps=30, guidance=1.0, seed=0, prompt=""):
        g = torch.Generator(device=self.device).manual_seed(seed)
        return self.pipe(
            prompt=[prompt] * len(images), image=images, strength=strength,
            num_inference_steps=steps, guidance_scale=guidance, generator=g,
        ).images

    @torch.no_grad()
    def inversion_regen(self, images, eta=0.1, guidance=1.0, substeps=50, prompt=""):
        vae, unet, sched = self.pipe.vae, self.pipe.unet, self.pipe.scheduler
        dtype = vae.dtype
        sched.set_timesteps(substeps)
        outs = []
        for im in images:
            im = im.resize((512, 512), Image.LANCZOS).convert("RGB")
            x0 = torch.from_numpy((np.asarray(im, np.float32) / 127.5 - 1.0)).permute(2, 0, 1)[None].to(self.device, dtype)
            z0 = vae.encode(x0).latent_dist.mode() * vae.config.scaling_factor
            emb = self.pipe._encode_prompt("", self.device, 1, False, None) if hasattr(self.pipe, "_encode_prompt") else self.pipe.encode_prompt("", self.device, 1, False, None)[0]
            timesteps = sched.timesteps
            z = z0
            eps_store = []
            for i, t in enumerate(timesteps):
                t_b = t[None].to(self.device)
                eps = unet(z, t_b, encoder_hidden_states=emb).sample
                alpha_t = sched.alphas_cumprod[t]
                z_prev = (z - (1 - alpha_t).sqrt() * eps) / alpha_t.sqrt()
                z = z_prev
                eps_store.append(eps)
            zT = z
            g = torch.Generator(device=self.device).manual_seed(0)
            z = zT
            for i in range(len(timesteps) - 1, -1, -1):
                t = timesteps[i]
                t_b = t[None].to(self.device)
                alpha_t = sched.alphas_cumprod[t]
                alpha_prev = sched.alphas_cumprod[timesteps[i - 1]] if i > 0 else torch.tensor(1.0, device=self.device)
                eps = eps_store[i]
                pred_x0 = (z - (1 - alpha_t).sqrt() * eps) / alpha_t.sqrt()
                dir_eps = (1 - alpha_prev).sqrt() * eps
                noise = torch.randn(z.shape, generator=g, device=self.device, dtype=dtype) if eta > 0 else 0.0
                sigma = eta * ((1 - alpha_t) / alpha_prev * (1 - alpha_prev / alpha_t)).sqrt() if i > 0 else 0.0
                z = alpha_prev.sqrt() * pred_x0 + dir_eps + sigma * noise
            img = vae.decode(z / vae.config.scaling_factor, return_dict=False)[0][0]
            arr = ((img.float().cpu().permute(1, 2, 0).numpy() + 1.0) * 127.5).clip(0, 255).astype(np.uint8)
            outs.append(Image.fromarray(arr))
        return outs
