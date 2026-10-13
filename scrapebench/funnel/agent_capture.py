import io
import numpy as np
from PIL import Image, ImageDraw
RESAMPLE_LANCZOS = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
RESAMPLE_BILINEAR = getattr(getattr(Image, "Resampling", Image), "BILINEAR")
from .browser import _canvas_shot, _feed_card

T3_TRANSFORMS = {}
_INSIGHT = {}


def register(names):
    def deco(fn):
        for n in names:
            T3_TRANSFORMS[n] = fn
        return fn
    return deco


def _insight_box(pil_img):
    try:
        from insightface.app import FaceAnalysis
        if "app" not in _INSIGHT:
            app = FaceAnalysis(name="buffalo_l", allowed_modules=["detection"], providers=["CPUExecutionProvider"])
            app.prepare(ctx_id=-1, det_size=(640, 640))
            _INSIGHT["app"] = app
        arr = np.array(pil_img.convert("RGB"))[:, :, ::-1]
        faces = _INSIGHT["app"].get(arr)
        if not faces:
            return None
        b = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1])).bbox
        return (int(b[0]), int(b[1]), int(b[2] - b[0]), int(b[3] - b[1]))
    except Exception:
        return None


def _haar_crop(pil_img, expand=0.35):
    img = np.array(pil_img.convert("RGB"))
    gray = img.mean(axis=2).astype(np.uint8)
    box = None
    try:
        import cv2
        cas = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        faces = cas.detectMultiScale(gray, 1.1, 5, minSize=(24, 24))
        if len(faces):
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            box = (x, y, w, h)
    except Exception:
        box = None
    if box is None:
        box = _insight_box(pil_img)
    W, H = pil_img.size
    if box is None:
        cx, cy, s = W // 2, int(H * 0.45), min(W, H) // 2
    else:
        x, y, w, h = box
        # ``expand`` is a margin on each side of the detected face.  Treating
        # it as the total expansion only leaves 17.5% per side for the
        # protocol's 0.35 setting and crops away landmarks needed by the
        # downstream face detector.
        cx, cy, s = x + w // 2, y + h // 2, int(max(w, h) * (1 + 2 * expand))
    x0, y0 = max(0, cx - s // 2), max(0, cy - s // 2)
    x1, y1 = min(W, x0 + s), min(H, y0 + s)
    return pil_img.crop((x0, y0, x1, y1))


def t3_agent(img, tile_w=300, viewport=(1280, 1600), agent_bar=True, face_crop=True, crop_margin=0.35):
    screen, box = _canvas_shot(img, tile_w, viewport)
    d = ImageDraw.Draw(screen)
    if agent_bar:
        d.rectangle([0, 0, screen.size[0], 56], fill=(30, 30, 34))
        d.rectangle([16, 16, 220, 40], fill=(60, 60, 66))
        d.rectangle([screen.size[0] - 120, 16, screen.size[0] - 16, 40], fill=(60, 60, 66))
    region = screen.crop(box)
    if face_crop:
        region = _haar_crop(region, expand=crop_margin)
    region = region.resize((512, 512), RESAMPLE_LANCZOS)
    buf = io.BytesIO()
    region.save(buf, "WEBP", quality=80)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


@register(["t3_agent_full"])
def _t3_full(img):
    return t3_agent(img, face_crop=False)


@register(["t3_agent_facecrop"])
def _t3_facecrop(img):
    return t3_agent(img, face_crop=True)
