#!/usr/bin/env python3
"""Build an identity-labelled CelebA-HQ-100 subset from local assets."""
import argparse
import tarfile
from collections import defaultdict
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", required=True)
    ap.add_argument("--mapping", required=True)
    ap.add_argument("--identities", required=True)
    ap.add_argument("--out", default="data/celeba_hq100")
    ap.add_argument("--n-ids", type=int, default=100)
    ap.add_argument("--gallery", type=int, default=8)
    ap.add_argument("--refs", type=int, default=2)
    args = ap.parse_args()

    identity = {}
    with open(args.identities) as handle:
        for line in handle:
            filename, pid = line.split()
            identity[filename] = int(pid)

    groups = defaultdict(list)
    with open(args.mapping) as handle:
        for line in handle:
            hq_idx, _, original = line.split()
            groups[identity[original]].append(f"{int(hq_idx):05d}.jpg")

    needed = args.gallery + args.refs
    selected = [pid for pid in sorted(groups) if len(groups[pid]) >= needed][:args.n_ids]
    if len(selected) != args.n_ids:
        raise SystemExit(f"need {args.n_ids} identities with {needed} images, found {len(selected)}")
    wanted = {}
    for pid in selected:
        for index, filename in enumerate(sorted(groups[pid])[:needed]):
            wanted[filename] = (pid, index)

    root = Path(args.out)
    extracted_names = set()
    with tarfile.open(args.archive, "r:gz") as archive:
        for member in archive:
            filename = Path(member.name).name
            # Some distributed CelebA-HQ tarballs contain duplicate archive
            # members. Count and write each logical image exactly once.
            if filename not in wanted or filename in extracted_names:
                continue
            pid, index = wanted[filename]
            identity_name = f"celeb{pid:05d}"
            if index < args.gallery:
                target = root / "raw" / identity_name / f"{index:04d}.jpg"
            else:
                target = root / "refs" / identity_name / f"ref{index - args.gallery:04d}.jpg"
            target.parent.mkdir(parents=True, exist_ok=True)
            source = archive.extractfile(member)
            if source is None:
                raise RuntimeError(f"cannot extract {member.name}")
            target.write_bytes(source.read())
            extracted_names.add(filename)

    extracted = len(extracted_names)
    if extracted != args.n_ids * needed:
        raise SystemExit(f"expected {args.n_ids * needed} images, extracted {extracted}")
    print(f"prepared {args.n_ids} identities and {extracted} unique images at {root}")


if __name__ == "__main__":
    main()
