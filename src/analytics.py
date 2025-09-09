from __future__ import annotations
import numpy as np
import pandas as pd


def compute_overall_score(df: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
    """Compute weighted overall score for each row if applicable."""
    def overall(row):
        s = 0.0
        for k, w in weights.items():
            if k in df.columns:
                s += w * float(row.get(k, np.nan))
        return s

    if any(k in df.columns for k in weights.keys()):
        df["overall_score"] = df.apply(overall, axis=1)
    return df


def compute_trends(df: pd.DataFrame, weight_keys: list[str]) -> tuple[pd.DataFrame, list[str]]:
    """Compute semester-to-semester deltas for weighted fields."""
    trend_fields = [k for k in weight_keys if k in df.columns]
    if "semester" in df.columns and "student_name" in df.columns and trend_fields:
        pivot = df.pivot_table(index="student_name", columns="semester", values=trend_fields, aggfunc="mean")
        pivot.columns = [f"{k}_{sem}" for (k, sem) in pivot.columns.to_flat_index()]
        pivot = pivot.reset_index()
        for k in trend_fields:
            col_a = f"{k}_א"
            col_b = f"{k}_ב"
            if col_a in pivot.columns and col_b in pivot.columns:
                pivot[f"delta_{k}"] = pivot[col_b] - pivot[col_a]
        merge_cols = ["student_name"] + [c for c in pivot.columns if c.startswith("delta_")]
        df = df.merge(pivot[merge_cols], on="student_name", how="left")
    return df, trend_fields


def apply_flags(df: pd.DataFrame, low_percentile_thr: int, drop_thr: int, trend_fields: list[str]) -> pd.DataFrame:
    """Apply criteria flags based on percentile and score drops."""
    flags = pd.Series([False] * len(df))
    if "national_percentile" in df.columns:
        flags = flags | (df["national_percentile"] < low_percentile_thr)
    for k in trend_fields:
        dcol = f"delta_{k}"
        if dcol in df.columns:
            flags = flags | (df[dcol] <= -abs(drop_thr))
    df["flagged"] = flags
    return df
