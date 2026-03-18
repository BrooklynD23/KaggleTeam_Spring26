from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.eda.track_e.fairness_baseline import METRIC_COLUMNS, compute_fairness_metrics, run


def _build_star_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"subgroup_type": "city", "subgroup_value": "Phoenix", "mean_stars": 4.5},
            {"subgroup_type": "city", "subgroup_value": "Vegas", "mean_stars": 3.5},
            {"subgroup_type": "price_tier", "subgroup_value": "low", "mean_stars": 4.2},
            {"subgroup_type": "price_tier", "subgroup_value": "high", "mean_stars": 4.0},
        ]
    )


def _build_useful_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"subgroup_type": "city", "subgroup_value": "Phoenix", "mean_useful": 2.0},
            {"subgroup_type": "city", "subgroup_value": "Vegas", "mean_useful": 1.4},
        ]
    )


def _build_coverage_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"subgroup_type": "city", "subgroup_value": "Phoenix", "review_count": 100},
            {"subgroup_type": "city", "subgroup_value": "Vegas", "review_count": 20},
            {"subgroup_type": "price_tier", "subgroup_value": "low", "review_count": 80},
            {"subgroup_type": "price_tier", "subgroup_value": "high", "review_count": 40},
        ]
    )


def _build_ks_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "subgroup_type": "city",
                "group_a": "Phoenix",
                "group_b": "Vegas",
                "ks_statistic": 0.12,
            },
            {
                "subgroup_type": "price_tier",
                "group_a": "low",
                "group_b": "high",
                "ks_statistic": 0.05,
            },
        ]
    )


def test_compute_fairness_metrics_flags_demographic_and_coverage_gaps() -> None:
    star_df = _build_star_df()
    useful_df = _build_useful_df()
    coverage_df = _build_coverage_df()
    ks_df = _build_ks_df()

    config = {"fairness": {"demographic_parity_threshold": 0.5, "coverage_parity_min_ratio": 0.3}}

    result = compute_fairness_metrics(star_df, useful_df, coverage_df, ks_df, config)

    star_gap = result.loc[
        (result["metric_name"] == "demographic_parity_gap_stars")
        & (result["subgroup_type"] == "city")
    ]
    assert not star_gap.empty
    assert star_gap["gap"].iloc[0] == 1.0
    assert bool(star_gap["exceeds_threshold"].iloc[0]) is True

    useful_gap = result.loc[
        (result["metric_name"] == "demographic_parity_gap_useful")
        & (result["subgroup_type"] == "city")
    ]
    assert useful_gap["gap"].iloc[0] == pytest.approx(0.6)
    assert bool(useful_gap["exceeds_threshold"].iloc[0]) is True

    coverage_ratio = result.loc[
        (result["metric_name"] == "coverage_parity_ratio")
        & (result["subgroup_type"] == "city")
    ]
    assert coverage_ratio["ratio"].iloc[0] == 0.2
    assert bool(coverage_ratio["exceeds_threshold"].iloc[0]) is True

    calibration_gap = result.loc[result["metric_name"] == "calibration_gap"]
    assert calibration_gap["gap"].eq(0.12).any()


def test_compute_fairness_metrics_respects_coverage_threshold() -> None:
    coverage_df = pd.DataFrame(
        [
            {"subgroup_type": "city", "subgroup_value": "Phoenix", "review_count": 50},
            {"subgroup_type": "city", "subgroup_value": "Vegas", "review_count": 40},
        ]
    )

    star_df = _build_star_df()
    useful_df = _build_useful_df()
    ks_df = _build_ks_df()

    config = {"fairness": {"demographic_parity_threshold": 1.0, "coverage_parity_min_ratio": 0.8}}

    result = compute_fairness_metrics(star_df, useful_df, coverage_df, ks_df, config)

    coverage_ratio = result.loc[
        (result["metric_name"] == "coverage_parity_ratio")
        & (result["subgroup_type"] == "city")
    ]
    assert coverage_ratio["ratio"].iloc[0] == 0.8
    assert bool(coverage_ratio["exceeds_threshold"].iloc[0]) is False


def test_compute_fairness_metrics_handles_missing_subgroup_type_column() -> None:
    config = {"fairness": {"demographic_parity_threshold": 0.1, "coverage_parity_min_ratio": 0.5}}
    result = compute_fairness_metrics(
        star_df=pd.DataFrame({"mean_stars": [4.0]}),
        useful_df=pd.DataFrame({"mean_useful": [1.0]}),
        coverage_df=pd.DataFrame({"review_count": [100]}),
        ks_df=pd.DataFrame({"ks_statistic": [0.2]}),
        config=config,
    )

    assert result.empty
    assert list(result.columns) == METRIC_COLUMNS


def test_run_writes_empty_metrics_when_upstream_artifacts_are_missing(tmp_path: Path) -> None:
    config = {
        "paths": {
            "curated_dir": str(tmp_path / "curated"),
            "tables_dir": str(tmp_path / "tables"),
            "figures_dir": str(tmp_path / "figures"),
            "logs_dir": str(tmp_path / "logs"),
        },
        "fairness": {"demographic_parity_threshold": 0.1, "coverage_parity_min_ratio": 0.5},
    }
    for dirname in ("curated", "tables", "figures", "logs"):
        (tmp_path / dirname).mkdir(parents=True, exist_ok=True)

    run(config)

    out_path = tmp_path / "tables" / "track_e_s7_fairness_metrics.parquet"
    assert out_path.exists()
    out_df = pd.read_parquet(out_path)
    assert out_df.empty
    assert list(out_df.columns) == METRIC_COLUMNS
