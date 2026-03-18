"""Stage 1: Usefulness distribution and quality checks for Track B."""

import argparse
import logging
from dataclasses import dataclass
from typing import Any

import duckdb
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from src.common.config import load_config
from src.eda.track_b.common import (
    TrackBPaths,
    create_snapshot_view,
    ensure_output_dirs,
    resolve_paths,
)

matplotlib.use("Agg")

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StageOneOutputs:
    """All Stage 1 aggregate outputs."""

    vote_distribution: pd.DataFrame
    bucket_summary: pd.DataFrame
    category_zero_fraction: pd.DataFrame
    age_distribution: pd.DataFrame


def _validate_quality(
    con: duckdb.DuckDBPyConnection,
    config: dict[str, Any],
) -> None:
    """Run Track B Stage 1 quality checks."""
    row = con.execute(
        """
        SELECT
            COUNT(*) AS row_count,
            AVG(CASE WHEN useful IS NOT NULL THEN 1.0 ELSE 0.0 END) AS useful_nonnull_rate,
            SUM(CASE WHEN useful < 0 THEN 1 ELSE 0 END) AS negative_useful_rows,
            SUM(CASE WHEN review_age_days < 0 THEN 1 ELSE 0 END) AS negative_age_rows
        FROM review_usefulness_snapshot
        """
    ).fetchone()
    if row is None:
        raise RuntimeError("Stage 1 quality query returned no rows")

    useful_nonnull_threshold = config.get("quality", {}).get(
        "useful_nonnull_threshold", 0.999
    )
    useful_nonnull_rate = float(row[1])
    negative_useful_rows = int(row[2])
    negative_age_rows = int(row[3])

    if useful_nonnull_rate < useful_nonnull_threshold:
        raise RuntimeError(
            "Track B useful non-null rate is below threshold: "
            f"{useful_nonnull_rate:.4f} < {useful_nonnull_threshold:.4f}"
        )
    if negative_useful_rows > 0:
        raise RuntimeError(
            f"Track B found {negative_useful_rows} negative useful counts"
        )
    if negative_age_rows > 0:
        raise RuntimeError(
            f"Track B found {negative_age_rows} reviews with negative age"
        )


def run_vote_distribution(
    con: duckdb.DuckDBPyConnection,
) -> pd.DataFrame:
    """Overall useful vote distribution (useful, count)."""
    sql = """
        SELECT useful, COUNT(*) AS review_count
        FROM review_usefulness_snapshot
        GROUP BY useful
        ORDER BY useful;
    """
    return con.execute(sql).fetchdf()


def run_bucket_summary(
    con: duckdb.DuckDBPyConnection,
) -> pd.DataFrame:
    """Bucket summary: 0, 1, 2-4, 5-9, 10-24, 25-99, 100+."""
    sql = """
        WITH bucketed AS (
            SELECT
                CASE
                    WHEN useful = 0 THEN '0'
                    WHEN useful = 1 THEN '1'
                    WHEN useful BETWEEN 2 AND 4 THEN '2-4'
                    WHEN useful BETWEEN 5 AND 9 THEN '5-9'
                    WHEN useful BETWEEN 10 AND 24 THEN '10-24'
                    WHEN useful BETWEEN 25 AND 99 THEN '25-99'
                    ELSE '100+'
                END AS useful_bucket,
                useful
            FROM review_usefulness_snapshot
        )
        SELECT
            useful_bucket,
            COUNT(*) AS review_count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct
        FROM bucketed
        GROUP BY useful_bucket
        ORDER BY
            CASE useful_bucket
                WHEN '0' THEN 0
                WHEN '1' THEN 1
                WHEN '2-4' THEN 2
                WHEN '5-9' THEN 3
                WHEN '10-24' THEN 4
                WHEN '25-99' THEN 5
                ELSE 6
            END;
    """
    return con.execute(sql).fetchdf()


def run_category_zero_fraction(
    con: duckdb.DuckDBPyConnection,
) -> pd.DataFrame:
    """Category-level zero fraction for categories with >= 1000 reviews."""
    sql = """
        SELECT
            TRIM(SPLIT_PART(categories, ',', 1)) AS primary_category,
            COUNT(*) AS review_count,
            ROUND(AVG(CASE WHEN useful = 0 THEN 1.0 ELSE 0.0 END), 4) AS zero_fraction,
            ROUND(AVG(useful), 4) AS mean_useful
        FROM review_usefulness_snapshot
        WHERE primary_category IS NOT NULL AND primary_category <> ''
        GROUP BY primary_category
        HAVING COUNT(*) >= 1000
        ORDER BY zero_fraction DESC;
    """
    return con.execute(sql).fetchdf()


def run_age_distribution(
    con: duckdb.DuckDBPyConnection,
) -> pd.DataFrame:
    """Review age distribution using DATEDIFF from review_date to snapshot."""
    sql = """
        SELECT
            review_age_days,
            COUNT(*) AS review_count
        FROM review_usefulness_snapshot
        GROUP BY review_age_days
        ORDER BY review_age_days;
    """
    return con.execute(sql).fetchdf()


def plot_useful_histogram(df: pd.DataFrame, paths: TrackBPaths) -> None:
    """Log-scale histogram of useful vote counts."""
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(df["useful"], df["review_count"], width=0.8, alpha=0.7)
    ax.set_yscale("log")
    ax.set_xlabel("Useful Vote Count")
    ax.set_ylabel("Number of Reviews (log scale)")
    ax.set_title("Track B: Useful Vote Distribution (log scale)")
    if len(df) > 30:
        ticks = list(range(0, len(df), max(1, len(df) // 20)))
        tick_values = df["useful"].iloc[ticks]
        ax.set_xticks(tick_values)
        ax.set_xticklabels([str(value) for value in tick_values], rotation=45)
    fig.tight_layout()
    out = paths.figures_dir / "track_b_s1_useful_histogram.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    logger.info("Wrote %s", out)


def plot_zero_fraction_by_category(df: pd.DataFrame, paths: TrackBPaths) -> None:
    """Horizontal bar chart of zero fraction by primary category."""
    top = df.head(30)
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.barh(top["primary_category"], top["zero_fraction"], color="steelblue", alpha=0.8)
    ax.set_xlabel("Fraction of Reviews with 0 Useful Votes")
    ax.set_ylabel("Primary Category")
    ax.set_title("Track B: Zero-Fraction by Category (Top 30)")
    ax.invert_yaxis()
    fig.tight_layout()
    out = paths.figures_dir / "track_b_s1_zero_fraction_by_category.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    logger.info("Wrote %s", out)


def run_stage(con: duckdb.DuckDBPyConnection, config: dict[str, Any], paths: TrackBPaths) -> StageOneOutputs:
    """Execute Stage 1 on the curated Track B parquet input."""
    create_snapshot_view(con, config, paths)
    _validate_quality(con, config)
    return StageOneOutputs(
        vote_distribution=run_vote_distribution(con),
        bucket_summary=run_bucket_summary(con),
        category_zero_fraction=run_category_zero_fraction(con),
        age_distribution=run_age_distribution(con),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 1: Usefulness Distribution")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(args.config)

    paths = resolve_paths(config)
    ensure_output_dirs(paths)

    con = duckdb.connect()
    try:
        outputs = run_stage(con, config, paths)
    finally:
        con.close()

    vote_out = paths.tables_dir / "track_b_s1_useful_vote_distribution.parquet"
    outputs.vote_distribution.to_parquet(vote_out, index=False)
    logger.info("Wrote %s (%d rows)", vote_out, len(outputs.vote_distribution))

    bucket_out = paths.tables_dir / "track_b_s1_bucket_summary.parquet"
    outputs.bucket_summary.to_parquet(bucket_out, index=False)
    logger.info("Wrote %s (%d rows)", bucket_out, len(outputs.bucket_summary))

    cat_out = paths.tables_dir / "track_b_s1_category_zero_fraction.parquet"
    outputs.category_zero_fraction.to_parquet(cat_out, index=False)
    logger.info(
        "Wrote %s (%d rows)",
        cat_out,
        len(outputs.category_zero_fraction),
    )

    age_out = paths.tables_dir / "track_b_s1_age_distribution.parquet"
    outputs.age_distribution.to_parquet(age_out, index=False)
    logger.info("Wrote %s (%d rows)", age_out, len(outputs.age_distribution))

    plot_useful_histogram(outputs.vote_distribution, paths)
    plot_zero_fraction_by_category(outputs.category_zero_fraction, paths)

    logger.info("Stage 1 complete.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    main()
