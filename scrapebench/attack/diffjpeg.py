import torch
import torch.nn.functional as F

_BASIS = {}
_QTABLE = {}


def _dct_basis(device):
    if device not in _BASIS:
        n = torch.arange(8, device=device, dtype=torch.float64)
        k = n.view(-1, 1)
        c = torch.cos((2 * n + 1) * k * torch.pi / 16.0)
        alpha = torch.full((8, 1), 2.0 / 8.0, device=device, dtype=torch.float64).sqrt()
        alpha[0, 0] = torch.sqrt(torch.tensor(1.0 / 8.0, device=device, dtype=torch.float64))
        _BASIS[device] = alpha * c
    return _BASIS[device]


def _quant_table(quality, device):
    if device not in _QTABLE:
        base = torch.tensor([
            [16, 11, 10, 16, 24, 40, 51, 61],
            [12, 12, 14, 19, 26, 58, 60, 55],
            [14, 13, 16, 24, 40, 57, 69, 56],
            [14, 17, 22, 29, 51, 87, 80, 62],
            [18, 22, 37, 56, 68, 109, 103, 77],
            [24, 35, 55, 64, 81, 104, 113, 92],
            [49, 64, 78, 87, 103, 121, 120, 101],
            [72, 92, 95, 98, 112, 100, 103, 99],
        ], dtype=torch.float64)
        _QTABLE[device] = base.to(device)
    scale = 5000.0 / quality if quality < 50 else 200.0 - 2.0 * quality
    return (_QTABLE[device] * scale / 100.0).clamp(1.0, 255.0)


def _blockify(x):
    b, c, h, w = x.shape
    return x.view(b, c, h // 8, 8, w // 8, 8).permute(0, 1, 2, 4, 3, 5).reshape(-1, 8, 8)


def _unblockify(blocks, b, c, h, w):
    x = blocks.view(b, c, h // 8, w // 8, 8, 8).permute(0, 1, 2, 4, 3, 5).reshape(b, c, h, w)
    return x


def dct2(blk, a):
    return torch.matmul(a, torch.matmul(blk, a.t()))


def idct2(coef, a):
    return torch.matmul(a.t(), torch.matmul(coef, a))


def diff_jpeg(x, quality=85):
    b, c, h, w = x.shape
    ph, pw = (8 - h % 8) % 8, (8 - w % 8) % 8
    xp = F.pad(x, (0, pw, 0, ph), mode="reflect") if (ph or pw) else x
    hh, ww = xp.shape[-2:]
    dev = xp.device
    a = _dct_basis(dev).to(xp.dtype)
    q = _quant_table(quality, dev).to(xp.dtype)
    r, g, ch_b = xp[:, 0], xp[:, 1], xp[:, 2]
    y = 0.299 * r + 0.587 * g + 0.114 * ch_b
    cb = 0.5 - 0.168736 * r - 0.331264 * g + 0.5 * ch_b
    cr = 0.5 + 0.5 * r - 0.418688 * g - 0.081312 * ch_b
    recs = []
    for ch in (y.unsqueeze(1), cb.unsqueeze(1), cr.unsqueeze(1)):
        blk = _blockify(ch * 255.0) - 128.0
        coef = dct2(blk, a)
        steps = coef / q
        qh = torch.round(steps)
        steps = steps + (qh - steps).detach()
        rec = idct2(steps * q, a) + 128.0
        recs.append(_unblockify(rec, b, 1, hh, ww) / 255.0)
    y, cb, cr = recs[0][:, 0], recs[1][:, 0], recs[2][:, 0]
    rr = y + 1.402 * (cr - 0.5)
    gg = y - 0.344136 * (cb - 0.5) - 0.714136 * (cr - 0.5)
    bb = y + 1.772 * (cb - 0.5)
    out = torch.stack([rr, gg, bb], dim=1).clamp(0, 1)
    return out[:, :, :h, :w]
