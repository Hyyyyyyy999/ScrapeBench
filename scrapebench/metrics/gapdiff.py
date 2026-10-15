"""Metrics used by GAP-Diff Table I, with explicit dependency reporting.

FDFR and ISM use the same InsightFace detector/ArcFace scorer as ScrapeBench.
BRISQUE and SER-FIQ are optional because their reference packages and weights
are not silently substituted: a missing metric is reported as unavailable.
"""
from pathlib import Path

import numpy as np
from PIL import Image


def fdfr_ism(images, ref_embeddings, scorer):
    scored = [scorer.best_sim(im, ref_embeddings) for im in images]
    detected = np.asarray([ok for _, ok in scored], dtype=bool)
    sims = np.asarray([s for s, _ in scored], dtype=np.float64)
    return {
        "fdfr": float(1.0 - detected.mean()) if len(detected) else float("nan"),
        "ism": float(np.nanmean(sims)) if np.any(detected) else float("nan"),
        "n": int(len(images)),
    }


def brisque(images):
    try:
        from brisque import BRISQUE
    except ImportError as exc:
        raise RuntimeError("BRISQUE unavailable: install the pinned 'brisque' package") from exc
    model = BRISQUE(url=False)
    return float(np.mean([model.score(np.asarray(im.convert("RGB"))) for im in images]))


def ser_fiq(images, implementation_root=None, gpu=0, repeats=100):
    """Evaluate the official ArcFace-based SER-FIQ implementation.

    ``implementation_root`` must point at pterhoer/FaceImageQuality.  We do not
    replace it with a different face-quality model when that environment is
    absent because the numbers would not be comparable with GAP-Diff.
    """
    import os
    import sys
    root = implementation_root or os.environ.get("FACE_IMAGE_QUALITY_ROOT")
    if root and root not in sys.path:
        sys.path.insert(0, root)
    try:
        from face_image_quality import SER_FIQ
    except ImportError as exc:
        raise RuntimeError("SER-FIQ unavailable: set FACE_IMAGE_QUALITY_ROOT to the official implementation") from exc
    evaluator = SER_FIQ(gpu=gpu)
    vals = []
    for image in images:
        bgr = np.asarray(image.convert("RGB"))[:, :, ::-1]
        aligned = evaluator.apply_mtcnn(bgr)
        if aligned is not None:
            vals.append(evaluator.get_score(aligned, T=repeats))
    return float(np.mean(vals))


def load_images(directory):
    paths = sorted(p for p in Path(directory).glob("*.png"))
    return [Image.open(path).convert("RGB") for path in paths]
