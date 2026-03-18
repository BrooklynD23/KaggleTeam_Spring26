"""Tests for Track E subgroup definition logic."""

from __future__ import annotations

import pandas as pd

from src.eda.track_e.subgroup_definition import build_subgroup_definitions


def test_build_subgroup_definitions_assigns_exactly_one_value_per_dimension() -> None:
    """Each business should map to one row with one label per subgroup dimension."""
    business_df = pd.DataFrame(
        [
            {
                "business_id": "b1",
                "city": "Phoenix",
                "state": "AZ",
                "categories": "Restaurants, Mexican",
                "attributes": '{"RestaurantsPriceRange2": "2"}',
            },
            {
                "business_id": "b2",
                "city": "Las Vegas",
                "state": "NV",
                "categories": None,
                "attributes": None,
            },
        ]
    )
    review_counts = pd.Series({"b1": 8, "b2": 75})
    config = {
        "subgroups": {
            "price_tier_labels": {1: "low", 2: "medium", 3: "high", 4: "premium"},
            "price_tier_missing_label": "missing",
            "review_volume_tier_boundaries": [10, 50],
        }
    }

    result = build_subgroup_definitions(business_df, review_counts, config)

    assert result["business_id"].is_unique
    assert len(result) == 2
    assert result.columns.tolist() == [
        "business_id",
        "city",
        "state",
        "primary_category",
        "price_tier",
        "review_volume_tier",
    ]
    assert result[["city", "primary_category", "price_tier", "review_volume_tier"]].notna().all().all()
    assert result.loc[result["business_id"] == "b1", "primary_category"].item() == "Restaurants"
    assert result.loc[result["business_id"] == "b2", "primary_category"].item() == "unknown"
    assert result.loc[result["business_id"] == "b1", "review_volume_tier"].item() == "<10"
    assert result.loc[result["business_id"] == "b2", "review_volume_tier"].item() == "50+"
