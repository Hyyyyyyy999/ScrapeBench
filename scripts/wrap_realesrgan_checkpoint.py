#!/usr/bin/env python3
"""Wrap a raw Real-ESRGAN state_dict for the PyPI RealESRGANer loader."""

import argparse
from pathlib import Path

import torch


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    state = torch.load(args.input, map_location="cpu")
    if "params" in state or "params_ema" in state:
        wrapped = state
    else:
        wrapped = {"params": state}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    torch.save(wrapped, args.output)
    print(args.output)


if __name__ == "__main__":
    main()
