"""Track E Stage 2 — Coverage Profile by Subgroup.

Computes review/business/user coverage for each subgroup dimension
defined in Stage 1 (city, primary_category, price_tier, review_volume_tier).
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.common.config import load_config
from src.common.db import connect_duckdb
from src.eda.track_e.common import (
    enforce_min_group_size,
    ensure_output_dirs,
    load_parquet,
    resolve_paths,
    save_placeholder_figure,
    write_parquet,
)

logger = logging.getLogger(__name__)

# Subgroup dimension columns produced by Stage 1.
_SUBGROUP_DIMS = ["city", "primary_category", "price_tier", "review_volume_tier"]


def _resolve_min_group_size(config: dict[str, Any]) -> int:
    """Return the Track E subgroup minimum size threshold."""
    return int(config.get("subgroups", {}).get("min_group_size", 10))


def _detect_stars_col(df: pd.DataFrame) -> str:
    """Return the stars column name, trying 'stars' then 'review_stars'.

    Raises:
        KeyError: If neither column is present.
    """
    if "stars" in df.columns:
        return "stars"
    if "review_stars" in df.columns:
        return "review_stars"
    raise KeyError(
        "reviews DataFrame has neither 'stars' nor 'review_stars' column; "
        f"available columns: {list(df.columns)}"
    )


def build_coverage_by_subgroup(
    reviews_df: pd.DataFrame,
    subgroup_defs: pd.DataFrame,
    min_group_size: int,
) -> pd.DataFrame:
    """Compute coverage metrics for each subgroup dimension.

    Joins reviews_df to subgroup_defs on business_id (inner join) then
    aggregates over each of the four dimension columns.

    Args:
        reviews_df: Review-fact rows; must contain business_id, user_id,
            stars (or review_stars), and useful.
        subgroup_defs: Stage-1 subgroup definitions; must contain
            business_id plus all four dimension columns.
        min_group_size: Minimum business_count to retain a subgroup row.

    Returns:
        Long-format DataFrame with columns: subgroup_type, subgroup_value,
        business_count, review_count, user_count, mean_stars, mean_useful.
    """
    stars_col = _detect_stars_col(reviews_df)

    # Narrow to needed columns before the join to keep memory usage low.
    review_cols = ["business_id", "user_id", stars_col, "useful"]
    reviews_narrow = reviews_df[review_cols].copy()

    def_cols = ["business_id"] + _SUBGROUP_DIMS
    # Only include dims that are actually present in subgroup_defs.
    available_dims = [d for d in _SUBGROUP_DIMS if d in subgroup_defs.columns]
    def_narrow = subgroup_defs[["business_id"] + available_dims].copy()

    merged = reviews_narrow.merge(def_narrow, on="business_id", how="inner")

    chunks: list[pd.DataFrame] = []
    for dim in available_dims:
        grouped = merged.groupby(dim, dropna=False).agg(
            business_count=("business_id", "nunique"),
            review_count=("business_id", "count"),
            user_count=("user_id", "nunique"),
            mean_stars=(stars_col, "mean"),
            mean_useful=("useful", "mean"),
        ).reset_index()

        grouped = grouped.rename(columns={dim: "subgroup_value"})
        grouped.insert(0, "subgroup_type", dim)
        chunks.append(grouped)

    if not chunks:
        empty = pd.DataFrame(
            columns=[
                "subgroup_type",
                "subgroup_value",
                "business_count",
                "review_count",
                "user_count",
                "mean_stars",
                "mean_useful",
            ]
        )
        return empty

    result = pd.concat(chunks, ignore_index=True)

    # Enforce schema dtypes.
    result["subgroup_type"] = result["subgroup_type"].astype(str)
    result["subgroup_value"] = result["subgroup_value"].astype(str)
    result["business_count"] = result["business_count"].astype(int)
    result["review_count"] = result["review_count"].astype(int)
    result["user_count"] = result["user_count"].astype(int)

    result = enforce_min_group_size(result, "business_count", min_group_size)
    return result.reset_index(drop=True)


def log_coverage_fraction(
    coverage_df: pd.DataFrame,
    reviews_df: pd.DataFrame,
) -> None:
    """Log retained review coverage by subgroup dimension after filtering."""
    if coverage_df.empty or reviews_df.empty:
        logger.info("Coverage fraction skipped because one or more inputs are empty.")
        return

    total_reviews = len(reviews_df)
    if total_reviews <= 0:
        logger.info("Coverage fraction skipped because total review count is zero.")
        return

    for subgroup_type, chunk in coverage_df.groupby("subgroup_type", dropna=False):
        retained_reviews = int(chunk["review_count"].sum())
        fraction = retained_reviews / total_reviews
        logger.info(
            "Coverage retention for %s: %d/%d reviews (%.3f)",
            subgroup_type,
            retained_reviews,
            total_reviews,
            fraction,
        )


def plot_coverage_bar(
    coverage_df: pd.DataFrame,
    subgroup_type: str,
    metric: str,
    top_n: int,
    path: Path,
) -> None:
    """Plot a horizontal bar chart of *metric* for the given subgroup_type.

    Args:
        coverage_df: Long-format coverage DataFrame from build_coverage_by_subgroup.
        subgroup_type: Dimension to filter on (e.g. "city").
        metric: Column to plot on the x-axis (e.g. "review_count").
        top_n: Maximum number of bars to show (sorted by review_count descending).
        path: Output file path (.png).
    """
    subset = coverage_df[coverage_df["subgroup_type"] == subgroup_type].copy()

    if subset.empty or metric not in subset.columns:
        save_placeholder_figure(
            path,
            title=f"Coverage by {subgroup_type}",
            message=f"No data for subgroup_type='{subgroup_type}'",
        )
        return

    subset = subset.sort_values("review_count", ascending=False).head(top_n)

    fig, ax = plt.subplots(figsize=(10, max(4, len(subset) * 0.4)))
    ax.barh(
        subset["subgroup_value"].tolist(),
        subset[metric].tolist(),
        color="steelblue",
    )
    ax.invert_yaxis()
    ax.set_xlabel(metric.replace("_", " ").title())
    ax.set_ylabel(subgroup_type.replace("_", " ").title())
    ax.set_title(f"Coverage by {subgroup_type.replace('_', ' ').title()} (top {top_n})")

    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=100, bbox_inches="tight")
    plt.close(fig)
    logger.info("Wrote figure %s", path)


def run(config: dict[str, Any]) -> None:
    """Execute Stage 2: compute and persist coverage profiles.

    Args:
        config: Loaded YAML config dict (from load_config).

    Raises:
        FileNotFoundError: If the Stage 1 subgroup definitions file is absent.
    """
    paths = resolve_paths(config)
    ensure_output_dirs(paths)

    min_group_size = _resolve_min_group_size(config)

    # -- Load Stage 1 subgroup definitions ------------------------------------
    s1_path = paths.tables_dir / "track_e_s1_subgroup_definitions.parquet"
    if not s1_path.exists():
        logger.error(
            "Stage 1 output not found at %s — run Stage 1 first.", s1_path
        )
        raise FileNotFoundError(
            f"Stage 1 subgroup definitions not found: {s1_path}"
        )
    subgroup_defs = load_parquet(s1_path)
    logger.info("Loaded subgroup definitions: %d rows", len(subgroup_defs))

    # -- Load review fact (select needed columns only) ------------------------
    review_fact_path = paths.review_fact_path
    # Try to detect available star column name via DuckDB schema inspection.
    pq_str = str(review_fact_path).replace("\\", "/")
    con = connect_duckdb(config)
    try:
        col_query = con.execute(
            f"SELECT column_name FROM parquet_schema('{pq_str}') WHERE column_name IN ('stars', 'review_stars')"
        ).fetchdf()
    finally:
        con.close()

    if col_query.empty:
        stars_col_sql = "stars"
    else:
        stars_col_sql = col_query["column_name"].iloc[0]

    pq_str = str(review_fact_path).replace("\\", "/")
    reviews_df = load_parquet(
        review_fact_path,
        sql=(
            f"SELECT business_id, user_id, {stars_col_sql}, useful "
            f"FROM read_parquet('{pq_str}') "
        ),
    )
    logger.info("Loaded %d review rows", len(reviews_df))

    # -- Build coverage table -------------------------------------------------
    coverage_df = build_coverage_by_subgroup(
        reviews_df, subgroup_defs, min_group_size=min_group_size
    )
    logger.info("Coverage table: %d subgroup rows", len(coverage_df))
    log_coverage_fraction(coverage_df, reviews_df)

    out_parquet = paths.tables_dir / "track_e_s2_coverage_by_subgroup.parquet"
    write_parquet(coverage_df, out_parquet)

    # -- Generate figures -----------------------------------------------------
    figure_specs = [
        ("city", paths.figures_dir / "track_e_s2_coverage_by_city.png"),
        ("primary_category", paths.figures_dir / "track_e_s2_coverage_by_category.png"),
        ("price_tier", paths.figures_dir / "track_e_s2_coverage_by_price.png"),
    ]
    for dim, fig_path in figure_specs:
        plot_coverage_bar(
            coverage_df,
            subgroup_type=dim,
            metric="review_count",
            top_n=20,
            path=fig_path,
        )

    logger.info("Stage 2 complete.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )
    parser = argparse.ArgumentParser(
        description="Track E Stage 2: coverage profile by subgroup"
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to track_e YAML config file",
    )
    args = parser.parse_args()

    cfg = load_config(args.config)
    run(cfg)
