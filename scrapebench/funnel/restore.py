import io
import os
from pathlib import Path
from PIL import Image, ImageFilter
RESAMPLE_LANCZOS = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
RESAMPLE_BILINEAR = getattr(getattr(Image, "Resampling", Image), "BILINEAR")
from .transcode import jpeg_compress

T4_TRANSFORMS = {}


def register(names):
    def deco(fn):
        for n in names:
            T4_TRANSFORMS[n] = fn
        return fn
    return deco


_UPSAMPLERS = {}


def _realesrgan_upscale(img, scale=2, model_path=None):
    # BasicSR 1.4.2 imports torchvision's pre-0.17 module name. Torchvision
    # 0.22 keeps the implementation under a private renamed module.
    import sys
    if "torchvision.transforms.functional_tensor" not in sys.modules:
        import torchvision.transforms._functional_tensor as functional_tensor
        sys.modules["torchvision.transforms.functional_tensor"] = functional_tensor
    from basicsr.archs.rrdbnet_arch import RRDBNet
    from realesrgan import RealESRGANer
    import numpy as np
    if scale not in _UPSAMPLERS:
        # The official x2 checkpoint uses RRDBNet's pixel-unshuffle x2 stem
        # (12 input channels), so both architecture and runner must use scale=2.
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=scale)
        _UPSAMPLERS[scale] = RealESRGANer(scale=scale, model_path=model_path, model=model, tile=256, half=True)
    # RealESRGANer follows OpenCV and expects/returns BGR arrays. Passing a PIL
    # RGB array directly silently swaps red and blue and corrupts conditioning.
    arr_bgr = np.array(img.convert("RGB"))[:, :, ::-1]
    out_bgr, _ = _UPSAMPLERS[scale].enhance(arr_bgr, outscale=scale)
    return Image.fromarray(out_bgr[:, :, ::-1])


def t4_restore(img, scale=2, engine="auto"):
    if engine in ("auto", "realesrgan"):
        try:
            if "path" not in _UPSAMPLERS:
                local = Path(__file__).resolve().parents[2] / "weights" / "RealESRGAN_x2_params.pth"
                if not local.exists():
                    raise FileNotFoundError(f"wrapped Real-ESRGAN checkpoint missing: {local}")
                _UPSAMPLERS["path"] = str(local)
            out = _realesrgan_upscale(img, scale, _UPSAMPLERS["path"])
            return jpeg_compress(out, 92)
        except Exception as exc:
            # A benchmark row labelled Real-ESRGAN must never silently become
            # bicubic sharpening because a weight or dependency is missing.
            raise RuntimeError(f"T4 Real-ESRGAN failed: {exc}") from exc
    w, h = img.size
    up = img.resize((w * scale, h * scale), RESAMPLE_LANCZOS)
    up = up.filter(ImageFilter.UnsharpMask(radius=2, percent=80, threshold=2))
    return jpeg_compress(up, 92)


@register(["t4_sr_x2"])
def _t4(img):
    return t4_restore(img, scale=2)
