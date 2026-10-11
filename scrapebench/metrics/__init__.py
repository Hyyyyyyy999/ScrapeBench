from .stats import bootstrap_ci_mean, paired_wilcoxon, holm, cliffs_delta


def __getattr__(name):
    if name in ("IdScorer",):
        from .id_sim import IdScorer
        return IdScorer
    if name in ("psnr", "kid_from_features", "ClipScorer"):
        import importlib
        mod = importlib.import_module(".quality", __name__)
        return getattr(mod, name)
    raise AttributeError(name)
