#!/usr/bin/env python3
"""Create a deterministic, immutable development/core/audit identity split."""
import argparse
import json
from pathlib import Path


def valid_ids(root, gallery=8, refs=2):
    def count(path):
        return len([p for p in path.glob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}])
    return sorted(
        path.name for path in (root / "raw").iterdir()
        if path.is_dir() and count(path) >= gallery
        and (root / "refs" / path.name).is_dir()
        and count(root / "refs" / path.name) >= refs
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default="data")
    ap.add_argument("--out", default="protocol/celeba100_split.json")
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--print-set", choices=["development", "core", "audit", "test"])
    ap.add_argument("--shard", type=int)
    ap.add_argument("--num-shards", type=int, default=1)
    args = ap.parse_args()
    out = Path(args.out)
    if out.exists():
        split = json.loads(out.read_text())
    else:
        ids = valid_ids(Path(args.data_root))[:args.n]
        if len(ids) < args.n:
            raise SystemExit(f"need {args.n} complete identities, found {len(ids)}")
        split = {
            "version": 1,
            "selection": "lexicographically first 100 complete CelebA identity IDs",
            "development": ids[:10],
            "core": ids[10:90],
            "audit": ids[90:100],
            "test": ids[10:100],
        }
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(split, indent=2) + "\n")
    if args.print_set:
        ids = split[args.print_set]
        if args.shard is not None:
            ids = ids[args.shard::args.num_shards]
        print(",".join(ids))
    else:
        print(out)


if __name__ == "__main__":
    main()
