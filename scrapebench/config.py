import os
import yaml

DEFAULTS = {
    "run": {"name": "default", "out_dir": "runs/default", "seed": 0, "device": "cuda"},
    "data": {"root": "data/identities", "gallery_per_id": 6, "ref_per_id": 4},
    "funnel": {"tiers": ["t0"]},
    "protection": {"methods": ["clean"], "eps": 8, "surrogate_steps": 200, "pgd_steps": 100},
    "attack": {
        "zero_shot": {"model": "ip_adapter_faceid_sd15", "batch": 8, "rounds": 2, "num_steps": 30, "guidance": 5.0, "id_scale": 0.8},
        "dreambooth": {"base": "stable-diffusion-v1-5/stable-diffusion-v1-5", "steps": 400, "lora_rank": 16, "lr": 1e-4, "prior": True, "class_images": 60},
        "gen": {"prompts_per_model": 5, "batch": 8, "rounds": 1, "num_steps": 30, "guidance": 7.5},
    },
    "metrics": {"tau": 0.30, "face_pack": "buffalo_l"},
}


def _merge(base, over):
    out = dict(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config(path=None, overrides=None):
    cfg = dict(DEFAULTS)
    if path and os.path.exists(path):
        with open(path) as f:
            cfg = _merge(cfg, yaml.safe_load(f) or {})
    elif path and not os.path.exists(path):
        raise FileNotFoundError(f"config file not found: {path}")
    for kv in overrides or []:
        key, _, val = kv.partition("=")
        node = cfg
        parts = key.split(".")
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        try:
            val = yaml.safe_load(val)
        except Exception:
            pass
        node[parts[-1]] = val
    return cfg
