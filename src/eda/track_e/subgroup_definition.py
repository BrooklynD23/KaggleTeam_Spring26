"""Stage 1 — Subgroup Definition for Track E Bias and Disparity Audit."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from src.common.config import load_config
from src.common.helpers import extract_price_range, primary_category
from src.eda.track_e.common import (
    assign_price_tier,
    assign_review_volume_tier,
    enforce_min_group_size,
    ensure_output_dirs,
    load_parquet,
    resolve_paths,
    save_placeholder_figure,  # noqa: F401 — imported for re-export convenience
    write_parquet,
)

logger = logging.getLogger(__name__)

_SUBGROUP_DIMENSIONS = ("city", "primary_category", "price_tier", "review_volume_tier")


# ---------------------------------------------------------------------------
# Core logic — importable by tests
# ---------------------------------------------------------------------------


def _build_single_row(
    row: Any,
    review_counts: pd.Series,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Derive subgroup fields for a single business row."""
    biz_id: str = row.business_id

    cat = primary_category(row.categories)
    if cat is None:
        cat = "unknown"

    price_range = extract_price_range(row.attributes)
    price_tier = assign_price_tier(price_range, config)

    review_count = int(review_counts.get(biz_id, 0))
    boundaries: list[int] = config["subgroups"]["review_volume_tier_boundaries"]
    volume_tier = assign_review_volume_tier(review_count, boundaries)

    return {
        "business_id": biz_id,
        "city": row.city if hasattr(row, "city") else None,
        "state": row.state if hasattr(row, "state") else None,
        "primary_category": cat,
        "price_tier": price_tier,
        "review_volume_tier": volume_tier,
    }


def build_subgroup_definitions(
    business_df: pd.DataFrame,
    review_counts: pd.Series,
    config: dict[str, Any],
) -> pd.DataFrame:
    """Assign subgroup labels to every business.

    Args:
        business_df: Loaded business.parquet columns including business_id,
            city, state, categories, attributes.
        review_counts: Series indexed by business_id with per-business
            review counts derived from review_fact.parquet.
        config: Merged track_e config dict.

    Returns:
        DataFrame with columns: business_id, city, state, primary_category,
        price_tier, review_volume_tier.
    """
    if business_df.empty:
        logger.warning("build_subgroup_definitions received an empty business_df.")
        return pd.DataFrame(
            columns=[
                "business_id", "city", "state",
                "primary_category", "price_tier", "review_volume_tier",
            ]
        )

    rows = [_build_single_row(row, review_counts, config) for row in business_df.itertuples()]
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Summary helpers
# ---------------------------------------------------------------------------


def _build_subgroup_summary(subgroup_defs: pd.DataFrame) -> pd.DataFrame:
    """Build a long-format summary: subgroup_type, subgroup_value, business_count."""
    frames: list[pd.DataFrame] = []
    for dim in _SUBGROUP_DIMENSIONS:
        if dim not in subgroup_defs.columns:
            continue
        counts = (
            subgroup_defs.groupby(dim, dropna=False)["business_id"]
            .count()
            .reset_index()
        )
        counts.columns = ["subgroup_value", "business_count"]
        counts.insert(0, "subgroup_type", dim)
        frames.append(counts)

    if not frames:
        return pd.DataFrame(columns=["subgroup_type", "subgroup_value", "business_count"])

    summary = pd.concat(frames, ignore_index=True)
    summary["subgroup_value"] = summary["subgroup_value"].astype(str)
    summary["business_count"] = summary["business_count"].astype(int)
    return summary


def _build_price_tier_diagnostic(
    subgroup_defs: pd.DataFrame,
    config: dict[str, Any],
) -> pd.DataFrame:
    """Compute price-tier data-quality metrics."""
    missing_label: str = config["subgroups"]["price_tier_missing_label"]
    min_coverage: float = config["quality"]["min_price_tier_coverage"]

    total: int = len(subgroup_defs)
    with_tier: int = int((subgroup_defs["price_tier"] != missing_label).sum())
    null_rate: float = 1.0 - (with_tier / total) if total > 0 else 1.0
    meets_min: bool = null_rate <= (1.0 - min_coverage)

    if not meets_min:
        logger.warning(
            "price_tier null_rate=%.3f exceeds threshold (1 - min_price_tier_coverage=%.3f). "
            "Only %d/%d businesses have a price tier.",
            null_rate,
            min_coverage,
            with_tier,
            total,
        )

    return pd.DataFrame(
        [
            {
                "total_businesses": total,
                "businesses_with_price_tier": with_tier,
                "null_rate": null_rate,
                "meets_min_coverage": meets_min,
            }
        ]
    )


# ---------------------------------------------------------------------------
# Dimension quality check
# ---------------------------------------------------------------------------


def _check_dimension_population(subgroup_defs: pd.DataFrame) -> int:
    """Return count of dimensions with at least one non-null, non-unknown value."""
    populated = 0
    for dim in _SUBGROUP_DIMENSIONS:
        if dim not in subgroup_defs.columns:
            continue
        col = subgroup_defs[dim].dropna()
        if dim == "primary_category":
            non_trivial = col[col != "unknown"]
        elif dim == "price_tier":
            non_trivial = col  # "missing" is a valid tier label; dimension still exists
        else:
            non_trivial = col
        if not non_trivial.empty:
            populated += 1
    return populated


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def run(config: dict[str, Any]) -> None:
    """Execute Stage 1: subgroup definition.

    Produces three parquet artifacts in outputs/tables/:
      - track_e_s1_subgroup_definitions.parquet
      - track_e_s1_subgroup_summary.parquet
      - track_e_s1_price_tier_diagnostic.parquet
    """
    paths = resolve_paths(config)
    ensure_output_dirs(paths)

    min_group_size = int(config.get("subgroups", {}).get("min_group_size", 10))

    # 1. Load business data
    logger.info("Loading business data from %s", paths.business_path)
    if paths.business_path.is_file():
        business_df = load_parquet(
            paths.business_path,
            "SELECT business_id, city, state, categories, attributes FROM read_parquet(?)",
            [str(paths.business_path)],
        )
    else:
        logger.warning("business.parquet not found at %s — using empty frame.", paths.business_path)
        business_df = pd.DataFrame(
            columns=["business_id", "city", "state", "categories", "attributes"]
        )

    # 2. Load per-business review counts from review_fact
    logger.info("Loading review counts from %s", paths.review_fact_path)
    if paths.review_fact_path.is_file():
        sql = (
            "SELECT business_id, COUNT(*) AS review_count "
            "FROM read_parquet(?) GROUP BY business_id"
        )
        rc_df = load_parquet(
            paths.review_fact_path,
            sql=sql,
            params=[str(paths.review_fact_path)],
        )
        review_counts: pd.Series = rc_df.set_index("business_id")["review_count"]
    else:
        logger.warning(
            "review_fact.parquet not found at %s — defaulting all review counts to 0.",
            paths.review_fact_path,
        )
        review_counts = pd.Series(dtype=int)

    # 3. Build subgroup definitions
    subgroup_defs = build_subgroup_definitions(business_df, review_counts, config)

    # 4. Write subgroup definitions
    defs_path = paths.tables_dir / "track_e_s1_subgroup_definitions.parquet"
    write_parquet(subgroup_defs, defs_path)

    # 5. Build subgroup summary (long format)
    subgroup_summary = _build_subgroup_summary(subgroup_defs)
    subgroup_summary = enforce_min_group_size(subgroup_summary, "business_count", min_group_size)

    summary_path = paths.tables_dir / "track_e_s1_subgroup_summary.parquet"
    write_parquet(subgroup_summary, summary_path)

    # 6. Build price tier diagnostic
    price_diag = _build_price_tier_diagnostic(subgroup_defs, config)
    diag_path = paths.tables_dir / "track_e_s1_price_tier_diagnostic.parquet"
    write_parquet(price_diag, diag_path)

    # 7. Quality: dimension population count
    min_dims: int = config.get("quality", {}).get("min_subgroup_dimensions", 3)
    populated_dims = _check_dimension_population(subgroup_defs)
    if populated_dims >= min_dims:
        logger.info(
            "Dimension population check passed: %d/%d dimensions populated.",
            populated_dims,
            len(_SUBGROUP_DIMENSIONS),
        )
    else:
        logger.warning(
            "Only %d/%d subgroup dimensions are populated (min=%d).",
            populated_dims,
            len(_SUBGROUP_DIMENSIONS),
            min_dims,
        )

    logger.info("Stage 1 complete.")


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
    parser = argparse.ArgumentParser(description="Stage 1 — Track E Subgroup Definition")
    parser.add_argument("--config", required=True, help="Path to track_e.yaml config file")
    args = parser.parse_args()
    _config = load_config(args.config)
    run(_config)
