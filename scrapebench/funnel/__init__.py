from .transcode import T1_TRANSFORMS, t1_platform
from .browser import T2_TRANSFORMS, t2_browser, t2_canvas
from .agent_capture import T3_TRANSFORMS, t3_agent
from .restore import T4_TRANSFORMS, t4_restore
from .mixpool import T6_TRANSFORMS, build_mixpool
from . import regenerate

REGISTRY = {}
REGISTRY.update(T1_TRANSFORMS)
REGISTRY.update(T2_TRANSFORMS)
REGISTRY.update(T3_TRANSFORMS)
REGISTRY.update(T4_TRANSFORMS)
REGISTRY.update(T6_TRANSFORMS)
REGISTRY.update(regenerate.T5_TRANSFORMS)


def get_tier(name):
    if name in ("t0", "raw", "clean"):
        return lambda img: img
    if name in REGISTRY:
        return REGISTRY[name]
    raise KeyError(f"unknown funnel tier: {name}")
