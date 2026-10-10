import torch
import numpy as np
from PIL import Image


def psnr(a, b):
    a = np.asarray(a.convert("RGB"), dtype=np.float64)
    b = np.asarray(b.convert("RGB"), dtype=np.float64)
    if a.shape != b.shape:
        b = np.array(Image.fromarray(b.astype(np.uint8)).resize((a.shape[1], a.shape[0])))
    mse = np.mean((a - b) ** 2)
    if mse <= 0:
        return float("inf")
    return 10.0 * np.log10(255.0 ** 2 / mse)


def kid_from_features(f1, f2, subsets=10, max_size=1000, rng=None):
    rng = rng or np.random.default_rng(0)
    f1 = np.asarray(f1, dtype=np.float64)
    f2 = np.asarray(f2, dtype=np.float64)
    n = min(len(f1), len(f2), max_size)
    if n < 4:
        return float("nan"), float("nan")
    vals = []
    for _ in range(subsets):
        i1 = rng.choice(len(f1), n, replace=False)
        i2 = rng.choice(len(f2), n, replace=False)
        x, y = f1[i1], f2[i2]
        d_xx = _sq_dist(x, x)
        d_yy = _sq_dist(y, y)
        d_xy = _sq_dist(x, y)
        vals.append(_mmd2(d_xx, d_yy, d_xy))
    vals = np.array(vals)
    return float(vals.mean()), float(vals.std() / max(1, np.sqrt(len(vals))))


def _sq_dist(a, b):
    aa = (a * a).sum(1)[:, None]
    bb = (b * b).sum(1)[None, :]
    d = aa + bb - 2.0 * (a @ b.T)
    return np.maximum(d, 0) / (a.shape[1])


def _mmd2(d_xx, d_yy, d_xy, sigma_mult=1.0):
    med = np.median(np.concatenate([d_xx.ravel(), d_yy.ravel(), d_xy.ravel()]))
    k = lambda d: np.exp(-d / max(med * sigma_mult, 1e-12))
    return k(d_xx).mean() + k(d_yy).mean() - 2.0 * k(d_xy).mean()


class ClipScorer:
    def __init__(self, device="cuda"):
        import torch
        import open_clip
        self.model, _, _ = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
        self.model = self.model.to(device).eval()
        self.tok = open_clip.get_tokenizer("ViT-B-32")
        self.device = device
        self.pre = self.model.preprocess

    @torch.no_grad()
    def score_images_prompts(self, images, prompts):
        import torch
        imgs = torch.stack([self.pre(im.convert("RGB")) for im in images]).to(self.device)
        txt = self.tok(prompts).to(self.device)
        fi = self.model.encode_image(imgs)
        ft = self.model.encode_text(txt)
        fi = fi / fi.norm(dim=-1, keepdim=True)
        ft = ft / ft.norm(dim=-1, keepdim=True)
        return (fi * ft).sum(-1).mean().item()
