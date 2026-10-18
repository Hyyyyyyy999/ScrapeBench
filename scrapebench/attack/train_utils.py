import random
import numpy as np
import torch
from PIL import Image
RESAMPLE_LANCZOS = getattr(getattr(Image, "Resampling", Image), "LANCZOS")

PROMPTS = [
    "a photo of a sks person",
    "a dslr portrait of sks person",
    "a close-up photo of sks person riding a bike",
    "a photo of sks person in front of eiffel tower",
    "a selfie photo of sks person on top of mount fuji",
]

# Exact prompt set used by GAP-Diff Table I and Figure 8.
GAPDIFF_PROMPTS = [
    "a photo of sks person",
    "a dslr portrait of sks person",
    "a photo of sks person looking at the mirror",
    "a photo of sks person in front of eiffel tower",
]
CLASS_PROMPT = "a photo of a person"


def seed_all(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def load_sd15(model_id, device="cuda", fp16=True):
    from diffusers import StableDiffusionPipeline, UNet2DConditionModel, AutoencoderKL, DDPMScheduler
    from transformers import CLIPTextModel, CLIPTokenizer
    dtype = torch.bfloat16 if fp16 else torch.float32
    tok = CLIPTokenizer.from_pretrained(model_id, subfolder="tokenizer")
    te = CLIPTextModel.from_pretrained(model_id, subfolder="text_encoder").to(device, dtype=dtype)
    vae = AutoencoderKL.from_pretrained(model_id, subfolder="vae").to(device, dtype=dtype)
    vae.requires_grad_(False)
    unet = UNet2DConditionModel.from_pretrained(model_id, subfolder="unet").to(device, dtype=dtype)
    sched = DDPMScheduler.from_pretrained(model_id, subfolder="scheduler")
    comps = dict(tokenizer=tok, text_encoder=te, vae=vae, unet=unet, scheduler=sched, dtype=dtype, device=device)
    comps["pipeline_factory"] = lambda: StableDiffusionPipeline(
        vae=vae, text_encoder=te, tokenizer=tok, unet=unet,
        scheduler=sched.__class__.from_config(sched.config),
        safety_checker=None, feature_extractor=None, requires_safety_checker=False,
    ).to(device)
    return comps


def load_gallery(paths, resolution=512):
    imgs = []
    for p in paths:
        im = Image.open(p).convert("RGB")
        w, h = im.size
        s = min(w, h)
        im = im.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2))
        imgs.append(im.resize((resolution, resolution), RESAMPLE_LANCZOS))
    return imgs


def images_to_tensor(imgs, dtype):
    arr = np.stack([np.asarray(im, dtype=np.float32) for im in imgs]) / 127.5 - 1.0
    return torch.from_numpy(arr).permute(0, 3, 1, 2).to(dtype)


def encode_latents(vae, x):
    lat = vae.encode(x).latent_dist.sample()
    return lat * vae.config.scaling_factor


def text_embed(comps, prompts):
    tok, te = comps["tokenizer"], comps["text_encoder"]
    ids = tok(prompts, padding="max_length", truncation=True, max_length=tok.model_max_length, return_tensors="pt").input_ids
    return te(ids.to(te.device)).last_hidden_state


def add_lora(unet, rank=16, lr=1e-4, name="default"):
    from peft import LoraConfig
    cfg = LoraConfig(r=rank, lora_alpha=rank, target_modules=["to_q", "to_k", "to_v", "to_out.0"], lora_dropout=0.0, bias="none")
    unet.add_adapter(cfg, adapter_name=name)
    params = [p for p in unet.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=lr)
    return opt


def reset_lora(unet):
    try:
        adapters = unet.get_list_adapters()
        names = adapters.get("unet", []) if isinstance(adapters, dict) else list(adapters or [])
    except Exception:
        names = []
    if names:
        try:
            unet.delete_adapters(names)
        except Exception:
            pass
    if hasattr(unet, "peft_config"):
        for n in list(unet.peft_config.keys()):
            unet.peft_config.pop(n, None)
    try:
        from peft.tuners.lora import LoraLayer
        for m in unet.modules():
            if isinstance(m, LoraLayer):
                for k in list(m.lora_A.keys()):
                    del m.lora_A[k]
                    del m.lora_B[k]
                if hasattr(m, "lora_embedding_A"):
                    for k in list(m.lora_embedding_A.keys()):
                        del m.lora_embedding_A[k]
                        del m.lora_embedding_B[k]
    except Exception:
        pass


def dreambooth_loss(comps, images, prompt, t_min=20, t_max=980, jpeg_aware=0):
    vae, unet, sched = comps["vae"], comps["unet"], comps["scheduler"]
    if isinstance(images, (list, tuple)):
        images = images_to_tensor(images, comps["dtype"])
    x = images.to(comps["device"], comps["dtype"])
    if jpeg_aware:
        from ..attack.diffjpeg import diff_jpeg
        x = diff_jpeg((x + 1.0) / 2.0, quality=jpeg_aware) * 2.0 - 1.0
    lat = encode_latents(vae, x)
    noise = torch.randn_like(lat)
    t = torch.randint(t_min, t_max, (lat.shape[0],), device=lat.device)
    noisy = sched.add_noise(lat, noise, t)
    emb = text_embed(comps, [prompt] * lat.shape[0])
    pred = unet(noisy, t, encoder_hidden_states=emb).sample
    return torch.nn.functional.mse_loss(pred.float(), noise.float(), reduction="mean")


def dreambooth_prior_loss(comps, instance_images, class_images, instance_prompt,
                          class_prompt="a photo of person", prior_weight=1.0,
                          t_min=20, t_max=980):
    """DreamBooth instance plus class-prior loss with trainable text encoder."""
    vae, unet, sched = comps["vae"], comps["unet"], comps["scheduler"]
    images = list(instance_images) + list(class_images)
    x = images_to_tensor(images, comps["dtype"]).to(comps["device"])
    with torch.no_grad():
        lat = encode_latents(vae, x)
    noise = torch.randn_like(lat)
    t = torch.randint(t_min, t_max, (lat.shape[0],), device=lat.device)
    noisy = sched.add_noise(lat, noise, t)
    prompts = ([instance_prompt] * len(instance_images) +
               [class_prompt] * len(class_images))
    emb = text_embed(comps, prompts)
    pred = unet(noisy, t, encoder_hidden_states=emb).sample
    n = len(instance_images)
    instance_loss = torch.nn.functional.mse_loss(pred[:n].float(), noise[:n].float())
    prior_loss = torch.nn.functional.mse_loss(pred[n:].float(), noise[n:].float())
    return instance_loss + prior_weight * prior_loss


def build_pipeline(comps):
    pipe = comps["pipeline_factory"]()
    pipe.set_progress_bar_config(disable=True)
    return pipe


@torch.no_grad()
def generate_images(pipe, prompts, n_per_prompt, steps=30, guidance=7.5, seed=0, height=512, width=512):
    out = []
    for pr in prompts:
        g = torch.Generator(device=pipe.device).manual_seed(seed)
        res = pipe([pr] * n_per_prompt, num_inference_steps=steps, guidance_scale=guidance, generator=g, height=height, width=width)
        out.extend(res.images)
    return out
