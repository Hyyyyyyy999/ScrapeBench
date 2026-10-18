#!/usr/bin/env python3
"""Build the audited 40-identity proof-of-concept cohort.

The cohort contains 35 CelebA identities from the original local campaign that
pass per-identity face/reference checks and the five identities distributed by
the GAP-Diff VGGFace2 artifact. All identities use four gallery and two held-out
reference images so dataset membership does not change attacker input count.
"""

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CELEBA = ROOT / "data"
VGG = ROOT / "data" / "vggface2_gap5"
OUT = ROOT / "data" / "web40"
EXCLUDED = {"celeb00026", "celeb00037"}


def image_files(path: Path) -> list[Path]:
    return sorted(p for p in path.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"})


def copy_group(pid: str, source_raw: Path, source_refs: Path, corpus: str) -> dict:
    gallery = image_files(source_raw)[:4]
    refs = image_files(source_refs)[:2]
    if len(gallery) != 4 or len(refs) != 2:
        raise RuntimeError(f"{pid}: need four gallery and two references")
    raw_out = OUT / "raw" / pid
    ref_out = OUT / "refs" / pid
    raw_out.mkdir(parents=True, exist_ok=True)
    ref_out.mkdir(parents=True, exist_ok=True)
    for index, source in enumerate(gallery):
        shutil.copy2(source, raw_out / f"{index:04d}{source.suffix.lower()}")
    for index, source in enumerate(refs):
        shutil.copy2(source, ref_out / f"ref{index:04d}{source.suffix.lower()}")
    return {"identity": pid, "corpus": corpus, "gallery": [str(p) for p in gallery], "refs": [str(p) for p in refs]}


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite existing cohort: {OUT}")
    records = []
    celeba_ids = sorted(p.name for p in (CELEBA / "raw").iterdir() if p.is_dir() and p.name not in EXCLUDED)
    if len(celeba_ids) != 35:
        raise RuntimeError(f"expected 35 audited CelebA identities, found {len(celeba_ids)}")
    for pid in celeba_ids:
        records.append(copy_group(pid, CELEBA / "raw" / pid, CELEBA / "refs" / pid, "CelebA"))
    for source in sorted((VGG / "raw").iterdir()):
        pid = f"vgg_{source.name}"
        records.append(copy_group(pid, source, VGG / "refs" / source.name, "VGGFace2/GAP-Diff artifact"))
    if len(records) != 40:
        raise RuntimeError(f"expected 40 identities, found {len(records)}")
    (OUT / "manifest.json").write_text(json.dumps({
        "version": 1,
        "selection": "35 legacy identities passing per-identity audit plus five GAP-Diff VGGFace2 identities",
        "gallery_per_identity": 4,
        "references_per_identity": 2,
        "excluded": sorted(EXCLUDED),
        "identities": records,
    }, indent=2) + "\n")
    print(f"prepared {len(records)} identities at {OUT}")


if __name__ == "__main__":
    main()
