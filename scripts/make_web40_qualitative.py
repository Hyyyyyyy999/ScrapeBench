#!/usr/bin/env python3
"""Deterministic qualitative panels from the same ledgers used for metrics."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

run = Path("runs/web40_single_intervention/generations")
pid = sorted(p.name for p in Path("data/web40/raw").iterdir() if p.is_dir())[0]
methods = [("clean", "No defense"), ("gapdiff_8", "GAP-Diff"),
           ("idprotector_8", "IDProtector"), ("arcp_web_v4", "ARCP-Web")]
sources = sorted((Path("data/web40/protected/clean") / pid).glob("*.png"))
font = ImageFont.load_default()
for attack, title in (("instantid", "InstantID"), ("ipfaceid", "IP-Adapter-FaceID")):
    ledgers = {}
    for method, _ in methods:
        p = run / attack / method / "t1_jpeg70" / pid / "samples.jsonl"
        rows = [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
        ledgers[method] = (p.parent, {int(r["prompt_id"]): r for r in rows})
    cw, ch, top, left = 170, 190, 28, 92
    canvas = Image.new("RGB", (left + cw * 5, top + ch * 4), "white")
    draw = ImageDraw.Draw(canvas)
    labels = ["Source"] + [x[1] for x in methods]
    for c, label in enumerate(labels): draw.text((left + c * cw + 5, 8), label, fill="black", font=font)
    for row in range(4):
        draw.text((5, top + row * ch + 5), f"Scenario {row + 1}", fill="black", font=font)
        src = ImageOps.fit(Image.open(sources[row]).convert("RGB"), (160, 160))
        canvas.paste(src, (left + 5, top + row * ch))
        for col, (method, _) in enumerate(methods, 1):
            folder, by_prompt = ledgers[method]; item = by_prompt[row]
            image = ImageOps.fit(Image.open(folder / item["file"]).convert("RGB"), (160, 160))
            canvas.paste(image, (left + col * cw + 5, top + row * ch))
            score = "no face" if not item.get("detected") else f"ISM {float(item['ism']):.3f}"
            draw.text((left + col * cw + 7, top + row * ch + 164), score, fill="black", font=font)
    out = Path(f"paper/figures/web40_{attack}_t1.png")
    canvas.save(out)
    print(f"wrote {out} ({title}, {pid})")
