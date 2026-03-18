"""Stage 3 — Star Rating Disparity for Track E Bias and Disparity Audit."""

from __future__ import annotations

import logging
from itertools import combinations
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from src.common.config import load_config
from src.eda.track_e.common import (
    enforce_min_group_size,
    ensure_output_dirs,
    load_parquet,
    resolve_paths,
    save_placeholder_figure,
    write_parquet,
)

logger = logging.getLogger(__name__)

_DIMENSIONS = ("city", "primary_category", "price_tier", "review_volume_tier")


# ---------------------------------------------------------------------------
# Stars column resolution
# ---------------------------------------------------------------------------


def _get_stars_col(df: pd.DataFrame) -> str:
    """Return the name of the star-rating column, trying 'stars' then 'review_stars'."""
    if "stars" in df.columns:
        return "stars"
    if "review_stars" in df.columns:
        return "review_stars"
    raise KeyError(
        "DataFrame has neither 'stars' nor 'review_stars' column. "
        f"Available columns: {list(df.columns)}"
    )


# ---------------------------------------------------------------------------
# Star statistics
# ---------------------------------------------------------------------------


def compute_star_stats(
    reviews_with_defs: pd.DataFrame,
    dimension: str,
    min_group_size: int,
) -> pd.DataFrame:
    """Compute per-subgroup star rating statistics for a given dimension.

    Args:
        reviews_with_defs: Reviews joined with subgroup definitions. Must contain
            a stars column ('stars' or 'review_stars') and the dimension column.
        dimension: One of city, primary_category, price_tier, review_volume_tier.
        min_group_size: Minimum review count; smaller groups are excluded.

    Returns:
        DataFrame with columns: subgroup_type, subgroup_value, review_count,
        mean_stars, median_stars, std_stars, pct_5star, pct_1star.
    """
    if dimension not in reviews_with_defs.columns:
        logger.warning("Dimension '%s' not found in DataFrame — returning empty.", dimension)
        return pd.DataFrame(
            columns=[
                "subgroup_type", "subgroup_value", "review_count",
                "mean_stars", "median_stars", "std_stars", "pct_5star", "pct_1star",
            ]
        )

    stars_col = _get_stars_col(reviews_with_defs)
    grouped = reviews_with_defs.groupby(dimension, dropna=False)[stars_col]

    records: list[dict[str, Any]] = []
    for group_value, series in grouped:
        count = len(series)
        if count < min_group_size:
            continue
        records.append(
            {
                "subgroup_type": dimension,
                "subgroup_value": str(group_value),
                "review_count": count,
                "mean_stars": float(series.mean()),
                "median_stars": float(series.median()),
                "std_stars": float(series.std(ddof=1)) if count > 1 else 0.0,
                "pct_5star": float((series == 5).sum() / count),
                "pct_1star": float((series == 1).sum() / count),
            }
        )

    result = pd.DataFrame(records)
    if result.empty:
        return pd.DataFrame(
            columns=[
                "subgroup_type", "subgroup_value", "review_count",
                "mean_stars", "median_stars", "std_stars", "pct_5star", "pct_1star",
            ]
        )
    return result


# ---------------------------------------------------------------------------
# KS tests
# ---------------------------------------------------------------------------


def compute_ks_tests(
    reviews_with_defs: pd.DataFrame,
    dimension: str,
    min_group_size: int,
    significance: float,
    max_groups: int | None = None,
) -> list[dict[str, Any]]:
    """Compute pairwise two-sample KS tests across subgroups of a dimension.

    Args:
        reviews_with_defs: Reviews joined with subgroup definitions.
        dimension: Dimension column to compare subgroups within.
        min_group_size: Minimum review count per group to include in tests.
        significance: Alpha threshold for is_significant flag.

    Returns:
        List of dicts with keys: subgroup_type, group_a, group_b,
        ks_statistic, p_value, is_significant, _simpson_flag.
    """
    if dimension not in reviews_with_defs.columns:
        logger.warning("Dimension '%s' not in DataFrame — skipping KS tests.", dimension)
        return []

    stars_col = _get_stars_col(reviews_with_defs)
    eligible_groups: list[tuple[str, np.ndarray]] = []
    for group_value, series in reviews_with_defs.groupby(dimension, dropna=False)[stars_col]:
        arr = series.dropna().to_numpy()
        if len(arr) >= min_group_size:
            eligible_groups.append((str(group_value), arr))

    eligible_groups.sort(key=lambda item: len(item[1]), reverse=True)
    if max_groups is not None and max_groups > 0:
        eligible_groups = eligible_groups[:max_groups]

    groups = {group_name: values for group_name, values in eligible_groups}

    results: list[dict[str, Any]] = []
    for group_a, group_b in combinations(sorted(groups), 2):
        ks_stat, p_val = stats.ks_2samp(groups[group_a], groups[group_b])
        results.append(
            {
                "subgroup_type": dimension,
                "group_a": group_a,
                "group_b": group_b,
                "ks_statistic": float(ks_stat),
                "p_value": float(p_val),
                "is_significant": bool(p_val < significance),
                "_simpson_flag": False,
            }
        )

    return results


# ---------------------------------------------------------------------------
# Simpson's paradox check
# ---------------------------------------------------------------------------


def check_simpsons_paradox(
    reviews_with_defs: pd.DataFrame,
    primary_dimension: str,
    conditioning_variable: str,
    ks_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Flag KS pairs where the mean-stars direction reverses in any conditioning stratum.

    Args:
        reviews_with_defs: Reviews joined with subgroup definitions.
        primary_dimension: Dimension used for the KS pairs to inspect.
        conditioning_variable: Column to condition on for paradox detection.
        ks_results: List of KS result dicts (modified in place via copy, immutably).

    Returns:
        New list of KS result dicts with _simpson_flag updated where relevant.
    """
    if (
        primary_dimension not in reviews_with_defs.columns
        or conditioning_variable not in reviews_with_defs.columns
    ):
        logger.warning(
            "Simpson's check skipped — missing column(s): primary_dimension=%s, "
            "conditioning_variable=%s",
            primary_dimension,
            conditioning_variable,
        )
        return ks_results

    stars_col = _get_stars_col(reviews_with_defs)
    updated: list[dict[str, Any]] = []

    for entry in ks_results:
        if entry["subgroup_type"] != primary_dimension:
            updated.append(dict(entry))
            continue

        group_a: str = entry["group_a"]
        group_b: str = entry["group_b"]

        mask_a = reviews_with_defs[primary_dimension].astype(str) == group_a
        mask_b = reviews_with_defs[primary_dimension].astype(str) == group_b

        overall_mean_a = reviews_with_defs.loc[mask_a, stars_col].mean()
        overall_mean_b = reviews_with_defs.loc[mask_b, stars_col].mean()
        overall_direction = np.sign(overall_mean_a - overall_mean_b)

        simpson_flag = False
        for cond_val in reviews_with_defs[conditioning_variable].dropna().unique():
            cond_mask = reviews_with_defs[conditioning_variable] == cond_val
            mean_a_cond = reviews_with_defs.loc[mask_a & cond_mask, stars_col].mean()
            mean_b_cond = reviews_with_defs.loc[mask_b & cond_mask, stars_col].mean()

            if pd.isna(mean_a_cond) or pd.isna(mean_b_cond):
                continue

            stratum_direction = np.sign(mean_a_cond - mean_b_cond)
            if stratum_direction != 0 and stratum_direction != overall_direction:
                simpson_flag = True
                break

        new_entry = dict(entry)
        new_entry["_simpson_flag"] = simpson_flag
        updated.append(new_entry)

    return updated


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------


def plot_star_dist(
    reviews_with_defs: pd.DataFrame,
    dimension: str,
    top_n: int,
    path: Path,
) -> None:
    """Plot overlaid bar charts of star distribution (% per star 1-5) for top N subgroups.

    Args:
        reviews_with_defs: Reviews joined with subgroup definitions.
        dimension: Dimension column to slice by.
        top_n: Number of top subgroups (by review count) to include.
        path: Output PNG path.
    """
    if dimension not in reviews_with_defs.columns:
        save_placeholder_figure(path, f"Star Distribution by {dimension}", "Dimension not available")
        return

    stars_col = _get_stars_col(reviews_with_defs) if _has_stars(reviews_with_defs) else None
    if stars_col is None:
        save_placeholder_figure(path, f"Star Distribution by {dimension}", "No stars column")
        return

    counts = reviews_with_defs[dimension].value_counts()
    if counts.empty:
        save_placeholder_figure(path, f"Star Distribution by {dimension}", "No data")
        return

    top_groups = counts.head(top_n).index.tolist()
    subset = reviews_with_defs[reviews_with_defs[dimension].isin(top_groups)]

    if subset.empty:
        save_placeholder_figure(path, f"Star Distribution by {dimension}", "No data after filter")
        return

    star_values = [1, 2, 3, 4, 5]
    x = np.arange(len(star_values))
    bar_width = 0.8 / max(len(top_groups), 1)

    fig, ax = plt.subplots(figsize=(10, 5))
    for i, group in enumerate(top_groups):
        group_series = subset.loc[subset[dimension] == group, stars_col]
        total = len(group_series)
        pcts = [
            100.0 * (group_series == sv).sum() / total if total > 0 else 0.0
            for sv in star_values
        ]
        offset = (i - len(top_groups) / 2 + 0.5) * bar_width
        ax.bar(x + offset, pcts, width=bar_width, label=str(group), alpha=0.8)

    ax.set_xticks(x)
    ax.set_xticklabels([str(sv) for sv in star_values])
    ax.set_xlabel("Star Rating")
    ax.set_ylabel("% of Reviews")
    ax.set_title(f"Star Distribution by {dimension} (top {top_n})")
    ax.legend(loc="upper left", fontsize=7, ncol=2)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=100, bbox_inches="tight")
    plt.close(fig)
    logger.info("Wrote figure %s", path)


def _has_stars(df: pd.DataFrame) -> bool:
    return "stars" in df.columns or "review_stars" in df.columns


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def run(config: dict[str, Any]) -> None:
    """Execute Stage 3: star rating disparity.

    Produces:
      - outputs/tables/track_e_s3_star_disparity.parquet
      - outputs/tables/track_e_s3_ks_test_results.parquet
      - outputs/figures/track_e_s3_star_dist_by_category.png
      - outputs/figures/track_e_s3_star_dist_by_price.png
      - outputs/figures/track_e_s3_star_dist_by_city.png
    """
    paths = resolve_paths(config)
    ensure_output_dirs(paths)

    disparity_cfg: dict[str, Any] = config.get("disparity", {})
    ks_significance: float = float(disparity_cfg.get("ks_test_significance", 0.05))
    min_pairwise: int = int(disparity_cfg.get("min_pairwise_comparisons", 10))
    subgroups_cfg: dict[str, Any] = config.get("subgroups", {})
    min_group_size: int = int(subgroups_cfg.get("min_group_size", 10))
    max_groups: int = int(subgroups_cfg.get("top_n_cities", 20))

    simpson_cfg: dict[str, Any] = config.get("simpson", {})
    simpson_enabled: bool = bool(simpson_cfg.get("enabled", True))
    conditioning_variable: str = str(simpson_cfg.get("conditioning_variable", "primary_category"))

    quality_cfg: dict[str, Any] = config.get("quality", {})
    min_ks_comparisons: int = int(quality_cfg.get("min_ks_comparisons", min_pairwise))

    top_n_plot: int = int(config.get("plots", {}).get("top_n_subgroups", 6))

    # 1. Load review_fact and s1 subgroup definitions, join on business_id
    logger.info("Loading review_fact from %s", paths.review_fact_path)
    if paths.review_fact_path.is_file():
        reviews_df = load_parquet(paths.review_fact_path)
    else:
        logger.warning("review_fact.parquet not found — using empty frame.")
        reviews_df = pd.DataFrame(columns=["business_id", "stars", "user_id"])

    s1_path = paths.tables_dir / "track_e_s1_subgroup_definitions.parquet"
    logger.info("Loading subgroup definitions from %s", s1_path)
    if s1_path.is_file():
        subgroup_defs = load_parquet(s1_path)
    else:
        logger.warning("s1 subgroup definitions not found — using empty frame.")
        subgroup_defs = pd.DataFrame(columns=["business_id"])

    # 2. Join reviews with subgroup definitions
    reviews_with_defs = reviews_df.merge(subgroup_defs, on="business_id", how="inner")

    # 3. Resolve stars column name
    if "stars" in reviews_with_defs.columns:
        stars_col = "stars"
    elif "review_stars" in reviews_with_defs.columns:
        stars_col = "review_stars"
    else:
        logger.warning("No stars column found — stage will produce empty outputs.")
        stars_col = None

    # 4. Compute star stats for each dimension, concatenate, write
    stats_frames: list[pd.DataFrame] = []
    for dim in _DIMENSIONS:
        dim_stats = compute_star_stats(reviews_with_defs, dim, min_group_size)
        if not dim_stats.empty:
            stats_frames.append(dim_stats)

    if stats_frames:
        star_disparity_df = pd.concat(stats_frames, ignore_index=True)
    else:
        star_disparity_df = pd.DataFrame(
            columns=[
                "subgroup_type", "subgroup_value", "review_count",
                "mean_stars", "median_stars", "std_stars", "pct_5star", "pct_1star",
            ]
        )

    disparity_path = paths.tables_dir / "track_e_s3_star_disparity.parquet"
    write_parquet(star_disparity_df, disparity_path)

    # 5. Compute KS tests for each dimension, accumulate
    all_ks: list[dict[str, Any]] = []
    for dim in _DIMENSIONS:
        dim_ks = compute_ks_tests(
            reviews_with_defs,
            dim,
            min_group_size,
            ks_significance,
            max_groups=max_groups,
        )
        all_ks.extend(dim_ks)

    # 6. Simpson's paradox check for city dimension
    if simpson_enabled and all_ks:
        all_ks = check_simpsons_paradox(
            reviews_with_defs, "city", conditioning_variable, all_ks
        )

    # 7. Build KS DataFrame with _simpson_flag, write
    if all_ks:
        ks_df = pd.DataFrame(all_ks)
    else:
        ks_df = pd.DataFrame(
            columns=[
                "subgroup_type", "group_a", "group_b",
                "ks_statistic", "p_value", "is_significant", "_simpson_flag",
            ]
        )

    ks_path = paths.tables_dir / "track_e_s3_ks_test_results.parquet"
    write_parquet(ks_df, ks_path)

    # 8. Quality check: log warning if fewer comparisons than threshold
    total_comparisons = len(all_ks)
    if total_comparisons < min_ks_comparisons:
        logger.warning(
            "Only %d KS comparisons produced (min_ks_comparisons=%d). "
            "Check group sizes and data availability.",
            total_comparisons,
            min_ks_comparisons,
        )
    else:
        logger.info("KS comparison count: %d (>= min=%d)", total_comparisons, min_ks_comparisons)

    # 9. Plot 3 figures (category, price, city)
    plot_star_dist(
        reviews_with_defs,
        "primary_category",
        top_n_plot,
        paths.figures_dir / "track_e_s3_star_dist_by_category.png",
    )
    plot_star_dist(
        reviews_with_defs,
        "price_tier",
        top_n_plot,
        paths.figures_dir / "track_e_s3_star_dist_by_price.png",
    )
    plot_star_dist(
        reviews_with_defs,
        "city",
        top_n_plot,
        paths.figures_dir / "track_e_s3_star_dist_by_city.png",
    )

    logger.info("Stage 3 complete.")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    import logging as _logging

    _logging.basicConfig(
        level=_logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(description="Stage 3 — Track E Star Rating Disparity")
    parser.add_argument("--config", required=True, help="Path to track_e.yaml config file")
    args = parser.parse_args()
    _config = load_config(args.config)
    run(_config)
