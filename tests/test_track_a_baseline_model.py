"""Tests for Track A baseline helpers."""

import numpy as np
import pandas as pd

from src.modeling.track_a.baseline import add_derived_features, compute_regression_metrics


def test_add_derived_features_builds_category_count_and_first_review_flag() -> None:
    df = pd.DataFrame(
        {
            "review_id": ["r1", "r2", "r3"],
            "review_date": pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"]),
            "categories": ["Food, Restaurants", None, "Beauty"],
            "review_stars": [4.0, 3.0, 5.0],
            "text_char_count": [100, 120, 90],
            "text_word_count": [20, 24, 18],
            "user_tenure_days": [10, 20, 30],
            "review_year": [2020, 2020, 2020],
            "review_month": [1, 1, 1],
            "latitude": [1.0, 2.0, 3.0],
            "longitude": [4.0, 5.0, 6.0],
            "user_prior_review_count": [0.0, 2.0, 1.0],
            "user_prior_avg_stars": [np.nan, 3.5, 4.0],
            "user_prior_std_stars": [np.nan, 1.2, 0.8],
            "biz_prior_review_count": [1.0, 5.0, 7.0],
            "biz_prior_avg_stars": [4.0, 3.5, 4.5],
            "biz_prior_std_stars": [0.5, 0.6, 0.7],
        }
    )

    result = add_derived_features(df)

    assert result["category_count"].tolist() == [2.0, 0.0, 1.0]
    assert result["is_first_review"].tolist() == [1.0, 0.0, 0.0]
    assert "categories" not in result.columns
    assert "review_id" not in result.columns
    assert "review_date" not in result.columns


def test_compute_regression_metrics_clips_to_star_bounds() -> None:
    y_true = np.array([1.0, 3.0, 5.0])
    y_pred = np.array([-2.0, 3.2, 8.0])

    metrics = compute_regression_metrics(y_true, y_pred)

    assert metrics["mae"] >= 0.0
    assert metrics["rmse"] >= 0.0
    assert 0.0 <= metrics["within_1_star_accuracy"] <= 1.0
    assert metrics["within_1_star_accuracy"] == 1.0
