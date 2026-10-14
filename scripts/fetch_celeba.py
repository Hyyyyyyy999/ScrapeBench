import argparse
import os
from collections import defaultdict
from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data")
    ap.add_argument("--n-ids", type=int, default=40)
    ap.add_argument("--per-id", type=int, default=8)
    ap.add_argument("--max-scan", type=int, default=60000)
    args = ap.parse_args()
    from datasets import load_dataset
    root = os.path.join(args.out, "raw")
    refs = os.path.join(args.out, "refs")
    have = defaultdict(int)
    if os.path.isdir(root):
        for d in os.listdir(root):
            have[d] = len([f for f in os.listdir(os.path.join(root, d)) if f.endswith((".png", ".jpg"))])
    need = {}
    ds = load_dataset("flwrlabs/celeba", split="train", streaming=True)
    it = iter(ds)
    scanned = 0
    quota_done = 0
    while scanned < args.max_scan and quota_done < args.n_ids:
        try:
            row = next(it)
        except StopIteration:
            break
        scanned += 1
        cid = row.get("celeb_id")
        if cid is None:
            continue
        key = f"celeb{int(cid):05d}"
        if have.get(key, 0) >= args.per_id + 2:
            continue
        img = row.get("image")
        if img is None:
            continue
        img = img.convert("RGB")
        if img.width < 128 or img.height < 128:
            continue
        d1 = os.path.join(root, key)
        d2 = os.path.join(refs, key)
        os.makedirs(d1, exist_ok=True)
        os.makedirs(d2, exist_ok=True)
        n = have.get(key, 0)
        if n < args.per_id:
            img.save(os.path.join(d1, f"{n:04d}.jpg"), quality=95)
        else:
            img.save(os.path.join(d2, f"ref{n - args.per_id:04d}.jpg"), quality=95)
        have[key] = n + 1
        if have[key] == args.per_id + 2:
            quota_done += 1
    done = [k for k, v in have.items() if v >= args.per_id + 2]
    print(f"scanned={scanned} complete_ids={len(done)}/{args.n_ids}")


if __name__ == "__main__":
    main()
    import os
    os._exit(0)
