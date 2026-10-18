#!/usr/bin/env python3
"""Run the official GAP-Diff generator in inference mode.

The released generate.py leaves the module in PyTorch's default training mode,
which makes its BatchNorm layers fail for the official single-image inference
batch. This wrapper changes only model mode (eval); weights, architecture,
normalization, noise budget, and output conversion remain unchanged.
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torchvision import transforms


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--generator-path", type=Path, required=True)
    parser.add_argument("--source-path", type=Path, required=True)
    parser.add_argument("--save-path", type=Path, required=True)
    parser.add_argument("--noise-budget", default="16.0")
    parser.add_argument("--resolution", type=int, default=512)
    args = parser.parse_args()

    sys.path.insert(0, str(args.repo))
    from models.Generator_Prelayer import Generator_Prelayer

    # The official constructor reads these argparse attributes.
    args.training = False
    device = torch.device("cuda")
    model = Generator_Prelayer(args).to(device)
    state = torch.load(args.generator_path, map_location=device)
    model.load_state_dict(state)
    model.eval()

    preprocess = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize([0.5], [0.5]),
    ])
    args.save_path.mkdir(parents=True, exist_ok=True)
    sources = sorted(p for p in args.source_path.iterdir()
                     if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    with torch.inference_mode():
        for source in sources:
            image = Image.open(source).convert("RGB")
            # Match ScrapeBench's canonical ingestion for every defense:
            # center-crop to square, then resize to the configured resolution.
            width, height = image.size
            side = min(width, height)
            image = image.crop(((width - side) // 2, (height - side) // 2,
                                (width + side) // 2, (height + side) // 2))
            image = image.resize((args.resolution, args.resolution), Image.Resampling.LANCZOS)
            tensor = preprocess(image).unsqueeze(0).to(device)
            protected = model(tensor)[0].detach().float().cpu().permute(1, 2, 0).numpy()
            array = np.clip((protected * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
            Image.fromarray(array).save(args.save_path / f"{source.stem}.png")
    print(f"GAP-Diff inference complete: {len(sources)} images -> {args.save_path}")


if __name__ == "__main__":
    main()
