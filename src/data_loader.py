from __future__ import annotations
import pandas as pd

numeric_keys = [
    "quiz_avg",
    "quarter_exam",
    "midterm_mock",
    "half_semester_final",
    "national_percentile",
    "homework_rate",
]


def load_excel(file) -> pd.DataFrame:
    """Read an uploaded Excel file into a DataFrame."""
    return pd.read_excel(file)


def map_columns(df_raw: pd.DataFrame, mappings: dict[str, str]) -> pd.DataFrame:
    """Return DataFrame with columns renamed to canonical keys."""
    df = pd.DataFrame()
    for key, col in mappings.items():
        if col != "(ללא)" and col in df_raw.columns:
            df[key] = df_raw[col]
    return df


def normalize_dataframe(df_raw: pd.DataFrame, mappings: dict[str, str]) -> pd.DataFrame:
    """Return DataFrame with columns renamed to canonical keys and numeric fields coerced."""
    df = map_columns(df_raw, mappings)
    for nk in numeric_keys:
        if nk in df.columns:
            df[nk] = pd.to_numeric(df[nk], errors="coerce")
    return df
