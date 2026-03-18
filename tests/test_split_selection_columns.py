"""Regression: Stage 5 must write canonical t1/t2, not legacy t1_date/t2_date."""

import pandas as pd
import pytest

from src.eda.track_a.split_selection import evaluate_candidates


def _make_reviews(n: int = 300) -> pd.DataFrame:
    dates = pd.date_range("2019-01-01", periods=n, freq="D")
    stars = [1, 2, 3, 4, 5] * (n // 5) + [3] * (n % 5)
    return pd.DataFrame({"review_date": dates, "review_stars": stars[:n]})


def test_evaluate_candidates_writes_canonical_t1_t2() -> None:
    """Stage 5 output must have 't1' and 't2', not 't1_date'/'t2_date'."""
    reviews = _make_reviews()
    candidates_cfg = [{"t1_pct": 33, "t2_pct": 66}]
    candidate_df, _ = evaluate_candidates(reviews, candidates_cfg, 0.10, 0.05)

    assert not candidate_df.empty
    assert "t1" in candidate_df.columns, "Stage 5 must write canonical 't1' column"
    assert "t2" in candidate_df.columns, "Stage 5 must write canonical 't2' column"
    assert "t1_date" not in candidate_df.columns, "Legacy 't1_date' must not appear"
    assert "t2_date" not in candidate_df.columns, "Legacy 't2_date' must not appear"


def test_evaluate_candidates_t1_t2_are_date_strings() -> None:
    """t1 and t2 values must be ISO-formatted date strings."""
    reviews = _make_reviews()
    candidates_cfg = [{"t1_pct": 33, "t2_pct": 66}]
    candidate_df, _ = evaluate_candidates(reviews, candidates_cfg, 0.10, 0.05)

    row = candidate_df.iloc[0]
    # Should be parseable as dates
    pd.Timestamp(row["t1"])
    pd.Timestamp(row["t2"])
    assert str(row["t1"]) < str(row["t2"]), "t1 must precede t2"
