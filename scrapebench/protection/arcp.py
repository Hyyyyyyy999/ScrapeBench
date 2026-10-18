import math
import random
import numpy as np
from PIL import Image
import torch
import torch.nn.functional as F
from .base import pil_to_tensor, tensor_to_pil, clamp_eps
from .fsmg import text_embed, encode_latents, CLASS_PROMPT
from ..attack.diffjpeg import diff_jpeg

_FN = {}
_ARC = {}


def _arcface(device):
    """Differentiable copy of InstantID's released antelopev2 recognizer."""
    if "m" not in _ARC:
        import os
        import onnx
        from onnx2torch import convert
        path = os.environ.get(
            "SCRAPEBENCH_ARCFACE_ONNX",
            "/mnt/beegfs/home/huangyue26/IDProtector/generation_methods/InstantID/models/antelopev2/glintr100.onnx",
        )
        if not os.path.isfile(path):
            raise FileNotFoundError(f"ARCP ArcFace checkpoint missing: {path}")
        _ARC["m"] = convert(onnx.load(path)).eval().requires_grad_(False)
    return _ARC["m"].to(device=device, dtype=torch.float32)


def _arcface_grids(imgs, device):
    """Detect once on clean inputs, then keep alignment differentiable.

    The detector itself need not be differentiated: the threat model fixes the
    clean face geometry and differentiates the ArcFace recognition path.  The
    returned grid maps a 112x112 ArcFace canvas into each 512x512 input.
    """
    import cv2
    import os
    from insightface.app import FaceAnalysis
    if "app" not in _ARC:
        root = os.environ.get(
            "SCRAPEBENCH_ANTELOPE_ROOT",
            "/mnt/beegfs/home/huangyue26/IDProtector/generation_methods/InstantID",
        )
        app = FaceAnalysis(name="antelopev2", root=root, providers=["CPUExecutionProvider"])
        app.prepare(ctx_id=-1, det_size=(640, 640))
        _ARC["app"] = app
    dst = np.array([[38.2946, 51.6963], [73.5318, 51.5014],
                    [56.0252, 71.7366], [41.5493, 92.3655],
                    [70.7299, 92.2041]], dtype=np.float32)
    yy, xx = np.meshgrid(np.arange(112, dtype=np.float32),
                         np.arange(112, dtype=np.float32), indexing="ij")
    target = np.stack((xx, yy, np.ones_like(xx)), axis=-1).reshape(-1, 3).T
    grids = []
    for image in imgs:
        arr = np.asarray(image.convert("RGB").resize((512, 512)))[:, :, ::-1]
        faces = _ARC["app"].get(arr)
        if not faces:
            # Audited inputs should never take this branch; retain a visible,
            # deterministic fallback so a failed detector cannot crash a job.
            matrix = np.array([[112 / 512, 0, 0], [0, 112 / 512, 0]], dtype=np.float32)
        else:
            face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
            matrix, _ = cv2.estimateAffinePartial2D(np.asarray(face.kps, np.float32), dst,
                                                    method=cv2.LMEDS)
            if matrix is None:
                raise RuntimeError("could not estimate ArcFace alignment")
        inverse = np.linalg.inv(np.vstack((matrix, [0, 0, 1])))
        source = inverse @ target
        gx = source[0].reshape(112, 112) / 511.0 * 2.0 - 1.0
        gy = source[1].reshape(112, 112) / 511.0 * 2.0 - 1.0
        grids.append(np.stack((gx, gy), axis=-1))
    return torch.as_tensor(np.stack(grids), device=device, dtype=torch.float32)


def _arc_emb(model, x, grids):
    if x.shape[0] != grids.shape[0]:
        if x.shape[0] % grids.shape[0] != 0:
            raise ValueError("ArcFace grid batch does not divide image batch")
        grids = grids.repeat(x.shape[0] // grids.shape[0], 1, 1, 1)
    aligned = F.grid_sample(x.float(), grids, mode="bilinear", padding_mode="border",
                            align_corners=True)
    return model(aligned)


def _fn(device, dtype):
    if "m" not in _FN:
        from facenet_pytorch import InceptionResnetV1
        m = InceptionResnetV1(pretrained="vggface2").eval().requires_grad_(False)
        _FN["m"] = m.to(device)
    return _FN["m"].to(dtype)


def _fn_emb(model, x, multiview=False):
    x01 = (x + 1.0) / 2.0
    x160 = F.interpolate(x01, size=(160, 160), mode="bicubic", align_corners=False)
    x160 = (x160 - 0.5) / 0.5
    full = model(x160)
    if not multiview:
        return full
    # Web readers normally detect/crop a face before recognition.  The old
    # ARCP optimized only a squeezed full frame, which left a large surrogate
    # mismatch.  Concatenating full-frame and central-face features keeps the
    # objective differentiable while covering both reader conventions.
    h, w = x.shape[-2:]
    side = int(min(h, w) * 0.75)
    top, left = (h - side) // 2, (w - side) // 2
    face = x01[:, :, top:top + side, left:left + side]
    face = F.interpolate(face, size=(160, 160), mode="bicubic", align_corners=False)
    face = model((face - 0.5) / 0.5)
    return torch.cat((F.normalize(full, dim=-1), F.normalize(face, dim=-1)), dim=-1) / math.sqrt(2.0)


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
    # diff_jpeg consumes [0,1], whereas ARCP tensors use [-1,1]. The previous
    # implementation mixed these domains and optimized against clipped images.
    return diff_jpeg((x + 1.0) / 2.0, quality=rng.uniform(65, 95)) * 2.0 - 1.0


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


def _p_identity(x, rng):
    return x


def _p_jpeg70(x, rng):
    return diff_jpeg((x + 1.0) / 2.0, quality=70) * 2.0 - 1.0


def _p_canvas360(x, rng):
    down = F.interpolate(x, size=(360, 360), mode="bicubic", align_corners=False)
    return F.interpolate(down, size=(512, 512), mode="bicubic", align_corners=False)


def _p_agent_crop(x, rng):
    # Differentiable center proxy for detector-guided face crop. Random jitter
    # prevents the optimization from depending on one exact crop window.
    side = 384
    jitter = 24
    top = 64 + rng.randint(-jitter, jitter)
    left = 64 + rng.randint(-jitter, jitter)
    crop = x[:, :, top:top + side, left:left + side]
    return F.interpolate(crop, size=(512, 512), mode="bicubic", align_corners=False)


def _p_regen30(x, rng):
    # Low-pass/bottleneck proxy for a mild img2img round trip. The exact T5
    # pipeline remains an unseen evaluation transform.
    small = F.interpolate(x, size=(256, 256), mode="bilinear", align_corners=False)
    rec = F.interpolate(small, size=(512, 512), mode="bilinear", align_corners=False)
    rec = F.avg_pool2d(rec, 3, stride=1, padding=1)
    return 0.7 * x + 0.3 * rec


def _p_purify50(x, rng):
    # Stronger low-pass proxy for diffusion reconstruction/purification.
    small = F.interpolate(x, size=(192, 192), mode="bilinear", align_corners=False)
    rec = F.interpolate(small, size=(512, 512), mode="bilinear", align_corners=False)
    return F.avg_pool2d(rec, 5, stride=1, padding=2)


WEB_PROXIES = [
    ("T0", _p_identity),
    ("T1", _p_jpeg70),
    ("T2", _p_canvas360),
    ("T3", _p_agent_crop),
    ("T4", _p_sr),
    ("T5", _p_regen30),
    ("T6", _p_purify50),
]


def _eot(x, rng, n_comp=2):
    out = x
    for fn in rng.sample(PIX_PROXIES, n_comp):
        out = fn(out, rng)
    return out


def forge_arcp(comps, imgs, out_dir=None, eps_max=16.0 / 255.0, eps_min=2.0 / 255.0,
               steps=150, alpha=2.0 / 255.0, lam=0.5, margin=0.4, grid=64, seed=0,
               rng=None, pixel_space=False, random_start=False, eot_depth=2,
               balanced_web=False, survival_weight=0.10, gap_margin=0.15,
               reader_softplus_beta=0.0, detail_grid=0, detail_weight=0.0,
               dual_t0=False, t0_weight=1.0, reader_multiview=False,
               arcface_weight=0.0):
    device, dtype = comps["device"], comps["dtype"]
    vae, unet, sched = comps["vae"], comps["unet"], comps["scheduler"]
    rng = rng or random.Random(seed)
    tgen = torch.Generator(device=device).manual_seed(seed)
    x = pil_to_tensor(imgs, device, dtype)
    n = x.shape[0]
    x01 = (x + 1.0) / 2.0
    # ``x`` is in [-1, 1].  New experiments specify epsilon in conventional
    # [0, 1] pixel units, hence the factor of two.  ``pixel_space=False`` is
    # retained solely to reproduce the frozen legacy ARCP pilot.
    scale = 2.0 if pixel_space else 1.0
    eps_max_model = eps_max * scale
    eps_min_model = eps_min * scale
    amp = _jnd_amp(x01, eps_min_model, eps_max_model)
    amp_low = F.interpolate(amp, size=(grid, grid), mode="area")
    amp_up = F.interpolate(amp_low, size=(512, 512), mode="bilinear", align_corners=False)
    if random_start:
        z = torch.empty(n, 3, grid, grid, device=device, dtype=dtype).uniform_(-1.0, 1.0)
    else:
        z = torch.zeros(n, 3, grid, grid, device=device, dtype=dtype)
    z.requires_grad_(True)
    z_detail = None
    if detail_grid and detail_weight > 0:
        if random_start:
            z_detail = torch.empty(n, 3, detail_grid, detail_grid, device=device, dtype=dtype).uniform_(-1.0, 1.0)
        else:
            z_detail = torch.zeros(n, 3, detail_grid, detail_grid, device=device, dtype=dtype)
        z_detail.requires_grad_(True)

    def compose_delta():
        low = F.interpolate(z, size=(512, 512), mode="bilinear", align_corners=False)
        if z_detail is None:
            return low * amp_up
        detail = F.interpolate(z_detail, size=(512, 512), mode="bilinear", align_corners=False)
        # A convex mixture preserves the same per-pixel JND/L_inf envelope.
        return ((1.0 - detail_weight) * low + detail_weight * detail) * amp_up

    def reader_violation(similarity, clean_similarity):
        violations = [similarity - margin, similarity - clean_similarity.detach() + gap_margin]
        if reader_softplus_beta > 0:
            beta = float(reader_softplus_beta)
            return sum(F.softplus(beta * v) / beta for v in violations).mean()
        return sum(F.relu(v) for v in violations).mean()

    emb = text_embed(comps, [CLASS_PROMPT] * n)
    with torch.no_grad():
        ref = _fn_emb(_fn(device, dtype), x, multiview=reader_multiview).mean(0, keepdim=True)
        ref = ref / ref.norm(dim=-1, keepdim=True)
    arc_model = _arcface(device) if arcface_weight > 0 else None
    arc_grids = _arcface_grids(imgs, device) if arcface_weight > 0 else None
    if arc_model is not None:
        with torch.no_grad():
            arc_ref = F.normalize(_arc_emb(arc_model, x, arc_grids), dim=-1).mean(0, keepdim=True)
            arc_ref = F.normalize(arc_ref, dim=-1)
    # EMA of the paired clean-minus-protected identity gap.  A small gap means
    # the intervention is currently a weak point. NaN marks an unseen layer.
    proxy_gap_ema = torch.full((len(WEB_PROXIES),), float("nan"), dtype=torch.float32)
    for step in range(steps):
        delta = compose_delta()
        # ARCP is a self-contained clean-to-protected method.  No baseline
        # protection image is used as initialization or as part of the loss.
        xp = clamp_eps(x + delta, x, eps_max_model).clamp(-1.0, 1.0)
        if balanced_web:
            # Half the updates cover T0--T6 uniformly; the interleaved half
            # revisits the currently weakest intervention (smallest paired
            # clean-minus-protected identity gap). Using a paired gap is
            # essential: reconstruction may reduce identity in both branches,
            # so absolute protected similarity would select the wrong layer.
            if step % 2 == 0:
                proxy_idx = (step // 2) % len(WEB_PROXIES)
            else:
                seen = torch.where(~torch.isnan(proxy_gap_ema))[0]
                proxy_idx = int(seen[torch.argmin(proxy_gap_ema[seen])])
            proxy_name, proxy_fn = WEB_PROXIES[proxy_idx]
            # Concatenate protected and clean inputs so stochastic crop
            # parameters are identical for the paired survival objective.
            paired = proxy_fn(torch.cat((xp, x), dim=0), rng)
            xa, clean_a = paired[:n], paired[n:2 * n]
        else:
            proxy_name = "EOT"
            xa = _eot(xp, rng, n_comp=eot_depth)
            clean_a = None
        e = _fn_emb(_fn(device, dtype), xa, multiview=reader_multiview)
        e = e / e.norm(dim=-1, keepdim=True)
        sim = (e * ref).sum(-1)
        if balanced_web:
            with torch.no_grad():
                clean_e = _fn_emb(_fn(device, dtype), clean_a, multiview=reader_multiview)
                clean_e = clean_e / clean_e.norm(dim=-1, keepdim=True)
                clean_sim = (clean_e * ref).sum(-1)
            paired_gap = (clean_sim - sim.detach()).float().mean().cpu()
            old_gap = proxy_gap_ema[proxy_idx]
            proxy_gap_ema[proxy_idx] = paired_gap if torch.isnan(old_gap) else 0.9 * old_gap + 0.1 * paired_gap
            # Require a positive identity gap relative to the matched clean
            # branch, while retaining the absolute identity-repulsion term.
            loss_reader = reader_violation(sim, clean_sim)
            if arc_model is not None:
                arc_e = F.normalize(_arc_emb(arc_model, xa, arc_grids), dim=-1)
                with torch.no_grad():
                    clean_arc_e = F.normalize(_arc_emb(arc_model, clean_a, arc_grids), dim=-1)
                    clean_arc_sim = (clean_arc_e * arc_ref).sum(-1)
                arc_sim = (arc_e * arc_ref).sum(-1)
                loss_reader = loss_reader + arcface_weight * reader_violation(arc_sim, clean_arc_sim)
            # Every transformed step also attacks the unprocessed reader.
            # This prevents Web robustness from being bought by giving up T0,
            # which was the main failure of ARCP-Web-v2.
            if dual_t0 and proxy_idx != 0:
                direct_e = _fn_emb(_fn(device, dtype), xp, multiview=reader_multiview)
                direct_e = direct_e / direct_e.norm(dim=-1, keepdim=True)
                direct_sim = (direct_e * ref).sum(-1)
                with torch.no_grad():
                    direct_clean = _fn_emb(_fn(device, dtype), x, multiview=reader_multiview)
                    direct_clean = direct_clean / direct_clean.norm(dim=-1, keepdim=True)
                    direct_clean_sim = (direct_clean * ref).sum(-1)
                direct_gap = (direct_clean_sim - direct_sim.detach()).float().mean().cpu()
                old_t0 = proxy_gap_ema[0]
                proxy_gap_ema[0] = direct_gap if torch.isnan(old_t0) else 0.9 * old_t0 + 0.1 * direct_gap
                loss_reader = loss_reader + t0_weight * reader_violation(direct_sim, direct_clean_sim)
                if arc_model is not None:
                    direct_arc = F.normalize(_arc_emb(arc_model, xp, arc_grids), dim=-1)
                    with torch.no_grad():
                        clean_direct_arc = F.normalize(_arc_emb(arc_model, x, arc_grids), dim=-1)
                        clean_direct_arc_sim = (clean_direct_arc * arc_ref).sum(-1)
                    direct_arc_sim = (direct_arc * arc_ref).sum(-1)
                    loss_reader = loss_reader + t0_weight * arcface_weight * reader_violation(
                        direct_arc_sim, clean_direct_arc_sim)
        else:
            loss_reader = F.relu(sim - margin).mean()
        lat = encode_latents(vae, xa)
        if rng.random() < 0.5:
            t = torch.randint(300, 500, (n,), device=device, generator=tgen)
        else:
            t = torch.randint(20, 980, (n,), device=device, generator=tgen)
        noise = torch.randn(lat.shape, device=device, dtype=dtype, generator=tgen)
        noisy = sched.add_noise(lat, noise, t)
        pred = unet(noisy, t, encoder_hidden_states=emb).sample
        loss_ft = torch.nn.functional.mse_loss(pred.float(), noise.float(), reduction="mean")
        survival = ((xa - clean_a) ** 2).mean() if clean_a is not None else torch.zeros((), device=device)
        obj = loss_ft - lam * loss_reader + survival_weight * survival
        params = [z] + ([z_detail] if z_detail is not None else [])
        grads = torch.autograd.grad(obj, params)
        with torch.no_grad():
            z.add_(alpha * grads[0].sign())
            z.clamp_(-1.0, 1.0)
            if z_detail is not None:
                z_detail.add_(alpha * grads[1].sign())
                z_detail.clamp_(-1.0, 1.0)
        z.requires_grad_(True)
        if z_detail is not None:
            z_detail.requires_grad_(True)
        if (step + 1) % 50 == 0:
            gaps = ",".join("--" if torch.isnan(v) else f"{v:.3f}" for v in proxy_gap_ema)
            print(f"[arcp] step {step + 1}/{steps} proxy={proxy_name} ft={loss_ft.item():.4f} reader={loss_reader.item():.4f} survive={survival.item():.6f} gaps=[{gaps}]", flush=True)
    with torch.no_grad():
        delta = compose_delta()
        out = clamp_eps(x + delta, x, eps_max_model).clamp(-1.0, 1.0)
    outs = tensor_to_pil(out)
    # Enforce the declared budget after 8-bit quantization.  Floating-point
    # projection alone allowed a one-level 17/255 overshoot when both clean
    # and protected tensors were rounded to PNG.
    eps_px = int(math.floor(eps_max * 255.0 + 1e-6))
    projected = []
    for clean_im, protected_im in zip(imgs, outs):
        clean_np = np.asarray(clean_im.convert("RGB"), dtype=np.int16)
        protected_np = np.asarray(protected_im.convert("RGB"), dtype=np.int16)
        protected_np = np.minimum(np.maximum(protected_np, clean_np - eps_px), clean_np + eps_px)
        projected.append(Image.fromarray(np.clip(protected_np, 0, 255).astype(np.uint8), mode="RGB"))
    outs = projected
    if out_dir is not None:
        import os
        os.makedirs(out_dir, exist_ok=True)
        for i, im in enumerate(outs):
            im.save(os.path.join(out_dir, f"{i:04d}.png"))
    return outs
