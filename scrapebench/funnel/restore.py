import io
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
    from basicsr.archs.rrdbnet_arch import RRDBNet
    from realesrgan import RealESRGANer
    import numpy as np
    if scale not in _UPSAMPLERS:
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
        _UPSAMPLERS[scale] = RealESRGANer(scale=4, model_path=model_path, model=model, tile=256, half=True)
    arr = np.array(img.convert("RGB"))
    out, _ = _UPSAMPLERS[scale].enhance(arr, outscale=scale)
    return Image.fromarray(out)


def t4_restore(img, scale=2, engine="auto"):
    if engine in ("auto", "realesrgan"):
        try:
            if "path" not in _UPSAMPLERS:
                from huggingface_hub import hf_hub_download
                _UPSAMPLERS["path"] = hf_hub_download("ai-forever/Real-ESRGAN", "RealESRGAN_x2.pth")
            out = _realesrgan_upscale(img, scale, _UPSAMPLERS["path"])
            return jpeg_compress(out, 92)
        except Exception:
            pass
    w, h = img.size
    up = img.resize((w * scale, h * scale), RESAMPLE_LANCZOS)
    up = up.filter(ImageFilter.UnsharpMask(radius=2, percent=80, threshold=2))
    return jpeg_compress(up, 92)


@register(["t4_sr_x2"])
def _t4(img):
    return t4_restore(img, scale=2)
