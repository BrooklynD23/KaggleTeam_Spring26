"""Focused regression tests for Track D cohort and evaluation helpers."""

from __future__ import annotations

import pandas as pd

from src.eda.track_d.business_cold_start import build_business_cold_start_cohort
from src.eda.track_d.business_early_signals import build_business_early_signals
from src.eda.track_d.evaluation_cohorts import exclude_seen_businesses
from src.eda.track_d.user_cold_start import build_user_cold_start_cohort


def test_business_cold_start_uses_asof_counts_not_future_reviews() -> None:
    reviews = pd.DataFrame(
        [
            {"review_id": "r1", "business_id": "b1", "review_date": "2020-01-20"},
            {"review_id": "r2", "business_id": "b2", "review_date": "2020-01-05"},
        ]
    )
    business_universe = pd.DataFrame(
        [
            {"business_id": "b1", "city": "Phoenix", "state": "AZ", "categories": "Food, Grocery"},
            {"business_id": "b2", "city": "Phoenix", "state": "AZ", "categories": "Food, Grocery"},
        ]
    )

    cohort = build_business_cold_start_cohort(
        reviews=reviews,
        business_universe=business_universe,
        as_of_dates=["2020-01-10"],
        thresholds={"zero_history": 0, "sparse_history": 3, "emerging": 10},
        recency_windows=[30],
    )

    b1 = cohort.loc[cohort["business_id"] == "b1"].iloc[0]
    b2 = cohort.loc[cohort["business_id"] == "b2"].iloc[0]

    assert int(b1["prior_review_count"]) == 0
    assert b1["cohort_label"] == "zero_history"
    assert int(b2["prior_review_count"]) == 1
    assert b2["cohort_label"] == "sparse_history"
    assert bool(b2["seen_within_30d"])


def test_business_early_signals_null_interaction_features_for_zero_history() -> None:
    cohort_df = pd.DataFrame(
        [
            {
                "business_id": "b1",
                "city": "Phoenix",
                "state": "AZ",
                "categories": "Food, Grocery",
                "primary_category": "Food",
                "as_of_date": "2020-01-10",
                "prior_review_count": 0,
                "cohort_label": "zero_history",
                "subtrack": "D1",
            },
            {
                "business_id": "b2",
                "city": "Phoenix",
                "state": "AZ",
                "categories": "Food, Grocery",
                "primary_category": "Food",
                "as_of_date": "2020-01-10",
                "prior_review_count": 2,
                "cohort_label": "sparse_history",
                "subtrack": "D1",
            },
        ]
    )
    business_df = pd.DataFrame(
        [
            {
                "business_id": "b1",
                "city": "Phoenix",
                "state": "AZ",
                "categories": "Food, Grocery",
                "attributes": '{"RestaurantsPriceRange2": "2"}',
                "hours": '{"Mon": "9-5"}',
                "latitude": 33.1,
                "longitude": -112.0,
            },
            {
                "business_id": "b2",
                "city": "Phoenix",
                "state": "AZ",
                "categories": "Food, Grocery",
                "attributes": '{"RestaurantsPriceRange2": "1"}',
                "hours": '{"Mon": "9-5"}',
                "latitude": 33.2,
                "longitude": -112.1,
            },
        ]
    )
    review_df = pd.DataFrame(
        [
            {"business_id": "b2", "review_date": "2020-01-02", "review_stars": 4.0, "text_word_count": 10},
            {"business_id": "b2", "review_date": "2020-01-03", "review_stars": 5.0, "text_word_count": 20},
        ]
    )
    tip_df = pd.DataFrame(
        [
            {"business_id": "b1", "tip_date": "2020-01-01"},
            {"business_id": "b2", "tip_date": "2020-01-04"},
        ]
    )
    checkin_df = pd.DataFrame(
        [
            {"business_id": "b1", "checkin_date": "2020-01-01"},
            {"business_id": "b2", "checkin_date": "2020-01-05"},
        ]
    )

    signals = build_business_early_signals(cohort_df, business_df, review_df, tip_df, checkin_df)
    zero_row = signals.loc[signals["business_id"] == "b1"].iloc[0]
    sparse_row = signals.loc[signals["business_id"] == "b2"].iloc[0]

    assert pd.isna(zero_row["prior_review_mean_stars"])
    assert pd.isna(zero_row["prior_review_mean_length"])
    assert pd.isna(zero_row["prior_tip_count"])
    assert pd.isna(zero_row["prior_checkin_count"])
    assert float(sparse_row["prior_review_mean_stars"]) == 4.5
    assert float(sparse_row["prior_review_mean_length"]) == 15.0
    assert float(sparse_row["prior_tip_count"]) == 1.0
    assert float(sparse_row["prior_checkin_count"]) == 1.0


def test_user_cold_start_uses_asof_counts_not_future_reviews() -> None:
    """D2 cohort: prior_review_count must not include reviews on/after as_of_date."""
    reviews = pd.DataFrame(
        [
            {"review_id": "r1", "user_id": "u1", "review_date": "2020-01-05"},
            {"review_id": "r2", "user_id": "u1", "review_date": "2020-01-15"},
            {"review_id": "r3", "user_id": "u2", "review_date": "2020-01-03"},
        ]
    )
    tips: pd.DataFrame = pd.DataFrame(columns=["user_id", "tip_date"])

    cohort = build_user_cold_start_cohort(
        review_df=reviews,
        tip_df=tips,
        as_of_dates=["2020-01-10"],
        primary_k=0,
    )

    u1 = cohort.loc[cohort["user_id"] == "u1"].iloc[0]
    u2 = cohort.loc[cohort["user_id"] == "u2"].iloc[0]

    # u1 has r1 (2020-01-05) before as_of; r2 (2020-01-15) must NOT be counted
    assert int(u1["prior_review_count"]) == 1
    assert int(u2["prior_review_count"]) == 1


def test_exclude_seen_businesses_removes_prior_items() -> None:
    candidates = pd.DataFrame(
        {
            "candidate_business_id": ["b1", "b2", "b3"],
            "score": [3, 2, 1],
        }
    )

    filtered = exclude_seen_businesses(candidates, {"b2"})

    assert filtered["candidate_business_id"].tolist() == ["b1", "b3"]
