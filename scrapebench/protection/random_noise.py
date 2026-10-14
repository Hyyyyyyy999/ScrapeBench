import numpy as np
from PIL import Image


def make_random_noise(imgs, eps=8.0 / 255.0, seed=0):
    """Additive uniform-noise control.

    ``eps`` is applied on the ``[0, 1]`` pixel scale, i.e. ``eps = 16/255``
    allows +-16 gray levels -- twice the amplitude of the FSMG/FSMG-J/ASPL/
    ARCP defenses, whose ``eps`` is enforced on the ``[-1, 1]`` Stable
    Diffusion pipeline scale (+-8 gray levels at the same nominal value).
    ``random_eps`` in the protection config sets this amplitude explicitly;
    it falls back to ``eps`` so legacy configs reproduce the frozen galleries.
    """
    rng = np.random.default_rng(seed)
    out = []
    for im in imgs:
        arr = np.asarray(im.convert("RGB"), dtype=np.float32) / 255.0
        arr = arr + rng.uniform(-eps, eps, size=arr.shape)
        out.append(Image.fromarray((arr * 255.0).clip(0, 255).astype(np.uint8)))
    return out
