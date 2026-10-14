"""Canonical row selection for every paper-facing analysis.

The append-only result log may hold several rows per (stage, pid, method,
tier, attack) key: failed attempts (``n_samples == 0``), pre-protocol rows
kept for audit, and post-repair reruns.  Every analysis must therefore
select exactly one successful row per key, and the selection rule must be
defined in one place so the paper, the tables, and the released CSVs can
never drift apart.  The rules implemented here match Appendix A.1:

* primary grid (Stage A, IP-Adapter-FaceID): the original campaign cell is
  kept; integrity-repair reruns of the six-identity pilot half after
  ``PILOT_CUT`` are excluded (they are reported separately as the repaired
  pilots), as are ARCP rows forged before the seeded-protocol boundary;
* repaired pilots, Stage C, Stage O, and the InstantID grid: the latest
  successful row per key (the post-repair run is the cell of record).
"""

import pandas as pd

KEY = ["stage", "pid", "method", "tier", "attack"]

PILOT_IDS = {"celeb00025", "celeb00027", "celeb00028", "celeb00029",
             "celeb00030", "celeb00031"}
PILOT_CUT = "2026-10-12 22:00:00"
PILOT_RERUN_TIERS = {"t0", "t1_jpeg85", "t2_canvas_dpr1", "t5_i2i30"}
ARCP_CUT = "2026-10-13 00:00:00"
# Methods whose pilot-half cells were re-measured in the integrity-repair
# pass.  ARCP and ARCP-lambda-2 launched after the cut (their pilot rows are
# original-era by construction), and ASPL was never re-measured, so none of
# them may enter this set.
RERUN_METHODS = {"clean", "random", "fsmg", "fsmgj"}


def successful(df):
    """Rows that completed a cell: ``n_samples > 0``."""
    ns = pd.to_numeric(df.get("n_samples"), errors="coerce")
    return df[ns.fillna(0) > 0].copy()


def latest_per_key(df):
    """Keep the latest successful row per key (ties broken by file order)."""
    df = successful(df)
    ts = pd.to_datetime(df.get("ts"), errors="coerce")
    ordered = df.assign(_ts=ts).sort_values("_ts", kind="stable")
    return ordered.groupby(KEY, as_index=False).tail(1).drop(columns="_ts")


def drop_pilot_reruns(df):
    """Exclude integrity-repair reruns from the primary grid.

    Only the methods re-measured in the repair pass (``RERUN_METHODS``) are
    affected; ARCP/ARCP-lambda rows launched after the cut are original-era
    and must survive."""
    ts = pd.to_datetime(df.get("ts"), errors="coerce")
    rerun = (df["pid"].isin(PILOT_IDS) & (ts >= pd.Timestamp(PILOT_CUT))
             & df["tier"].isin(PILOT_RERUN_TIERS) & df["method"].isin(RERUN_METHODS))
    pre_arcp = df["method"].isin({"arcp", "arcp2"}) & (ts < pd.Timestamp(ARCP_CUT))
    return df[~(rerun | pre_arcp)]


def primary_frame(df):
    """Rows feeding the 40-identity primary grid: one row per key, original
    campaign era for rerun cells."""
    return latest_per_key(drop_pilot_reruns(df))


def repaired_frame(df):
    """Rows feeding the repaired pilots, Stage C/O, and InstantID tables:
    latest post-repair run per key."""
    return latest_per_key(df)


def pilot_frame(df):
    """All successful post-repair rows on the six-identity pilot half.

    Feeds the repaired T3 column and its matched T0 normalization."""
    df = successful(df)
    ts = pd.to_datetime(df.get("ts"), errors="coerce")
    return df[df["pid"].isin(PILOT_IDS) & (ts >= pd.Timestamp(PILOT_CUT))]
