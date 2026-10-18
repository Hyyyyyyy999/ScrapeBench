#!/usr/bin/env python3
"""Prepare the five-identity VGGFace2 subset shipped with GAP-Diff.

set_B is the protected/customization gallery and set_C is held out for
identity evaluation, matching the GAP-Diff artifact protocol.
"""

import argparse
import json
import shutil
from pathlib import Path


IDENTITIES = ("n000061", "n000089", "n000090", "n000154", "n000161")


def copy_images(source: Path, target: Path, expected: int) -> list[str]:
    images = sorted(p for p in source.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg"})
    if len(images) != expected:
        raise RuntimeError(f"{source}: expected {expected} images, found {len(images)}")
    target.mkdir(parents=True, exist_ok=True)
    outputs = []
    for index, image in enumerate(images):
        destination = target / f"{index:04d}{image.suffix.lower()}"
        shutil.copy2(image, destination)
        outputs.append(str(destination))
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("/home/huangyue26/GAP-Diff/data/test_dataset"))
    parser.add_argument("--output", type=Path, default=Path("data/vggface2_gap5"))
    args = parser.parse_args()

    records = []
    for identity in IDENTITIES:
        base = args.source / identity
        gallery = copy_images(base / "set_B", args.output / "raw" / identity, 4)
        refs = copy_images(base / "set_C", args.output / "refs" / identity, 4)
        records.append({"identity": identity, "gallery": gallery, "refs": refs})
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "manifest.json").write_text(
        json.dumps({"protocol": "GAP-Diff VGGFace2 set_B/set_C", "identities": records}, indent=2) + "\n"
    )
    print(f"prepared {len(records)} identities at {args.output}")


if __name__ == "__main__":
    main()
