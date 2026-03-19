"""Stage 1: Geographic coverage profiling for Track C."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import duckdb
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from src.common.config import load_config
from src.common.db import connect_duckdb
from src.eda.track_c.common import (
    ensure_output_dirs,
    resolve_paths,
    save_placeholder_figure,
    write_parquet,
)

matplotlib.use("Agg")

logger = logging.getLogger(__name__)


def build_city_coverage(
    con: duckdb.DuckDBPyConnection,
    review_fact_path: str,
    business_path: str,
    min_city_reviews: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Build Track C city/state coverage tables."""
    pq_review = str(review_fact_path).replace("\\", "/")
    pq_business = str(business_path).replace("\\", "/")
    city_df = con.execute(
        f"""
        WITH review_city AS (
            SELECT
                city,
                LOWER(TRIM(city)) AS normalized_city,
                state,
                COUNT(*) AS review_count,
                COUNT(DISTINCT business_id) AS reviewed_business_count,
                MIN(review_date)::VARCHAR AS first_review_date,
                MAX(review_date)::VARCHAR AS last_review_date,
                AVG(latitude) AS latitude,
                AVG(longitude) AS longitude
            FROM read_parquet('{pq_review}')
            GROUP BY city, normalized_city, state
        ),
        business_city AS (
            SELECT
                LOWER(TRIM(city)) AS normalized_city,
                state,
                COUNT(DISTINCT business_id) AS business_count
            FROM read_parquet('{pq_business}')
            GROUP BY normalized_city, state
        )
        SELECT
            rc.city,
            rc.normalized_city,
            rc.state,
            rc.review_count,
            COALESCE(bc.business_count, rc.reviewed_business_count) AS business_count,
            rc.review_count >= ? AS is_analyzable,
            rc.first_review_date,
            rc.last_review_date,
            rc.latitude,
            rc.longitude
        FROM review_city rc
        LEFT JOIN business_city bc
          ON rc.normalized_city = bc.normalized_city
         AND rc.state = bc.state
        ORDER BY rc.review_count DESC, rc.city
        """,
        [min_city_reviews],
    ).fetchdf()

    if city_df.empty:
        state_df = pd.DataFrame(
            columns=["state", "city_count", "review_count", "analyzable_city_count"]
        )
    else:
        state_df = (
            city_df.groupby("state", dropna=False, as_index=False)
            .agg(
                city_count=("city", "count"),
                review_count=("review_count", "sum"),
                analyzable_city_count=("is_analyzable", "sum"),
            )
            .sort_values(["review_count", "state"], ascending=[False, True])
        )

    variant_df = con.execute(
        f"""
        WITH raw_city AS (
            SELECT
                LOWER(TRIM(city)) AS normalized_city,
                state,
                city,
                COUNT(*) AS review_count
            FROM read_parquet('{pq_review}')
            GROUP BY normalized_city, state, city
        )
        SELECT
            normalized_city,
            state,
            COUNT(*) AS raw_variant_count,
            STRING_AGG(city, ', ' ORDER BY review_count DESC, city) AS raw_city_variants,
            SUM(review_count) AS combined_review_count
        FROM raw_city
        GROUP BY normalized_city, state
        HAVING COUNT(*) > 1
        ORDER BY combined_review_count DESC, normalized_city
        """
    ).fetchdf()

    return city_df, state_df, variant_df


def plot_city_bar(city_df: pd.DataFrame, top_n: int, output_path: str) -> None:
    """Plot top cities by review count."""
    if city_df.empty:
        save_placeholder_figure(Path(output_path), "Track C: City Review Counts")
        return
    top_df = city_df.head(top_n)
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(top_df["city"], top_df["review_count"], color="#3b82f6")
    ax.set_title("Track C: Top Cities by Review Count")
    ax.set_ylabel("Review Count")
    ax.set_xticks(range(len(top_df)))
    ax.set_xticklabels(top_df["city"], rotation=45, ha="right")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    logger.info("Wrote %s", output_path)


def plot_coverage_map(city_df: pd.DataFrame, output_path: str) -> None:
    """Plot city-level coordinates sized by review count."""
    if city_df.empty or city_df["latitude"].isna().all() or city_df["longitude"].isna().all():
        save_placeholder_figure(Path(output_path), "Track C: Coverage Map")
        return
    fig, ax = plt.subplots(figsize=(10, 6))
    sizes = city_df["review_count"].clip(lower=1).pow(0.5) * 2
    colors = city_df["is_analyzable"].map({True: "#16a34a", False: "#94a3b8"})
    ax.scatter(city_df["longitude"], city_df["latitude"], s=sizes, c=colors, alpha=0.6)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Track C: City Coverage Map")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    logger.info("Wrote %s", output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 1: Geographic Coverage")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(args.config)

    paths = resolve_paths(config)
    ensure_output_dirs(paths)

    min_city_reviews = int(config.get("geography", {}).get("min_city_reviews", 1000))
    top_n = int(config.get("geography", {}).get("top_n_cities", 20))

    con = connect_duckdb(config)
    try:
        city_df, state_df, variant_df = build_city_coverage(
            con,
            str(paths.review_fact_path),
            str(paths.business_path),
            min_city_reviews,
        )
    finally:
        con.close()

    write_parquet(city_df, paths.tables_dir / "track_c_s1_city_coverage.parquet")
    write_parquet(state_df, paths.tables_dir / "track_c_s1_state_coverage.parquet")
    write_parquet(variant_df, paths.tables_dir / "track_c_s1_city_variant_diagnostic.parquet")

    plot_city_bar(
        city_df,
        top_n,
        str(paths.figures_dir / "track_c_s1_city_review_count_bar.png"),
    )
    plot_coverage_map(
        city_df,
        str(paths.figures_dir / "track_c_s1_coverage_map.png"),
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    main()
