"""Regression: feasibility_signoff must require meets_min_group_gate AND valid_pairs > 0."""

import pandas as pd
import pytest

from src.eda.track_b.training_feasibility import build_pairwise_stats


def _make_group_level(
    n_groups: int,
    age_bucket: str = "0-180",
    group_size: int = 10,
    tied_pairs: int = 0,
) -> pd.DataFrame:
    rows = []
    for i in range(n_groups):
        n = group_size
        raw = n * (n - 1) // 2
        rows.append(
            {
                "group_type": "business",
                "group_id": f"b{i}",
                "age_bucket": age_bucket,
                "group_size": n,
                "raw_pairs": raw,
                "tied_pairs": tied_pairs,
                "valid_pairs": raw - tied_pairs,
                "distinct_useful_count": 3,
                "binary_class_count": 2,
                "top_decile_class_count": 2,
                "graded_class_count": 3,
                "percentile_range": 0.5,
            }
        )
    return pd.DataFrame(rows)


def test_signoff_false_when_min_group_gate_fails() -> None:
    """feasibility_signoff must be False when meets_min_group_gate is False."""
    # Only 2 groups; min_qualifying_groups = 1000 → gate fails
    group_level = _make_group_level(n_groups=2)
    config = {"quality": {"min_qualifying_groups": 1000}}
    stats = build_pairwise_stats(group_level, config)

    bucket_row = stats[stats["age_bucket"] == "0-180"].iloc[0]
    assert not bucket_row["meets_min_group_gate"]
    assert not bucket_row["feasibility_signoff"], (
        "feasibility_signoff must be False when meets_min_group_gate is False, "
        "even if valid_pairs > 0."
    )


def test_signoff_false_when_no_valid_pairs() -> None:
    """feasibility_signoff must be False when valid_pairs == 0 even if gate passes."""
    group_level = _make_group_level(n_groups=2000, group_size=2, tied_pairs=1)
    # 2000 groups, each size 2 with 1 tied pair → valid_pairs = 0
    config = {"quality": {"min_qualifying_groups": 1000}}
    stats = build_pairwise_stats(group_level, config)

    bucket_row = stats[stats["age_bucket"] == "0-180"].iloc[0]
    assert bucket_row["meets_min_group_gate"]
    assert stats[stats["age_bucket"] == "0-180"]["valid_pairs"].sum() == 0
    assert not bucket_row["feasibility_signoff"], (
        "feasibility_signoff must be False when valid_pairs == 0."
    )


def test_signoff_true_when_both_conditions_met() -> None:
    """feasibility_signoff must be True only when gate passes AND valid_pairs > 0."""
    group_level = _make_group_level(n_groups=2000, group_size=10, tied_pairs=0)
    config = {"quality": {"min_qualifying_groups": 1000}}
    stats = build_pairwise_stats(group_level, config)

    bucket_row = stats[stats["age_bucket"] == "0-180"].iloc[0]
    assert bucket_row["meets_min_group_gate"]
    assert bucket_row["valid_pairs"] > 0
    assert bucket_row["feasibility_signoff"]
