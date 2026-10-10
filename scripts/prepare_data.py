import argparse
import os
import shutil
import zipfile
import numpy as np
from PIL import Image, ImageDraw


def make_demo(data_root, n_ids=6, per_id=8):
    rng = np.random.default_rng(0)
    root = os.path.join(data_root, "raw")
    refs = os.path.join(data_root, "refs")
    for i in range(n_ids):
        pid = f"demo{i:03d}"
        d1, d2 = os.path.join(root, pid), os.path.join(refs, pid)
        os.makedirs(d1, exist_ok=True)
        os.makedirs(d2, exist_ok=True)
        base = rng.integers(0, 255, 3)
        for j in range(per_id):
            im = Image.new("RGB", (512, 512), tuple(int(v) for v in base))
            dr = ImageDraw.Draw(im)
            cx, cy = 256, 256
            r = int(120 + 10 * np.sin(j))
            dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=tuple(int(v) for v in (base + 60) % 256))
            dr.ellipse([cx - 40, cy - 40, cx - 10, cy - 10], fill=(30, 30, 30))
            dr.ellipse([cx + 10, cy - 40, cx + 40, cy - 10], fill=(30, 30, 30))
            dst = os.path.join(d1, f"{j:04d}.png") if j < per_id - 2 else os.path.join(d2, f"ref{j:04d}.png")
            im.save(dst)
    print(f"demo data written to {root} ({n_ids} ids)")


def unpack_celeba(archive, data_root, n_ids=40, per_id=8):
    import pandas as pd
    tmp = os.path.join(data_root, "_celeba_tmp")
    os.makedirs(tmp, exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        z.extractall(tmp)
    ident = None
    for root_dir, _, files in os.walk(tmp):
        if "identity_CelebA.txt" in files:
            ident = os.path.join(root_dir, "identity_CelebA.txt")
            img_dir = root_dir
            break
    if ident is None:
        raise FileNotFoundError("identity_CelebA.txt not found in archive")
    df = pd.read_csv(ident, sep=r"\s+", names=["file", "id"])
    counts = df["id"].value_counts()
    chosen = counts[counts >= per_id + 2].index[:n_ids]
    root_out = os.path.join(data_root, "raw")
    refs_out = os.path.join(data_root, "refs")
    made = 0
    for cid in chosen:
        files = df[df["id"] == cid]["file"].tolist()[: per_id + 2]
        pid = f"celeb{int(cid):05d}"
        d1, d2 = os.path.join(root_out, pid), os.path.join(refs_out, pid)
        os.makedirs(d1, exist_ok=True)
        os.makedirs(d2, exist_ok=True)
        for k, fn in enumerate(files):
            src = os.path.join(img_dir, fn)
            if not os.path.isfile(src):
                continue
            dst = os.path.join(d1, f"{k:04d}.jpg") if k < per_id else os.path.join(d2, f"ref{k:04d}.jpg")
            im = Image.open(src).convert("RGB")
            im.thumbnail((1024, 1024), Image.LANCZOS)
            im.save(dst, quality=95)
        made += 1
        if made >= n_ids:
            break
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"celeba data written ({made} ids)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["demo", "local", "kaggle"], default="demo")
    ap.add_argument("--data-root", default="data")
    ap.add_argument("--local-dir", default=None)
    ap.add_argument("--archive", default=None)
    ap.add_argument("--n-ids", type=int, default=40)
    ap.add_argument("--per-id", type=int, default=8)
    args = ap.parse_args()
    os.makedirs(args.data_root, exist_ok=True)
    if args.source == "demo":
        make_demo(args.data_root, n_ids=6, per_id=args.per_id)
    elif args.source == "local":
        src = args.local_dir
        assert src and os.path.isdir(src), f"local dir {src} not found"
        root, refs = os.path.join(args.data_root, "raw"), os.path.join(args.data_root, "refs")
        ids = sorted(os.listdir(src))
        for pid_dir in ids:
            d = os.path.join(src, pid_dir)
            if not os.path.isdir(d):
                continue
            files = sorted(f for f in os.listdir(d) if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")))
            if len(files) < args.per_id + 2:
                continue
            os.makedirs(os.path.join(root, pid_dir), exist_ok=True)
            os.makedirs(os.path.join(refs, pid_dir), exist_ok=True)
            for k, fn in enumerate(files[: args.per_id + 2]):
                dst = os.path.join(root, pid_dir, f"{k:04d}.jpg") if k < args.per_id else os.path.join(refs, pid_dir, f"ref{k:04d}.jpg")
                shutil.copy(os.path.join(d, fn), dst)
        print(f"local import done from {src}")
    elif args.source == "kaggle":
        archive = args.archive
        assert archive and os.path.isfile(archive), f"archive {archive} not found; download first via kaggle CLI"
        unpack_celeba(archive, args.data_root, n_ids=args.n_ids, per_id=args.per_id)


if __name__ == "__main__":
    main()
