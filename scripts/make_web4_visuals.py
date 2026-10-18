#!/usr/bin/env python3
"""Build GAP-Diff-style prompt-by-method panels from auditable generations."""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


TIERS = ("t0", "t1_jpeg70", "t2_canvas_dpr1", "t3_agent_facecrop",
         "t4_sr_x2", "t5_i2i30", "t6_sde50")
SCENES = ("Avatar", "Selfie", "Low light", "Travel")


def font(size, bold=False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    for root in (Path("/usr/share/fonts/truetype/dejavu"), Path("/usr/share/fonts/dejavu")):
        path = root / name
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def crop_square(image):
    image = image.convert("RGB")
    side = min(image.size)
    left = (image.width - side) // 2
    top = (image.height - side) // 2
    return image.crop((left, top, left + side, top + side))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="web4_validation")
    ap.add_argument("--pid", default="celeb00001")
    ap.add_argument("--methods", default="clean,gapdiff,metacloak,goodac,arcp_web_v4")
    args = ap.parse_args()
    root = Path("runs") / args.run
    out = root / "visuals"
    out.mkdir(parents=True, exist_ok=True)
    methods = args.methods.split(",")
    labels = {"clean": "No defense", "gapdiff": "GAP-Diff",
              "metacloak": "MetaCloak", "goodac": "GoodAC",
              "arcp_web_v4": "ARCP-Web"}
    clean_inputs = sorted((Path("data/web40/protected/clean") / args.pid).glob("*"))
    if len(clean_inputs) < 4:
        raise SystemExit(f"need four clean inputs for {args.pid}")

    tile, row_label, header, footer, gap = 210, 96, 48, 26, 5
    columns = ["Input photo"] + [labels.get(m, m) for m in methods]
    width = row_label + len(columns) * (tile + gap) + gap
    height = header + len(SCENES) * (tile + footer + gap) + gap
    made = 0
    for attack in ("instantid", "ipfaceid"):
        for tier in TIERS:
            method_samples = {}
            complete = True
            for method in methods:
                cell = root / "generations" / attack / method / tier / args.pid
                ledger = cell / "samples.jsonl"
                if not ledger.exists():
                    complete = False
                    break
                rows = [json.loads(x) for x in ledger.read_text().splitlines() if x.strip()]
                by_prompt = {}
                for row in rows:
                    by_prompt.setdefault(int(row["prompt_id"]), (cell / row["file"], row))
                if len(by_prompt) < 4:
                    complete = False
                    break
                method_samples[method] = by_prompt
            if not complete:
                continue

            panel = Image.new("RGB", (width, height), "white")
            draw = ImageDraw.Draw(panel)
            for col, title in enumerate(columns):
                x = row_label + gap + col * (tile + gap)
                bbox = draw.textbbox((0, 0), title, font=font(19, True))
                draw.text((x + (tile - (bbox[2] - bbox[0])) / 2, 13), title,
                          fill=(25, 25, 25), font=font(19, True))
            for p, scene in enumerate(SCENES):
                y = header + p * (tile + footer + gap)
                draw.rounded_rectangle((5, y, row_label - 6, y + tile), radius=7,
                                       fill=(240, 244, 248), outline=(150, 165, 180), width=1)
                bbox = draw.textbbox((0, 0), scene, font=font(17, True))
                draw.text(((row_label - (bbox[2] - bbox[0])) / 2,
                           y + (tile - (bbox[3] - bbox[1])) / 2), scene,
                          fill=(45, 70, 95), font=font(17, True))
                images = [(clean_inputs[p], None)] + [method_samples[m][p] for m in methods]
                for col, (path, meta) in enumerate(images):
                    x = row_label + gap + col * (tile + gap)
                    image = crop_square(Image.open(path)).resize((tile, tile), Image.Resampling.LANCZOS)
                    panel.paste(image, (x, y))
                    draw.rectangle((x, y, x + tile - 1, y + tile - 1), outline=(75, 75, 75), width=1)
                    if meta is not None:
                        value = meta.get("ism")
                        status = "no face" if value is None else f"ISM {float(value):0.3f}"
                        color = (155, 45, 45) if value is None else (45, 45, 45)
                        bbox = draw.textbbox((0, 0), status, font=font(14))
                        draw.text((x + (tile - (bbox[2] - bbox[0])) / 2, y + tile + 4),
                                  status, fill=color, font=font(14))
            title = f"{attack} | {tier} | fixed identity {args.pid}"
            panel.save(out / f"{attack}_{tier}_{args.pid}.png", optimize=True)
            made += 1
    print(f"wrote {made} prompt-by-method visual panels under {out}")


if __name__ == "__main__":
    main()
