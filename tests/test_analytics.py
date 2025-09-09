import pandas as pd
import pytest

from src.analytics import (
    normalize_weights,
    compute_trends,
    apply_flags,
    compute_overall_score,
)


def test_normalize_weights():
    weights = {"quiz_avg": 2.0, "quarter_exam": 6.0}
    normalized = normalize_weights(weights)
    assert pytest.approx(1.0) == sum(normalized.values())
    assert normalized["quiz_avg"] == pytest.approx(0.25)
    assert normalized["quarter_exam"] == pytest.approx(0.75)


def test_normalize_weights_invalid():
    with pytest.raises(ValueError):
        normalize_weights({})
    with pytest.raises(ValueError):
        normalize_weights({"a": -1})


def test_apply_flags_percentile():
    df = pd.DataFrame(
        {"student_name": ["A", "B"], "national_percentile": [5, 20]}
    )
    result = apply_flags(df, low_percentile_thr=10, drop_thr=5, trend_fields=[])
    assert result.loc[result["student_name"] == "A", "flagged"].iloc[0]
    assert not result.loc[result["student_name"] == "B", "flagged"].iloc[0]


def test_compute_trends():
    df = pd.DataFrame(
        [
            {"student_name": "A", "semester": "א", "quiz_avg": 80},
            {"student_name": "A", "semester": "ב", "quiz_avg": 90},
        ]
    )
    out, trend_fields = compute_trends(df, ["quiz_avg"])
    assert "quiz_avg" in trend_fields
    assert "delta_quiz_avg" in out.columns
    delta_val = out.loc[out["student_name"] == "A", "delta_quiz_avg"].iloc[0]
    assert delta_val == 10


def test_compute_trends_missing_column():
    df = pd.DataFrame({"student_name": ["A"], "semester": ["א"]})
    out, trend_fields = compute_trends(df, ["quiz_avg"])
    assert trend_fields == []
    assert "delta_quiz_avg" not in out.columns


def test_compute_overall_score():
    df = pd.DataFrame({"quiz_avg": [80], "quarter_exam": [90]})
    weights = normalize_weights({"quiz_avg": 0.4, "quarter_exam": 0.6})
    result = compute_overall_score(df.copy(), weights)
    expected = 0.4 * 80 + 0.6 * 90
    assert result["overall_score"].iloc[0] == pytest.approx(expected)


def test_compute_overall_score_missing_and_empty():
    df = pd.DataFrame({"quiz_avg": [80]})
    weights = normalize_weights({"quiz_avg": 1.0, "quarter_exam": 1.0})
    result = compute_overall_score(df.copy(), weights)
    # missing "quarter_exam" column should simply ignore that weight
    assert result["overall_score"].iloc[0] == pytest.approx(40.0)
    empty = compute_overall_score(pd.DataFrame(), weights)
    assert empty.empty
