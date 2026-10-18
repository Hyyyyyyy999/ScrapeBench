#!/usr/bin/env python3
"""Run an official protector and normalize its outputs into ScrapeBench."""

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image


HOME = Path("/mnt/beegfs/home/huangyue26")
SB = HOME / "ScrapBench"
INPUTS = SB / "runs/web40_official_inputs"
MODEL = HOME / "GAP-Diff/stable-diffusion/stable-diffusion-2-1-base"
CLASS = HOME / "GAP-Diff/data/class-person-2-1"


def run(command, cwd, env=None):
    print("RUN", " ".join(map(str, command)), flush=True)
    subprocess.run([str(x) for x in command], cwd=cwd, env=env, check=True)


def normalize(method, pid, source):
    destination = SB / "data/web40/protected" / method / pid
    destination.mkdir(parents=True, exist_ok=True)
    outputs = sorted(p for p in source.iterdir()
                     if p.suffix.lower() in {".png", ".jpg", ".jpeg"})
    if len(outputs) != 4:
        raise RuntimeError(f"{method}/{pid}: expected 4 protected images, got {len(outputs)}")
    clean_paths = sorted((INPUTS / pid / "set_B").glob("*.png"))
    max_linf = 0
    psnrs = []
    for i, (protected, clean) in enumerate(zip(outputs, clean_paths)):
        p = Image.open(protected).convert("RGB").resize((512, 512))
        c = Image.open(clean).convert("RGB")
        pa = np.asarray(p, dtype=np.int16)
        ca = np.asarray(c, dtype=np.int16)
        max_linf = max(max_linf, int(np.max(np.abs(pa - ca))))
        mse = np.mean((pa.astype(np.float32) - ca.astype(np.float32)) ** 2)
        psnrs.append(float("inf") if mse == 0 else 10.0 * np.log10(255.0 ** 2 / mse))
        p.save(destination / f"{i:04d}.png")
    print(f"VALID {method}/{pid} n=4 size=512 linf_px={max_linf} psnr={np.mean(psnrs):.2f}", flush=True)


def goodac(pid, smoke):
    root = HOME / "GoodAC"
    output = SB / "runs/official_protectors/goodac" / pid
    if output.exists():
        shutil.rmtree(output)
    # Adaptive timestep selection must retain its official 50-step bound even
    # in smoke mode. With a one-step bound the upstream implementation never
    # appends all four per-image timestep sets and later indexes past the list.
    # At least three outer iterations are required to expose inter-iteration
    # memory leaks; a one-iteration smoke test gave a false pass on RTX 4090.
    outer, f_steps, adv_steps, select_steps = ((3, 1, 1, 50) if smoke else (50, 3, 6, 50))
    command = [
        sys.executable, "attacks/goodac.py",
        "--pretrained_model_name_or_path", MODEL,
        "--instance_data_dir_for_train", INPUTS / pid / "set_A",
        "--instance_data_dir_for_adversarial", INPUTS / pid / "set_B",
        "--instance_prompt", "a photo of sks person",
        "--guidance_prompt", "a detailed high resolution portrait of a person, centered face, realistic skin, eyes and facial features",
        "--class_data_dir", CLASS, "--num_class_images", "200",
        "--class_prompt", "a photo of person", "--output_dir", output,
        "--center_crop", "--with_prior_preservation", "--prior_loss_weight", "1.0",
        "--resolution", "512", "--train_text_encoder", "--train_batch_size", "1",
        "--max_train_steps", outer, "--max_f_train_steps", f_steps,
        "--max_adv_train_steps", adv_steps, "--max_steps", select_steps,
        "--checkpointing_iterations", outer, "--learning_rate", "5e-7",
        "--pgd_alpha", "0.005", "--pgd_eps", "16", "--seed", "0",
        "--beta", "1.625", "--gamma", "0.2", "--mixed_precision", "bf16",
        "--report_to", "none",
    ]
    run(command, root)
    normalize("goodac_smoke" if smoke else "goodac", pid, output / "noise-ckpt" / str(outer))


def metacloak(pid, smoke):
    root = HOME / "MetaCloak"
    output = SB / "runs/official_protectors/metacloak" / pid
    if output.exists():
        shutil.rmtree(output)
    train_steps, interval, advance, trails, pgd_steps = ((2, 2, 1, 1, 1) if smoke else (1000, 200, 2, 4, 6))
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root) + os.pathsep + env.get("PYTHONPATH", "")
    env["WANDB_MODE"] = "disabled"
    command = [
        sys.executable, "robust_facecloak/attacks/algs/metacloak.py",
        "--instance_name", pid, "--dataset_name", "web40",
        "--total_train_steps", train_steps, "--interval", interval,
        "--advance_steps", advance, "--unroll_steps", "1",
        "--total_trail_num", trails, "--exp_name", "web40", "--exp_hyper", "official",
        "--pretrained_model_name_or_path", MODEL,
        "--instance_data_dir_for_train", INPUTS / pid / "set_A",
        "--instance_data_dir_for_adversarial", INPUTS / pid / "set_B",
        "--instance_prompt", "a photo of sks person", "--class_data_dir", CLASS,
        "--num_class_images", "200", "--class_prompt", "a photo of person",
        "--output_dir", output, "--center_crop", "--with_prior_preservation",
        "--prior_loss_weight", "1.0", "--resolution", "512", "--train_text_encoder",
        "--train_batch_size", "1", "--learning_rate", "5e-7",
        "--defense_pgd_radius", "11", "--defense_pgd_step_size", "1.1",
        "--defense_pgd_step_num", pgd_steps, "--defense_sample_num", "1",
        "--defense_pgd_ascending", "--attack_pgd_radius", "0",
        "--attack_pgd_step_size", "1", "--attack_pgd_step_num", "3",
        "--transform_gau", "--gau_kernel_size", "7", "--transform_hflip",
        "--mixed_precision", "bf16", "--report_to", "none", "--seed", "0",
    ]
    run(command, root, env)
    normalize("metacloak_smoke" if smoke else "metacloak", pid, output / "noise-ckpt/final")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", choices=("goodac", "metacloak"), required=True)
    parser.add_argument("--pid", required=True)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    if not MODEL.joinpath("unet/config.json").is_file():
        raise SystemExit(f"missing SD2.1 model: {MODEL}")
    if len(list(CLASS.glob("*"))) < 200:
        raise SystemExit(f"need 200 class images: {CLASS}")
    (SB / "runs/official_protectors" / args.method).mkdir(parents=True, exist_ok=True)
    (SB / "data/web40/protected").mkdir(parents=True, exist_ok=True)
    (goodac if args.method == "goodac" else metacloak)(args.pid, args.smoke)


if __name__ == "__main__":
    main()
