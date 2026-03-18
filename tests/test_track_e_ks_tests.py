"""Tests for Track E KS disparity helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.eda.track_e.star_disparity import check_simpsons_paradox, compute_ks_tests, run


def test_compute_ks_tests_returns_bounded_statistics_and_simpson_flag() -> None:
    """KS outputs should stay in valid ranges and expose the paradox flag column."""
    reviews_with_defs = pd.DataFrame(
        [
            {"business_id": "b1", "stars": 1.0, "city": "Phoenix", "primary_category": "Food"},
            {"business_id": "b2", "stars": 2.0, "city": "Phoenix", "primary_category": "Food"},
            {"business_id": "b3", "stars": 4.0, "city": "Las Vegas", "primary_category": "Food"},
            {"business_id": "b4", "stars": 5.0, "city": "Las Vegas", "primary_category": "Food"},
            {"business_id": "b5", "stars": 5.0, "city": "Phoenix", "primary_category": "Bars"},
            {"business_id": "b6", "stars": 4.0, "city": "Phoenix", "primary_category": "Bars"},
            {"business_id": "b7", "stars": 2.0, "city": "Las Vegas", "primary_category": "Bars"},
            {"business_id": "b8", "stars": 1.0, "city": "Las Vegas", "primary_category": "Bars"},
        ]
    )

    ks_results = compute_ks_tests(
        reviews_with_defs,
        dimension="city",
        min_group_size=2,
        significance=0.05,
    )
    flagged = check_simpsons_paradox(
        reviews_with_defs,
        primary_dimension="city",
        conditioning_variable="primary_category",
        ks_results=ks_results,
    )
    result_df = pd.DataFrame(flagged)

    assert not result_df.empty
    assert result_df["ks_statistic"].between(0, 1).all()
    assert result_df["p_value"].between(0, 1).all()
    assert "_simpson_flag" in result_df.columns


def test_run_uses_disparity_fallback_when_quality_min_ks_is_missing(tmp_path: Path) -> None:
    config = {
        "paths": {
            "curated_dir": str(tmp_path / "curated"),
            "tables_dir": str(tmp_path / "tables"),
            "figures_dir": str(tmp_path / "figures"),
            "logs_dir": str(tmp_path / "logs"),
        },
        "subgroups": {"min_group_size": 10, "top_n_cities": 20},
        "disparity": {"ks_test_significance": 0.05, "min_pairwise_comparisons": 7},
        "simpson": {"enabled": True, "conditioning_variable": "primary_category"},
        # Intentionally omit quality.min_ks_comparisons to verify fallback path.
        "quality": {},
    }
    for dirname in ("curated", "tables", "figures", "logs"):
        (tmp_path / dirname).mkdir(parents=True, exist_ok=True)

    run(config)

    ks_path = tmp_path / "tables" / "track_e_s3_ks_test_results.parquet"
    assert ks_path.exists()
    ks_df = pd.read_parquet(ks_path)
    assert list(ks_df.columns) == [
        "subgroup_type",
        "group_a",
        "group_b",
        "ks_statistic",
        "p_value",
        "is_significant",
        "_simpson_flag",
    ]
