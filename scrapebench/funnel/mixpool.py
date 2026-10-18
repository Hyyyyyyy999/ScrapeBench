import random
from pathlib import Path

T6_TRANSFORMS = {}


def register(names):
    def deco(fn):
        for n in names:
            T6_TRANSFORMS[n] = fn
        return fn
    return deco


def build_mixpool(protected_dir, clean_pool_dir, ratio_clean, out_dir, seed=0):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    prot = sorted(Path(protected_dir).glob("*"))
    clean = sorted(Path(clean_pool_dir).glob("*"))
    rng = random.Random(seed)
    k_clean = int(len(prot) * ratio_clean / max(1e-9, 1 - ratio_clean))
    k_clean = min(k_clean, len(clean))
    picked_clean = rng.sample(clean, k_clean) if k_clean else []
    for i, src in enumerate(prot):
        dst = out / f"prot_{i:03d}{src.suffix}"
        dst.write_bytes(src.read_bytes())
    for i, src in enumerate(picked_clean):
        dst = out / f"clean_{i:03d}{src.suffix}"
        dst.write_bytes(src.read_bytes())
    return out, len(prot), len(picked_clean)


@register(["t6_sde50", "t6_diffpure50"])
def t6_diffpure50(img):
    """One-shot SD1.5 reconstruction proxy, applied directly to T0.

    This is not claimed to reproduce the official DiffPure classifier-defense
    implementation. It is a deterministic, prompt-free img2img reconstruction
    at strength .50, representative of an attacker-side diffusion purifier.
    """
    from .regenerate import _get_regen
    return _get_regen().i2i([img], strength=0.5, steps=50, guidance=1.0, seed=0, prompt="")[0]


@register(["t6_sde30"])
def t6_sde30(img):
    """Clean-calibration candidate; never selected using defense outcomes."""
    from .regenerate import _get_regen
    return _get_regen().i2i([img], strength=0.30, steps=50, guidance=1.0, seed=0, prompt="")[0]


@register(["t6_sde35"])
def t6_sde35(img):
    """Clean-calibration candidate; never selected using defense outcomes."""
    from .regenerate import _get_regen
    return _get_regen().i2i([img], strength=0.35, steps=50, guidance=1.0, seed=0, prompt="")[0]


@register(["t6_sde40"])
def t6_sde40(img):
    """Clean-calibration candidate; never selected using defense outcomes."""
    from .regenerate import _get_regen
    return _get_regen().i2i([img], strength=0.40, steps=50, guidance=1.0, seed=0, prompt="")[0]
