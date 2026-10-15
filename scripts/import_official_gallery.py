#!/usr/bin/env python3
"""Import an official defense's protected images without reimplementation."""
import argparse
import shutil
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--data-root", default="data")
    ap.add_argument("--method", required=True, choices=["gapdiff", "idprotector", "antipure", "vcpro"])
    ap.add_argument("--copy", action="store_true", help="copy instead of symlink")
    args = ap.parse_args()
    source = Path(args.source).resolve()
    target = Path(args.data_root) / "protected" / args.method
    target.mkdir(parents=True, exist_ok=True)
    imported = 0
    for identity in sorted(p for p in source.iterdir() if p.is_dir()):
        dst = target / identity.name
        dst.mkdir(exist_ok=True)
        for image in sorted(identity.iterdir()):
            if image.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
                continue
            out = dst / image.name
            if out.exists() or out.is_symlink():
                continue
            shutil.copy2(image, out) if args.copy else out.symlink_to(image)
            imported += 1
    print(f"imported {imported} images into {target}")


if __name__ == "__main__":
    main()
