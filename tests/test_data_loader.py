import pandas as pd
import pytest

from src.data_loader import load_excel, map_columns, normalize_dataframe


def test_load_excel_sample():
    df = load_excel("data/sample_class.xlsx")
    assert not df.empty


def test_map_columns_and_normalize():
    df_raw = pd.DataFrame({
        "Name": ["A"],
        "Quiz": ["90"],
        "Extra": [1],
    })
    mappings = {"student_name": "Name", "quiz_avg": "Quiz", "quarter_exam": "(ללא)"}
    mapped = map_columns(df_raw, mappings)
    assert list(mapped.columns) == ["student_name", "quiz_avg"]
    normalized = normalize_dataframe(df_raw, mappings)
    assert normalized["quiz_avg"].iloc[0] == 90
    assert "quarter_exam" not in normalized.columns
    df_raw2 = pd.DataFrame({"Quiz": ["notnum"]})
    mappings2 = {"quiz_avg": "Quiz"}
    norm2 = normalize_dataframe(df_raw2, mappings2)
    assert pd.isna(norm2["quiz_avg"].iloc[0])
