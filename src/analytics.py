from __future__ import annotations
import numpy as np
import pandas as pd


def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    """Normalize weight values so they sum to 1.0.

    Parameters
    ----------
    weights:
        Mapping from field name to its weight (may be any positive number).

    Returns
    -------
    dict[str, float]
        Normalized weights that sum to ``1.0``.

    Raises
    ------
    ValueError
        If ``weights`` is empty, contains negative values or the total weight
        is not positive.  This guards against subtle bugs later in the
        calculation pipeline.
    """

    if not weights:
        raise ValueError("weights mapping must not be empty")
    if any(v < 0 for v in weights.values()):
        raise ValueError("weights must be non-negative")

    total = sum(weights.values())
    if total <= 0:
        raise ValueError("total weight must be positive")

    return {k: v / total for k, v in weights.items()}


def compute_overall_score(df: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
    """Compute a weighted overall score for each row if applicable.

    The function is defensive against empty inputs and non-numeric values so
    that upstream data issues do not crash the application.  Any fields missing
    from ``df`` are simply ignored.
    """

    if df.empty or not weights:
        return df

    def overall(row: pd.Series) -> float:
        total = 0.0
        for key, w in weights.items():
            if key in df.columns:
                try:
                    val = float(row.get(key, np.nan))
                except (TypeError, ValueError):
                    val = np.nan
                if not np.isnan(val):
                    total += w * val
        return total

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
