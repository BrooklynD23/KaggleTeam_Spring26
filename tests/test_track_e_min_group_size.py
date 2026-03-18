"""Tests for Track E aggregate minimum group-size enforcement."""

from __future__ import annotations

import pandas as pd

from src.eda.track_e.coverage_profile import build_coverage_by_subgroup


def test_build_coverage_by_subgroup_drops_below_threshold_and_keeps_edge() -> None:
    """Coverage rows should be filtered by business_count using the provided threshold."""
    reviews_df = pd.DataFrame(
        [
            {"business_id": "b1", "user_id": "u1", "stars": 4.0, "useful": 1},
            {"business_id": "b2", "user_id": "u2", "stars": 5.0, "useful": 2},
            {"business_id": "b3", "user_id": "u3", "stars": 2.0, "useful": 0},
        ]
    )
    subgroup_defs = pd.DataFrame(
        [
            {
                "business_id": "b1",
                "city": "Phoenix",
                "primary_category": "Food",
                "price_tier": "medium",
                "review_volume_tier": "<10",
            },
            {
                "business_id": "b2",
                "city": "Phoenix",
                "primary_category": "Food",
                "price_tier": "medium",
                "review_volume_tier": "<10",
            },
            {
                "business_id": "b3",
                "city": "Las Vegas",
                "primary_category": "Bars",
                "price_tier": "high",
                "review_volume_tier": "<10",
            },
        ]
    )

    result = build_coverage_by_subgroup(reviews_df, subgroup_defs, min_group_size=2)
    city_rows = result.loc[result["subgroup_type"] == "city"]

    assert city_rows["subgroup_value"].tolist() == ["Phoenix"]
    assert city_rows["business_count"].tolist() == [2]
