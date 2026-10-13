import random
import torch
import torch.nn.functional as F
from .base import pil_to_tensor, tensor_to_pil, clamp_eps
from .fsmg import text_embed, encode_latents, CLASS_PROMPT
from ..attack.diffjpeg import diff_jpeg

_FN = {}


def _fn(device, dtype):
    if "m" not in _FN:
        from facenet_pytorch import InceptionResnetV1
        m = InceptionResnetV1(pretrained="vggface2").eval().requires_grad_(False)
        _FN["m"] = m.to(device)
    return _FN["m"].to(dtype)


def _fn_emb(model, x):
    x01 = (x + 1.0) / 2.0
    x160 = F.interpolate(x01, size=(160, 160), mode="bicubic", align_corners=False)
    x160 = (x160 - 0.5) / 0.5
    return model(x160)


def _jnd_amp(x01, eps_min, eps_max):
    g = x01.mean(1, keepdim=True)
    kx = torch.tensor([[1.0, 0.0, -1.0], [2.0, 0.0, -2.0], [1.0, 0.0, -1.0]], device=x01.device, dtype=x01.dtype).view(1, 1, 3, 3)
    ky = kx.transpose(2, 3)
    gx = F.conv2d(g, kx, padding=1)
    gy = F.conv2d(g, ky, padding=1)
    e = torch.sqrt(gx * gx + gy * gy + 1e-12)
    tex = F.avg_pool2d(e, 9, stride=1, padding=4)
    q = torch.quantile(tex.float().flatten(1), 0.95, dim=1).view(-1, 1, 1, 1)
    tex = (tex / (q.to(tex.dtype) + 1e-8)).clamp(0.0, 1.0)
    return eps_min + (eps_max - eps_min) * tex


def _p_jpeg(x, rng):
    return diff_jpeg(x, quality=rng.uniform(65, 95))


def _p_resize(x, rng):
    n = max(32, int(512 * rng.uniform(0.35, 1.0)))
    d = F.interpolate(x, size=(n, n), mode="bicubic", align_corners=False)
    return F.interpolate(d, size=(512, 512), mode="bicubic", align_corners=False)


def _p_sr(x, rng):
    d = F.interpolate(x, scale_factor=0.5, mode="bicubic", align_corners=False)
    u = F.interpolate(d, size=(512, 512), mode="bicubic", align_corners=False)
    b = F.avg_pool2d(u, 3, stride=1, padding=1)
    return u + 1.5 * (u - b)


def _p_crop(x, rng):
    f = rng.uniform(0.7, 1.0)
    h = int(512 * f)
    y = rng.randint(0, 512 - h)
    xx = rng.randint(0, 512 - h)
    c = x[:, :, y:y + h, xx:xx + h]
    return F.interpolate(c, size=(512, 512), mode="bicubic", align_corners=False)


PIX_PROXIES = [_p_jpeg, _p_resize, _p_sr, _p_crop]


def _eot(x, rng, n_comp=2):
    out = x
    for fn in rng.sample(PIX_PROXIES, n_comp):
        out = fn(out, rng)
    return out


def forge_arcp(comps, imgs, out_dir=None, eps_max=16.0 / 255.0, eps_min=2.0 / 255.0,
               steps=150, alpha=2.0 / 255.0, lam=0.5, margin=0.4, grid=64, seed=0,
               rng=None):
    device, dtype = comps["device"], comps["dtype"]
    vae, unet, sched = comps["vae"], comps["unet"], comps["scheduler"]
    rng = rng or random.Random(seed)
    x = pil_to_tensor(imgs, device, dtype)
    n = x.shape[0]
    x01 = (x + 1.0) / 2.0
    amp = _jnd_amp(x01, eps_min, eps_max)
    amp_low = F.interpolate(amp, size=(grid, grid), mode="area")
    amp_up = F.interpolate(amp_low, size=(512, 512), mode="bilinear", align_corners=False)
    z = torch.zeros(n, 3, grid, grid, device=device, dtype=dtype)
    z.requires_grad_(True)
    emb = text_embed(comps, [CLASS_PROMPT] * n)
    with torch.no_grad():
        ref = _fn_emb(_fn(device, dtype), x).mean(0, keepdim=True)
        ref = ref / ref.norm(dim=-1, keepdim=True)
    for step in range(steps):
        delta = F.interpolate(z, size=(512, 512), mode="bilinear", align_corners=False) * amp_up
        xp = clamp_eps(x + delta, x, eps_max)
        xa = _eot(xp, rng)
        e = _fn_emb(_fn(device, dtype), xa)
        e = e / e.norm(dim=-1, keepdim=True)
        sim = (e * ref).sum(-1)
        loss_reader = F.relu(sim - margin).mean()
        lat = encode_latents(vae, xa)
        if rng.random() < 0.5:
            t = torch.randint(300, 500, (n,), device=device)
        else:
            t = torch.randint(20, 980, (n,), device=device)
        noise = torch.randn(lat.shape, device=device, dtype=dtype)
        noisy = sched.add_noise(lat, noise, t)
        pred = unet(noisy, t, encoder_hidden_states=emb).sample
        loss_ft = torch.nn.functional.mse_loss(pred.float(), noise.float(), reduction="mean")
        obj = loss_ft - lam * loss_reader
        grad, = torch.autograd.grad(obj, z)
        with torch.no_grad():
            z.add_(alpha * grad.sign())
            z.clamp_(-1.0, 1.0)
        z.requires_grad_(True)
        if (step + 1) % 50 == 0:
            print(f"[arcp] step {step + 1}/{steps} ft {loss_ft.item():.4f} reader {loss_reader.item():.4f}", flush=True)
    with torch.no_grad():
        delta = F.interpolate(z, size=(512, 512), mode="bilinear", align_corners=False) * amp_up
        out = clamp_eps(x + delta, x, eps_max)
    outs = tensor_to_pil(out)
    if out_dir is not None:
        import os
        os.makedirs(out_dir, exist_ok=True)
        for i, im in enumerate(outs):
            im.save(os.path.join(out_dir, f"{i:04d}.png"))
    return outs
