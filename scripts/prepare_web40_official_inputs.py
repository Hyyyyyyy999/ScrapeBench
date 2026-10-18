#!/usr/bin/env python3
"""Prepare identical square inputs for official MetaCloak/GoodAC runners."""

from pathlib import Path
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/web40"
OUT = ROOT / "runs/web40_official_inputs"
LANCZOS = getattr(getattr(Image, "Resampling", Image), "LANCZOS")


def square(path: Path) -> Image.Image:
    im = Image.open(path).convert("RGB")
    w, h = im.size
    side = min(w, h)
    im = im.crop(((w - side) // 2, (h - side) // 2,
                  (w + side) // 2, (h + side) // 2))
    return im.resize((512, 512), LANCZOS)


def write_split(source: Path, target: Path, prefix: str) -> None:
    target.mkdir(parents=True, exist_ok=True)
    paths = sorted(p for p in source.iterdir()
                   if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"})
    for i, path in enumerate(paths):
        square(path).save(target / f"{prefix}{i:04d}.png")


def main() -> None:
    for raw in sorted((DATA / "raw").iterdir()):
        if not raw.is_dir():
            continue
        pid = raw.name
        write_split(DATA / "refs" / pid, OUT / pid / "set_A", "ref")
        write_split(raw, OUT / pid / "set_B", "")
    print(f"prepared {len(list(OUT.glob('*/set_B')))} identities under {OUT}")


if __name__ == "__main__":
    main()
