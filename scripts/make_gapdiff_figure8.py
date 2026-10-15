#!/usr/bin/env python3
"""Create a four-prompt qualitative grid from saved Stage-B samples."""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--pid", required=True)
    ap.add_argument("--tier", default="t1_jpeg70")
    ap.add_argument("--methods", default="clean,gapdiff,idprotector,arcp_v2")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    methods = args.methods.split(",")
    root = Path("runs") / args.run / "generations" / "dreambooth"
    cells = {}
    prompts = {}
    for col, method in enumerate(methods):
        folder = root / method / args.tier / args.pid
        manifest = folder / "samples.jsonl"
        if not manifest.exists():
            continue
        rows = [json.loads(line) for line in manifest.read_text().splitlines()]
        for row in rows:
            if row["sample_id"] == 0:
                cells[(row["prompt_id"], col)] = Image.open(folder / row["file"]).convert("RGB").resize((256, 256))
                prompts[row["prompt_id"]] = row["prompt"]
    if not cells:
        raise SystemExit("no saved samples found")
    label_w, header_h = 260, 48
    canvas = Image.new("RGB", (label_w + 256 * len(methods), header_h + 256 * 4), "white")
    draw = ImageDraw.Draw(canvas)
    for col, method in enumerate(methods):
        draw.text((label_w + col * 256 + 8, 14), method, fill="black")
    for row in range(4):
        draw.text((8, header_h + row * 256 + 12), prompts.get(row, f"prompt {row}"), fill="black")
        for col in range(len(methods)):
            if (row, col) in cells:
                canvas.paste(cells[(row, col)], (label_w + col * 256, header_h + row * 256))
    out = Path(args.out or f"figures/gapdiff_fig8_{args.pid}.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out)
    print(out)


if __name__ == "__main__":
    main()
