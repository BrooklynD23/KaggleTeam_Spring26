"""Stage 3: Ranking-group analysis for Track B."""

import argparse
import logging

import duckdb
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from src.common.config import load_config
from src.common.db import connect_duckdb
from src.eda.track_b.common import (
    TrackBPaths,
    create_snapshot_view,
    ensure_output_dirs,
    resolve_paths,
)

matplotlib.use("Agg")

logger = logging.getLogger(__name__)


def _run_group_summary(
    con: duckdb.DuckDBPyConnection,
    group_type: str,
    group_expr: str,
    min_group_size: int,
    min_distinct_useful: int,
) -> pd.DataFrame:
    """Build a ranking-group summary for one grouping strategy."""
    sql = f"""
        WITH base AS (
            SELECT
                {group_expr} AS group_id,
                age_bucket,
                useful
            FROM review_usefulness_snapshot
            WHERE {group_expr} IS NOT NULL AND TRIM(CAST({group_expr} AS VARCHAR)) <> ''
        ),
        grouped AS (
            SELECT
                group_id,
                age_bucket,
                COUNT(*) AS review_count,
                COUNT(DISTINCT useful) AS distinct_useful_count,
                AVG(CASE WHEN useful = 0 THEN 1.0 ELSE 0.0 END) AS pct_zero_useful,
                AVG(useful) AS mean_useful,
                MAX(useful) AS max_useful
            FROM base
            GROUP BY group_id, age_bucket
        ),
        tie_counts AS (
            SELECT
                group_id,
                age_bucket,
                SUM(value_count * (value_count - 1) / 2) AS tied_pairs
            FROM (
                SELECT
                    group_id,
                    age_bucket,
                    useful,
                    COUNT(*) AS value_count
                FROM base
                GROUP BY group_id, age_bucket, useful
            )
            GROUP BY group_id, age_bucket
        )
        SELECT
            '{group_type}' AS group_type,
            group_id,
            age_bucket,
            review_count,
            distinct_useful_count,
            ROUND(pct_zero_useful, 4) AS pct_zero_useful,
            ROUND(mean_useful, 4) AS mean_useful,
            max_useful,
            COALESCE(tied_pairs, 0) AS tied_pairs,
            CASE
                WHEN review_count < 2 THEN 1.0
                ELSE ROUND(
                    COALESCE(tied_pairs, 0)::DOUBLE
                    / NULLIF(review_count * (review_count - 1) / 2, 0),
                    4
                )
            END AS tie_rate,
            review_count >= {min_group_size}
                AND distinct_useful_count >= {min_distinct_useful}
                AS qualifies
        FROM grouped
        LEFT JOIN tie_counts USING (group_id, age_bucket)
        ORDER BY review_count DESC, group_id, age_bucket
    """
    return con.execute(sql).fetchdf()


def plot_group_size_distribution(
    business_df: pd.DataFrame,
    category_df: pd.DataFrame,
    paths: TrackBPaths,
) -> None:
    """Plot group-size distributions for business and category fallback groups."""
    fig, ax = plt.subplots(figsize=(10, 6))
    bins = 30
    ax.hist(
        business_df["review_count"],
        bins=bins,
        alpha=0.55,
        label="business x age",
    )
    ax.hist(
        category_df["review_count"],
        bins=bins,
        alpha=0.55,
        label="category x age",
    )
    ax.set_xlabel("Group Size")
    ax.set_ylabel("Number of Groups")
    ax.set_title("Track B: Ranking Group Size Distribution")
    ax.set_yscale("log")
    ax.legend()
    fig.tight_layout()
    out = paths.figures_dir / "track_b_s3_group_size_distribution.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    logger.info("Wrote %s", out)


def _build_recommended_buckets(
    business_df: pd.DataFrame,
    category_df: pd.DataFrame,
    min_qualifying_groups: int,
) -> pd.DataFrame:
    """Determine which age buckets meet the qualifying-group gate.

    An age bucket is recommended when the combined count of qualifying groups
    (business + category) across that bucket meets or exceeds
    ``min_qualifying_groups``.

    Returns a DataFrame with columns:
        age_bucket, business_qualifying_groups, category_qualifying_groups,
        total_qualifying_groups, recommended_for_modeling
    """
    business_qualifying = (
        business_df[business_df["qualifies"]]
        .groupby("age_bucket")
        .size()
        .reset_index(name="business_qualifying_groups")
    )
    category_qualifying = (
        category_df[category_df["qualifies"]]
        .groupby("age_bucket")
        .size()
        .reset_index(name="category_qualifying_groups")
    )

    all_buckets = sorted(
        set(business_df["age_bucket"].unique()) | set(category_df["age_bucket"].unique())
    )
    bucket_df = pd.DataFrame({"age_bucket": all_buckets})
    bucket_df = bucket_df.merge(business_qualifying, on="age_bucket", how="left")
    bucket_df = bucket_df.merge(category_qualifying, on="age_bucket", how="left")
    bucket_df["business_qualifying_groups"] = (
        bucket_df["business_qualifying_groups"].fillna(0).astype(int)
    )
    bucket_df["category_qualifying_groups"] = (
        bucket_df["category_qualifying_groups"].fillna(0).astype(int)
    )
    bucket_df["total_qualifying_groups"] = (
        bucket_df["business_qualifying_groups"] + bucket_df["category_qualifying_groups"]
    )
    bucket_df["recommended_for_modeling"] = (
        bucket_df["total_qualifying_groups"] >= min_qualifying_groups
    )
    return bucket_df


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 3: Ranking Group Analysis")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(args.config)

    paths = resolve_paths(config)
    ensure_output_dirs(paths)

    business_cfg = config["ranking_groups"]["business"]
    fallback_cfg = config["ranking_groups"]["category_city"]

    con = connect_duckdb(config)
    try:
        create_snapshot_view(con, config, paths)
        business_df = _run_group_summary(
            con,
            group_type="business",
            group_expr="business_id",
            min_group_size=business_cfg["min_group_size"],
            min_distinct_useful=business_cfg["min_distinct_useful"],
        )
        category_df = _run_group_summary(
            con,
            group_type="category",
            group_expr="primary_category",
            min_group_size=fallback_cfg["min_group_size"],
            min_distinct_useful=fallback_cfg["min_distinct_useful"],
        )
    finally:
        con.close()

    business_out = paths.tables_dir / "track_b_s3_group_sizes_by_business_age.parquet"
    business_df.to_parquet(business_out, index=False)
    logger.info("Wrote %s (%d rows)", business_out, len(business_df))

    category_out = paths.tables_dir / "track_b_s3_group_sizes_by_category_age.parquet"
    category_df.to_parquet(category_out, index=False)
    logger.info("Wrote %s (%d rows)", category_out, len(category_df))

    # Write the authoritative recommended-bucket list filtered by qualifying-group gate
    min_qualifying_groups = int(
        config.get("quality", {}).get("min_qualifying_groups", 1000)
    )
    recommended_df = _build_recommended_buckets(
        business_df, category_df, min_qualifying_groups
    )
    recommended_out = paths.tables_dir / "track_b_s3_recommended_age_buckets.parquet"
    recommended_df.to_parquet(recommended_out, index=False)
    logger.info("Wrote %s (%d rows)", recommended_out, len(recommended_df))

    n_recommended = int(recommended_df["recommended_for_modeling"].sum())
    if n_recommended == 0:
        logger.warning(
            "Stage 3: no age bucket meets the min_qualifying_groups=%d gate. "
            "Downstream stages will raise a pipeline error.",
            min_qualifying_groups,
        )
    else:
        logger.info("Stage 3: %d age bucket(s) recommended for modeling.", n_recommended)

    plot_group_size_distribution(business_df, category_df, paths)
    logger.info("Stage 3 complete.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    main()
