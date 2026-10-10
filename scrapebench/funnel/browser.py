import base64
import io
import os
import tempfile
from PIL import Image, ImageDraw
RESAMPLE_LANCZOS = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
RESAMPLE_BILINEAR = getattr(getattr(Image, "Resampling", Image), "BILINEAR")

T2_TRANSFORMS = {}

_TILE_W = 360
_CARD_PAD = 12
_HEADER = 44


def register(names):
    def deco(fn):
        for n in names:
            T2_TRANSFORMS[n] = fn
        return fn
    return deco


def _feed_card(img, tile_w=_TILE_W):
    w, h = img.size
    scale = tile_w / w
    thumb = img.resize((tile_w, max(1, int(h * scale))), RESAMPLE_LANCZOS)
    card_w = tile_w + 2 * _CARD_PAD
    card_h = _HEADER + thumb.size[1] + 56
    card = Image.new("RGB", (card_w, card_h), (255, 255, 255))
    d = ImageDraw.Draw(card)
    d.rectangle([0, 0, card_w, _HEADER - 8], fill=(245, 245, 245))
    d.ellipse([_CARD_PAD, 6, _CARD_PAD + 24, 30], fill=(200, 200, 200))
    d.rectangle([_CARD_PAD + 32, 12, _CARD_PAD + 32 + 90, 24], fill=(210, 210, 210))
    card.paste(thumb, (_CARD_PAD, _HEADER))
    d.rectangle([_CARD_PAD, _HEADER + thumb.size[1] + 16, _CARD_PAD + 60, _HEADER + thumb.size[1] + 30], fill=(230, 230, 230))
    d.rectangle([card_w - 80, _HEADER + thumb.size[1] + 16, card_w - _CARD_PAD, _HEADER + thumb.size[1] + 30], fill=(230, 230, 230))
    return card, (tile_w, thumb.size[1])


def _canvas_shot(img, tile_w, viewport_css):
    card, thumb_size = _feed_card(img, tile_w)
    vw, vh = viewport_css
    screen = Image.new("RGB", (vw, vh), (18, 18, 18))
    x = (vw - card.size[0]) // 2
    y = 24
    screen.paste(card, (x, y))
    img_box = (x + _CARD_PAD, y + _HEADER, x + _CARD_PAD + thumb_size[0], y + _HEADER + thumb_size[1])
    return screen, img_box


def _data_uri(img):
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _playwright_shot(img, tile_w, viewport_css, dpr):
    from playwright.sync_api import sync_playwright
    card, thumb = _feed_card(img, tile_w)
    vw, vh = viewport_css
    html = f"""
    <html><body style="margin:0;background:#121212;font-family:sans-serif">
    <div style="width:{card.size[0]}px;margin:24px auto;background:#fff;border-radius:8px;overflow:hidden">
      <div style="height:{_HEADER - 8}px;background:#f5f5f5"></div>
      <img src="{_data_uri(card.crop((0, _HEADER, card.size[0], card.size[1])))}" style="display:block;width:100%">
      <div style="height:56px"></div>
    </div></body></html>
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": vw, "height": vh}, device_scale_factor=dpr)
        page.set_content(html, wait_until="load")
        page.wait_for_timeout(120)
        png = page.screenshot(type="png")
        browser.close()
    shot = Image.open(io.BytesIO(png)).convert("RGB")
    sx = shot.size[0] / vw
    sy = shot.size[1] / vh
    box = ((24 + _CARD_PAD) * sx, (24 + _HEADER) * sy, (24 + _CARD_PAD + tile_w) * sx, (24 + _HEADER + thumb[1]) * sy)
    return shot.crop(tuple(int(v) for v in box))


def t2_browser(img, tile_w=_TILE_W, viewport=(1080, 1400), dpr=1):
    try:
        return _playwright_shot(img, tile_w, viewport, dpr)
    except Exception:
        pass
    return t2_canvas(img, tile_w=tile_w, viewport=viewport, dpr=dpr)


def t2_canvas(img, tile_w=_TILE_W, viewport=(1080, 1400), dpr=1):
    screen, box = _canvas_shot(img, tile_w, viewport)
    if dpr != 1:
        screen = screen.resize((int(screen.size[0] * dpr), int(screen.size[1] * dpr)), RESAMPLE_BILINEAR)
        box = tuple(v * dpr for v in box)
    return screen.crop(tuple(int(v) for v in box))


@register(["t2_browser_dpr1"])
def _t2_dpr1(img):
    return t2_browser(img, dpr=1)


@register(["t2_browser_dpr2"])
def _t2_dpr2(img):
    return t2_browser(img, dpr=2)


@register(["t2_canvas_dpr1"])
def _t2c_dpr1(img):
    return t2_canvas(img, dpr=1)


@register(["t2_canvas_dpr2"])
def _t2c_dpr2(img):
    return t2_canvas(img, dpr=2)


@register(["t2_thumb_small"])
def _t2_small(img):
    return t2_browser(img, tile_w=240, viewport=(720, 900), dpr=1)
