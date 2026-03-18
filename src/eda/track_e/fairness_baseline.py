"""Stage 7 — Fairness baseline metrics for Track E."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from src.common.config import load_config
from src.eda.track_e.common import ensure_output_dirs, resolve_paths, write_parquet

logger = logging.getLogger(__name__)

METRIC_COLUMNS = [
    "subgroup_type",
    "metric_name",
    "group_a",
    "group_b",
    "group_a_value",
    "group_b_value",
    "gap",
    "ratio",
    "exceeds_threshold",
]


def _load_optional_table(path: Path, expected_columns: list[str]) -> pd.DataFrame:
    """Load a parquet table if present, else return an empty typed shell."""
    if not path.exists():
        logger.warning("Missing upstream artifact %s; using empty table.", path.name)
        return pd.DataFrame(columns=expected_columns)
    df = pd.read_parquet(path)
    for column in expected_columns:
        if column not in df.columns:
            df[column] = pd.Series(dtype=object)
    return df


def _iter_subgroup_types(df: pd.DataFrame) -> list[str]:
    """Safely read subgroup types, tolerating missing or empty inputs."""
    if df.empty or "subgroup_type" not in df.columns:
        return []
    return sorted(df["subgroup_type"].dropna().astype(str).unique().tolist())


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return float(numerator) / float(denominator)


def _build_extreme_rows(
    df: pd.DataFrame,
    value_col: str,
) -> tuple[pd.Series | None, pd.Series | None]:
    if df.empty or value_col not in df.columns:
        return None, None
    try:
        max_idx = df[value_col].idxmax()
        min_idx = df[value_col].idxmin()
    except ValueError:
        return None, None
    return df.loc[max_idx], df.loc[min_idx]


def compute_fairness_metrics(
    star_df: pd.DataFrame,
    useful_df: pd.DataFrame,
    coverage_df: pd.DataFrame,
    ks_df: pd.DataFrame,
    config: dict[str, Any],
) -> pd.DataFrame:
    """Compute fairness metrics for each subgroup dimension.

    Args:
        star_df: Stage 3 star disparity table.
        useful_df: Stage 4 usefulness disparity table.
        coverage_df: Stage 2 coverage table.
        ks_df: Stage 3 KS test results table.
        config: Loaded Track E config dict.

    Returns:
        DataFrame with columns defined by METRIC_COLUMNS.
    """
    fairness_cfg = config.get("fairness", {})
    dp_threshold = float(fairness_cfg.get("demographic_parity_threshold", 0.1))
    coverage_threshold = float(fairness_cfg.get("coverage_parity_min_ratio", 0.5))

    rows: list[dict[str, Any]] = []

    for subgroup_type in _iter_subgroup_types(star_df):
        subset = star_df[star_df["subgroup_type"] == subgroup_type]
        max_row, min_row = _build_extreme_rows(subset, "mean_stars")
        if max_row is None or min_row is None:
            continue
        gap = float(max_row["mean_stars"]) - float(min_row["mean_stars"])
        rows.append(
            {
                "subgroup_type": subgroup_type,
                "metric_name": "demographic_parity_gap_stars",
                "group_a": str(max_row["subgroup_value"]),
                "group_b": str(min_row["subgroup_value"]),
                "group_a_value": float(max_row["mean_stars"]),
                "group_b_value": float(min_row["mean_stars"]),
                "gap": gap,
                "ratio": None,
                "exceeds_threshold": gap > dp_threshold,
            }
        )

    for subgroup_type in _iter_subgroup_types(useful_df):
        subset = useful_df[useful_df["subgroup_type"] == subgroup_type]
        max_row, min_row = _build_extreme_rows(subset, "mean_useful")
        if max_row is None or min_row is None:
            continue
        gap = float(max_row["mean_useful"]) - float(min_row["mean_useful"])
        rows.append(
            {
                "subgroup_type": subgroup_type,
                "metric_name": "demographic_parity_gap_useful",
                "group_a": str(max_row["subgroup_value"]),
                "group_b": str(min_row["subgroup_value"]),
                "group_a_value": float(max_row["mean_useful"]),
                "group_b_value": float(min_row["mean_useful"]),
                "gap": gap,
                "ratio": None,
                "exceeds_threshold": gap > dp_threshold,
            }
        )

    for subgroup_type in _iter_subgroup_types(coverage_df):
        subset = coverage_df[coverage_df["subgroup_type"] == subgroup_type]
        top_row, bottom_row = _build_extreme_rows(subset, "review_count")
        if top_row is None or bottom_row is None:
            continue
        top_count = float(top_row["review_count"])
        bottom_count = float(bottom_row["review_count"])
        ratio = _safe_ratio(bottom_count, top_count)
        gap = top_count - bottom_count
        rows.append(
            {
                "subgroup_type": subgroup_type,
                "metric_name": "coverage_parity_ratio",
                "group_a": str(top_row["subgroup_value"]),
                "group_b": str(bottom_row["subgroup_value"]),
                "group_a_value": top_count,
                "group_b_value": bottom_count,
                "gap": gap,
                "ratio": ratio,
                "exceeds_threshold": ratio < coverage_threshold,
            }
        )

    for subgroup_type in _iter_subgroup_types(ks_df):
        subset = ks_df[ks_df["subgroup_type"] == subgroup_type]
        if subset.empty or "ks_statistic" not in subset.columns:
            continue
        best = subset.loc[subset["ks_statistic"].idxmax()]
        gap = float(best["ks_statistic"])
        rows.append(
            {
                "subgroup_type": subgroup_type,
                "metric_name": "calibration_gap",
                "group_a": str(best.get("group_a", "")),
                "group_b": str(best.get("group_b", "")),
                "group_a_value": gap,
                "group_b_value": 0.0,
                "gap": gap,
                "ratio": None,
                "exceeds_threshold": False,
            }
        )

    if not rows:
        return pd.DataFrame(columns=METRIC_COLUMNS)

    result = pd.DataFrame(rows)
    return result[METRIC_COLUMNS]


def run(config: dict[str, Any]) -> None:
    paths = resolve_paths(config)
    ensure_output_dirs(paths)

    star_path = paths.tables_dir / "track_e_s3_star_disparity.parquet"
    useful_path = paths.tables_dir / "track_e_s4_usefulness_disparity.parquet"
    coverage_path = paths.tables_dir / "track_e_s2_coverage_by_subgroup.parquet"
    ks_path = paths.tables_dir / "track_e_s3_ks_test_results.parquet"

    star_df = _load_optional_table(
        star_path,
        ["subgroup_type", "subgroup_value", "mean_stars"],
    )
    useful_df = _load_optional_table(
        useful_path,
        ["subgroup_type", "subgroup_value", "mean_useful"],
    )
    coverage_df = _load_optional_table(
        coverage_path,
        ["subgroup_type", "subgroup_value", "review_count"],
    )
    ks_df = _load_optional_table(
        ks_path,
        ["subgroup_type", "group_a", "group_b", "ks_statistic"],
    )

    fairness_df = compute_fairness_metrics(
        star_df,
        useful_df,
        coverage_df,
        ks_df,
        config,
    )

    out_path = paths.tables_dir / "track_e_s7_fairness_metrics.parquet"
    write_parquet(fairness_df, out_path)
    logger.info("Wrote fairness metrics: %s", out_path)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(description="Stage 7 — Track E Fairness Baseline")
    parser.add_argument("--config", required=True, help="Path to track_e.yaml config file")
    args = parser.parse_args()
    _config = load_config(args.config)
    run(_config)
