"""Regression coverage for Track E Stage 9 summary and validity scan."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.eda.track_e.common import TrackEPaths
from src.eda.track_e.summary_report import build_summary_report, run_validity_scan


def _make_paths(tmp_path: Path) -> TrackEPaths:
    curated = tmp_path / "curated"
    curated.mkdir(parents=True, exist_ok=True)
    tables = tmp_path / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    figures = tmp_path / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    logs = tmp_path / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    return TrackEPaths(
        curated_dir=curated,
        tables_dir=tables,
        figures_dir=figures,
        logs_dir=logs,
        review_fact_path=curated / "review_fact.parquet",
        business_path=curated / "business.parquet",
        user_path=curated / "user.parquet",
    )


def _write_parquet(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def test_summary_report_includes_all_sections(tmp_path: Path) -> None:
    paths = _make_paths(tmp_path)
    _write_parquet(
        paths.tables_dir / "track_e_s1_subgroup_definitions.parquet",
        pd.DataFrame(
            [
                {
                    "business_id": "b1",
                    "city": "Phoenix",
                    "primary_category": "Food",
                    "price_tier": "low",
                    "review_volume_tier": "10-50",
                },
                {
                    "business_id": "b2",
                    "city": "Vegas",
                    "primary_category": "Food",
                    "price_tier": "medium",
                    "review_volume_tier": "10-50",
                },
            ]
        ),
    )
    _write_parquet(
        paths.tables_dir / "track_e_s1_subgroup_summary.parquet",
        pd.DataFrame(
            [
                {"subgroup_type": "city", "subgroup_value": "Phoenix", "business_count": 1},
                {"subgroup_type": "price_tier", "subgroup_value": "low", "business_count": 1},
            ]
        ),
    )
    _write_parquet(
        paths.tables_dir / "track_e_s2_coverage_by_subgroup.parquet",
        pd.DataFrame(
            [
                {
                    "subgroup_type": "city",
                    "subgroup_value": "Phoenix",
                    "business_count": 1,
                    "review_count": 50,
                    "user_count": 40,
                    "mean_stars": 4.0,
                    "mean_useful": 1.2,
                }
            ]
        ),
    )
    _write_parquet(
        paths.tables_dir / "track_e_s3_star_disparity.parquet",
        pd.DataFrame(
            [
                {
                    "subgroup_type": "primary_category",
                    "subgroup_value": "Food",
                    "review_count": 30,
                    "mean_stars": 4.1,
                },
                {
                    "subgroup_type": "price_tier",
                    "subgroup_value": "low",
                    "review_count": 30,
                    "mean_stars": 3.6,
                },
            ]
        ),
    )
    _write_parquet(
        paths.tables_dir / "track_e_s3_ks_test_results.parquet",
        pd.DataFrame(
            [
                {
                    "subgroup_type": "city",
                    "group_a": "Phoenix",
                    "group_b": "Vegas",
                    "ks_statistic": 0.2,
                    "p_value": 0.01,
                    "is_significant": True,
                    "_simpson_flag": True,
                }
            ]
        ),
    )
    _write_parquet(
        paths.tables_dir / "track_e_s4_usefulness_disparity.parquet",
        pd.DataFrame(
            [
                {
                    "subgroup_type": "city",
                    "subgroup_value": "Phoenix",
                    "review_count": 50,
                    "mean_useful": 1.2,
                    "median_useful": 1.0,
                    "pct_zero_useful": 0.1,
                }
            ]
        ),
    )
    _write_parquet(
        paths.tables_dir / "track_e_s5_imbalance_report.parquet",
        pd.DataFrame(
            [
                {
                    "subgroup_type": "city",
                    "metric": "review_count",
                    "gini_coefficient": 0.3,
                    "top_pct_share": 60.0,
                    "bottom_pct_share": 5.0,
                    "subgroup_count": 2,
                }
            ]
        ),
    )
    _write_parquet(
        paths.tables_dir / "track_e_s6_proxy_correlations.parquet",
        pd.DataFrame(
            [
                {
                    "feature": "review_count_asof",
                    "subgroup_indicator": "city_Phoenix",
                    "correlation": 0.5,
                    "p_value": 0.01,
                    "is_proxy_risk": True,
                }
            ]
        ),
    )
    _write_parquet(
        paths.tables_dir / "track_e_s7_fairness_metrics.parquet",
        pd.DataFrame(
            [
                {
                    "subgroup_type": "city",
                    "metric_name": "demographic_parity_gap_stars",
                    "group_a": "Phoenix",
                    "group_b": "Vegas",
                    "group_a_value": 4.1,
                    "group_b_value": 3.6,
                    "gap": 0.5,
                    "ratio": 0.8,
                    "exceeds_threshold": True,
                }
            ]
        ),
    )
    (paths.tables_dir / "track_e_s8_mitigation_candidates.md").write_text("# Mitigations\n", encoding="utf-8")

    config = {"subgroups": {"min_group_size": 10}}
    findings = [
        {
            "artifact_path": str(paths.tables_dir / "track_e_s2_coverage_by_subgroup.parquet"),
            "status": "WARN",
            "detail": "placeholder",
        }
    ]
    summary = build_summary_report(paths, config, findings)

    assert "## 2. Hypothesis Assessment" in summary
    assert "Proxy correlation analysis" in summary
    assert "Validity scan recorded" in summary
    assert "## 9. Artifacts Index" in summary


def test_validity_scan_detects_issues(tmp_path: Path) -> None:
    paths = _make_paths(tmp_path)
    _write_parquet(
        paths.tables_dir / "track_e_s2_coverage_by_subgroup.parquet",
        pd.DataFrame(
            [
                {"business_id": "b1", "text": "bad", "business_count": 5, "review_count": 3}
            ]
        ),
    )
    config = {"subgroups": {"min_group_size": 10}}
    findings = run_validity_scan(paths, config)
    assert any("banned text" in f["detail"] for f in findings)
    assert any("business_count" in f["detail"] for f in findings)


def test_validity_scan_ignores_non_aggregate_subgroup_count(tmp_path: Path) -> None:
    paths = _make_paths(tmp_path)
    _write_parquet(
        paths.tables_dir / "track_e_s5_imbalance_report.parquet",
        pd.DataFrame(
            [
                {
                    "subgroup_type": "city",
                    "metric": "review_count",
                    "gini_coefficient": 0.3,
                    "top_pct_share": 0.6,
                    "bottom_pct_share": 0.1,
                    "subgroup_count": 2,
                }
            ]
        ),
    )
    config = {"subgroups": {"min_group_size": 10}}
    findings = run_validity_scan(paths, config)
    assert not any("subgroup_count" in f["detail"] for f in findings)
