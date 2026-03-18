"""Unit tests for Track E proxy correlation helpers."""

from __future__ import annotations

import pandas as pd

from src.eda.track_e.proxy_risk import compute_proxy_correlations


def _make_test_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    features = pd.DataFrame(
        {
            "business_id": [f"b{i}" for i in range(6)],
            "review_count_asof": [10, 12, 1, 2, 11, 13],
            "avg_stars_asof": [5.0, 4.8, 2.0, 2.1, 4.9, 4.7],
            "text_length_mean_asof": [100, 110, 130, 140, 115, 105],
            "useful_mean_asof": [3, 2, 0, 0.5, 3.2, 2.9],
        }
    )
    subgroup_defs = pd.DataFrame(
        {
            "business_id": features["business_id"],
            "city": ["Phoenix", "Phoenix", "Vegas", "Vegas", "Phoenix", "Phoenix"],
            "price_tier": ["high", "high", "low", "low", "high", "high"],
        }
    )
    return features, subgroup_defs


def test_proxy_correlation_schema_and_values() -> None:
    features, subgroup_defs = _make_test_data()
    result = compute_proxy_correlations(
        features_df=features,
        subgroup_defs=subgroup_defs,
        candidate_features=["review_count_asof", "avg_stars_asof", "useful_mean_asof"],
        correlation_threshold=0.3,
        min_group_size=2,
    )

    assert set(result.columns) == {
        "feature",
        "subgroup_indicator",
        "correlation",
        "p_value",
        "is_proxy_risk",
    }
    assert not result.empty
    assert result["correlation"].between(-1, 1).all()
    assert result["p_value"].between(0, 1).all()
    assert result["is_proxy_risk"].isin({True, False}).all()


def test_proxy_risk_flags_drive_thresholds() -> None:
    features, subgroup_defs = _make_test_data()
    low_threshold = compute_proxy_correlations(
        features_df=features,
        subgroup_defs=subgroup_defs,
        candidate_features=["avg_stars_asof"],
        correlation_threshold=0.2,
        min_group_size=2,
    )
    high_threshold = compute_proxy_correlations(
        features_df=features,
        subgroup_defs=subgroup_defs,
        candidate_features=["avg_stars_asof"],
        correlation_threshold=1.01,
        min_group_size=2,
    )

    assert any(low_threshold["is_proxy_risk"])
    assert not any(high_threshold["is_proxy_risk"])
