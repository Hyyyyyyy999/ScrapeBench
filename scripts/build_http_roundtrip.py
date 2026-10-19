#!/usr/bin/env python3
"""Reproducible self-hosted HTTP upload--transcode--scrape round trip."""
import csv
import hashlib
import io
import tempfile
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

from PIL import Image


class Handler(BaseHTTPRequestHandler):
    store = None
    def log_message(self, *_): pass
    def do_POST(self):
        rel = unquote(self.path.removeprefix("/upload/")).strip("/")
        raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        image = Image.open(io.BytesIO(raw)).convert("RGB").resize((512, 512), Image.Resampling.LANCZOS)
        out = self.store / (rel + ".jpg"); out.parent.mkdir(parents=True, exist_ok=True)
        image.save(out, "JPEG", quality=70, subsampling=2, optimize=False)
        self.send_response(201); self.end_headers(); self.wfile.write(rel.encode())
    def do_GET(self):
        rel = unquote(self.path.removeprefix("/media/")).strip("/")
        p = self.store / (rel + ".jpg")
        if not p.is_file(): self.send_error(404); return
        data = p.read_bytes(); self.send_response(200)
        self.send_header("Content-Type", "image/jpeg"); self.send_header("Content-Length", str(len(data)))
        self.end_headers(); self.wfile.write(data)


def sha(data): return hashlib.sha256(data).hexdigest()


def main():
    data = Path("data/web40"); methods = ("clean", "gapdiff", "idprotector", "arcp_web_v4")
    ids = sorted(p.name for p in (data / "raw").iterdir() if p.is_dir())[:4]
    rows=[]
    with tempfile.TemporaryDirectory(prefix="scrapebench-http-") as tmp:
        Handler.store = Path(tmp)
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        # Cluster login/compute environments may export HTTP_PROXY.  The
        # closed-loop audit must contact our self-hosted endpoint directly.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            for _ in range(50):
                if thread.is_alive():
                    break
                time.sleep(0.02)
            for method in methods:
                target_method = method + "_http_roundtrip"
                for pid in ids:
                    sources = sorted((data / "protected" / method / pid).glob("*.png"))
                    if len(sources) != 4: raise SystemExit(f"incomplete source {method}/{pid}")
                    out_dir = data / "protected" / target_method / pid; out_dir.mkdir(parents=True, exist_ok=True)
                    for source in sources:
                        raw=source.read_bytes(); rel=f"{target_method}/{pid}/{source.stem}"
                        req=urllib.request.Request(base+"/upload/"+rel, data=raw, method="POST",
                                                   headers={"Content-Type":"image/png"})
                        with opener.open(req, timeout=30) as response: post_status=response.status
                        with opener.open(base+"/media/"+rel, timeout=30) as response:
                            served=response.read(); get_status=response.status
                        dst=out_dir/(source.stem+".jpg"); dst.write_bytes(served)
                        rows.append({"method":method,"roundtrip_method":target_method,"pid":pid,
                                     "file":source.name,"post_status":post_status,"get_status":get_status,
                                     "source_sha256":sha(raw),"served_sha256":sha(served),"served_bytes":len(served)})
        finally:
            server.shutdown(); thread.join()
    out=Path("runs/web4_http_roundtrip/http_audit.csv"); out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("w",newline="") as h:
        w=csv.DictWriter(h,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    if len(rows)!=64 or any(r["post_status"]!=201 or r["get_status"]!=200 for r in rows):
        raise SystemExit("HTTP roundtrip audit failed")
    print(f"PASS: {len(rows)} HTTP upload/transcode/scrape operations; audit={out}")


if __name__ == "__main__": main()
