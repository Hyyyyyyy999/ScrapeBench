import io
from PIL import Image
RESAMPLE_LANCZOS = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
RESAMPLE_BILINEAR = getattr(getattr(Image, "Resampling", Image), "BILINEAR")

T1_TRANSFORMS = {}


def register(names):
    def deco(fn):
        for n in names:
            T1_TRANSFORMS[n] = fn
        return fn
    return deco


def jpeg_compress(img, quality):
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=quality, subsampling=2)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def webp_compress(img, quality):
    buf = io.BytesIO()
    img.save(buf, "WEBP", quality=quality)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def resize_to(img, size):
    w, h = img.size
    scale = size / min(w, h)
    return img.resize((max(1, int(w * scale)), max(1, int(h * scale))), RESAMPLE_LANCZOS)


@register(["t1_jpeg95"])
def t1_jpeg95(img):
    return jpeg_compress(resize_to(img, 512), 95)


@register(["t1_jpeg85"])
def t1_jpeg85(img):
    return jpeg_compress(resize_to(img, 512), 85)


@register(["t1_jpeg75"])
def t1_jpeg75(img):
    return jpeg_compress(resize_to(img, 512), 75)


@register(["t1_jpeg70"])
def t1_jpeg70(img):
    """GAP-Diff Table-I compatible platform transcode."""
    return jpeg_compress(resize_to(img, 512), 70)


@register(["t1_jpeg65"])
def t1_jpeg65(img):
    return jpeg_compress(resize_to(img, 512), 65)


@register(["t1_webp80"])
def t1_webp80(img):
    return webp_compress(resize_to(img, 512), 80)


@register(["t1_platform"])
def t1_platform(img):
    img = resize_to(img, 768)
    return jpeg_compress(img, 85)
