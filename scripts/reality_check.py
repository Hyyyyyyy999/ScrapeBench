import csv
import hashlib
import io
import json
import os

import requests
from PIL import Image

UA = {"User-Agent": "ScrapeBenchRealityCheck/0.1 (research; contact: benchmark@example.org)"}


def probe(url, tag, params):
    try:
        r = requests.get(url, params=params, headers=UA, timeout=30)
        if r.status_code != 200 or len(r.content) < 500:
            return {"target": tag, "url": r.url, "status": r.status_code, "bytes": len(r.content),
                    "format": "", "width": "", "height": "", "est_q": "", "note": "small-or-error"}
        im = Image.open(io.BytesIO(r.content))
        q = ""
        if im.format == "JPEG":
            qt = im.quantization
            if qt and 0 in qt:
                table = qt[0]
                try:
                    import numpy as np
                    std = Image.open(io.BytesIO(r.content))
                    std.save("/tmp/_rc_ref.jpg", quality=100)
                    best, bq = None, None
                    for cand in range(30, 100):
                        std.save("/tmp/_rc_c.jpg", quality=cand)
                        ref = Image.open("/tmp/_rc_ref.jpg").quantization[0]
                        cur = Image.open("/tmp/_rc_c.jpg").quantization[0]
                        d = sum(abs(a - b) for a, b in zip(ref, cur)) + sum(abs(a - b) for a, b in zip(table, cur))
                        if best is None or d < best:
                            best, bq = d, cand
                    q = bq
                except Exception:
                    q = ""
        return {"target": tag, "url": r.url, "status": r.status_code, "bytes": len(r.content),
                "format": im.format, "width": im.width, "height": im.height, "est_q": q, "note": ""}
    except Exception as e:
        return {"target": tag, "url": url, "status": -1, "bytes": 0, "format": "", "width": "", "height": "", "est_q": "", "note": str(e)[:60]}


def main():
    rows = []
    for u in [1, 2, 5, 9, 18]:
        for s in [200, 400, 800]:
            rows.append(probe(f"https://avatars.githubusercontent.com/u/{u}", f"github_avatar_u{u}_s{s}", {"s": s}))
    email = "scrapebench-reality-check@example.org"
    h = hashlib.md5(email.encode()).hexdigest()
    for s in [200, 512]:
        rows.append(probe(f"https://www.gravatar.com/avatar/{h}", f"gravatar_default_s{s}", {"s": s, "d": "mp"}))
    for q in [60, 70, 80, 90]:
        rows.append(probe("https://wsrv.nl/", f"wsrv_q{q}", {"url": "upload.wikimedia.org/wikipedia/commons/3/3a/Cat03.jpg", "w": 512, "q": q, "output": "jpg"}))
    for q in [60, 80, 90]:
        rows.append(probe("https://i0.wp.com/", f"photon_q{q}", {"resize": "512,384", "quality": q}))
    for w in [320, 640]:
        rows.append(probe("https://i0.wp.com/", f"photon_w{w}", {"resize": f"{w},{w}", "quality": ""}))
    os.makedirs("runs/reality", exist_ok=True)
    with open("runs/reality/platform_cdn.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["target", "url", "status", "bytes", "format", "width", "height", "est_q", "note"])
        w.writeheader()
        w.writerows(rows)
    print(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
