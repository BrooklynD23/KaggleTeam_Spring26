"""Stage 2: Temporal binning for Track C."""

from __future__ import annotations

import argparse
import logging

import duckdb
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from src.common.config import load_config
from src.eda.track_c.common import (
    ensure_output_dirs,
    load_analyzable_cities,
    month_label,
    quarter_label,
    resolve_paths,
    save_placeholder_figure,
    write_parquet,
)

matplotlib.use("Agg")

logger = logging.getLogger(__name__)


def build_monthly_table(
    con: duckdb.DuckDBPyConnection,
    review_fact_path: str,
    min_reviews_per_bin: int,
) -> pd.DataFrame:
    """Aggregate monthly review volume by city."""
    df = con.execute(
        """
        SELECT
            city,
            LOWER(TRIM(city)) AS normalized_city,
            state,
            review_year,
            review_month,
            COUNT(*) AS review_count
        FROM read_parquet($1)
        GROUP BY city, normalized_city, state, review_year, review_month
        ORDER BY review_year, review_month, review_count DESC
        """,
        [review_fact_path],
    ).fetchdf()
    if df.empty:
        return pd.DataFrame(
            columns=[
                "city",
                "normalized_city",
                "state",
                "review_year",
                "review_month",
                "year_month",
                "review_count",
                "is_stable_bin",
            ]
        )
    df["year_month"] = [
        month_label(year, month)
        for year, month in zip(df["review_year"], df["review_month"], strict=True)
    ]
    df["is_stable_bin"] = df["review_count"] >= min_reviews_per_bin
    return df


def build_quarterly_table(monthly_df: pd.DataFrame, min_reviews_per_bin: int) -> pd.DataFrame:
    """Aggregate quarterly review volume by city."""
    if monthly_df.empty:
        return pd.DataFrame(
            columns=[
                "city",
                "normalized_city",
                "state",
                "year_quarter",
                "review_count",
                "is_stable_bin",
            ]
        )
    quarterly = monthly_df.copy()
    quarterly["year_quarter"] = [
        quarter_label(year, month)
        for year, month in zip(
            quarterly["review_year"], quarterly["review_month"], strict=True
        )
    ]
    quarterly = (
        quarterly.groupby(
            ["city", "normalized_city", "state", "year_quarter"],
            dropna=False,
            as_index=False,
        )["review_count"]
        .sum()
    )
    quarterly["is_stable_bin"] = quarterly["review_count"] >= min_reviews_per_bin
    return quarterly


def plot_volume_timeline(
    monthly_df: pd.DataFrame,
    analyzable_cities: set[str],
    output_path: str,
) -> None:
    """Plot overall review volume with top-city overlays."""
    from pathlib import Path

    if monthly_df.empty:
        save_placeholder_figure(Path(output_path), "Track C: Review Volume Timeline")
        return

    timeline = (
        monthly_df.groupby("year_month", as_index=False)["review_count"]
        .sum()
        .sort_values("year_month")
    )
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(timeline["year_month"], timeline["review_count"], label="all cities", linewidth=2)

    candidate_df = monthly_df.loc[
        monthly_df["normalized_city"].isin(analyzable_cities)
    ] if analyzable_cities else monthly_df
    top_cities = (
        candidate_df.groupby("city")["review_count"]
        .sum()
        .sort_values(ascending=False)
        .head(3)
        .index.tolist()
    )
    for city in top_cities:
        city_df = monthly_df.loc[monthly_df["city"] == city].sort_values("year_month")
        ax.plot(city_df["year_month"], city_df["review_count"], label=city, alpha=0.8)

    ax.set_title("Track C: Review Volume Over Time")
    ax.set_ylabel("Review Count")
    ax.tick_params(axis="x", rotation=45)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    logger.info("Wrote %s", output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 2: Temporal Binning")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(args.config)

    paths = resolve_paths(config)
    ensure_output_dirs(paths)
    min_reviews_per_bin = int(config.get("temporal", {}).get("min_reviews_per_bin", 30))

    con = duckdb.connect()
    try:
        monthly_df = build_monthly_table(
            con,
            str(paths.review_fact_path),
            min_reviews_per_bin,
        )
    finally:
        con.close()

    quarterly_df = build_quarterly_table(monthly_df, min_reviews_per_bin)

    write_parquet(monthly_df, paths.tables_dir / "track_c_s2_review_volume_by_month.parquet")
    write_parquet(
        quarterly_df,
        paths.tables_dir / "track_c_s2_review_volume_by_quarter.parquet",
    )
    plot_volume_timeline(
        monthly_df,
        load_analyzable_cities(paths),
        str(paths.figures_dir / "track_c_s2_volume_timeline.png"),
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    main()
