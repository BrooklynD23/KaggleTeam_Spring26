"""Tests for Track E no-demographic-inference safeguards."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.eda.track_e.common import write_parquet
from src.eda.track_e.subgroup_definition import build_subgroup_definitions


def test_write_parquet_rejects_forbidden_demographic_columns(tmp_path: Path) -> None:
    """Demographic-looking output columns must be blocked."""
    with pytest.raises(ValueError, match="income"):
        write_parquet(pd.DataFrame({"income": [1]}), tmp_path / "bad.parquet")


def test_subgroup_definition_uses_business_attributes_only() -> None:
    """Stage 1 subgroup definitions should expose only business-derived columns."""
    business_df = pd.DataFrame(
        [
            {
                "business_id": "b1",
                "city": "Phoenix",
                "state": "AZ",
                "categories": "Food, Grocery",
                "attributes": '{"RestaurantsPriceRange2": "1"}',
            }
        ]
    )
    review_counts = pd.Series({"b1": 5})
    config = {
        "subgroups": {
            "price_tier_labels": {1: "low", 2: "medium", 3: "high", 4: "premium"},
            "price_tier_missing_label": "missing",
            "review_volume_tier_boundaries": [10, 50],
        }
    }

    result = build_subgroup_definitions(business_df, review_counts, config)

    forbidden = {"gender", "race", "income", "ethnicity"}
    assert forbidden.isdisjoint({column.lower() for column in result.columns})
