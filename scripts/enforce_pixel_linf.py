#!/usr/bin/env python3
"""Apply a final integer-domain L-infinity projection to saved PNGs."""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean-root", type=Path, required=True)
    parser.add_argument("--protected-root", type=Path, required=True)
    parser.add_argument("--max-delta", type=int, required=True)
    args = parser.parse_args()
    count = 0
    for clean_path in sorted(args.clean_root.glob("*/*.png")):
        protected_path = args.protected_root / clean_path.relative_to(args.clean_root)
        if not protected_path.exists():
            raise FileNotFoundError(protected_path)
        clean = np.asarray(Image.open(clean_path).convert("RGB"), dtype=np.int16)
        protected = np.asarray(Image.open(protected_path).convert("RGB"), dtype=np.int16)
        if clean.shape != protected.shape:
            raise ValueError(f"shape mismatch: {clean_path} {clean.shape} vs {protected_path} {protected.shape}")
        projected = np.clip(protected, clean - args.max_delta, clean + args.max_delta)
        projected = np.clip(projected, 0, 255).astype(np.uint8)
        temporary = protected_path.with_suffix(".projected.png")
        Image.fromarray(projected).save(temporary)
        temporary.replace(protected_path)
        count += 1
    print(f"projected {count} images to integer L_inf <= {args.max_delta}")


if __name__ == "__main__":
    main()
