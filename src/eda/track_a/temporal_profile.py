"""Stage 1: Temporal Profile -- star distributions and review volume over time."""

import argparse
import logging
from pathlib import Path
from typing import Any

import duckdb
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from src.common.config import load_config
from src.common.db import connect_duckdb

matplotlib.use("Agg")

logger = logging.getLogger(__name__)


def _resolve(config: dict[str, Any], key: str) -> Path:
    return Path(config["paths"][key])


def run_star_distribution(con: duckdb.DuckDBPyConnection, curated: Path, tables: Path) -> pd.DataFrame:
    """Star counts grouped by year, month, and star rating."""
    pq = str(curated / "review_fact.parquet").replace("\\", "/")
    sql = f"""
        SELECT
            review_year,
            review_month,
            review_stars,
            COUNT(*)        AS review_count,
            AVG(review_stars) AS mean_stars
        FROM read_parquet('{pq}')
        GROUP BY review_year, review_month, review_stars
        ORDER BY review_year, review_month, review_stars
    """
    df = con.execute(sql).fetchdf()
    out = tables / "track_a_s1_stars_by_year_month.parquet"
    df.to_parquet(out, index=False)
    logger.info("Wrote %s (%d rows)", out, len(df))
    return df


def run_monthly_volume(con: duckdb.DuckDBPyConnection, curated: Path, tables: Path) -> pd.DataFrame:
    """Monthly review volume with count, mean, and stddev."""
    pq = str(curated / "review_fact.parquet").replace("\\", "/")
    sql = f"""
        SELECT
            DATE_TRUNC('month', review_date) AS period,
            COUNT(*)                         AS review_count,
            AVG(review_stars)                AS mean_stars,
            STDDEV(review_stars)             AS std_stars
        FROM read_parquet('{pq}')
        GROUP BY period
        ORDER BY period
    """
    df = con.execute(sql).fetchdf()
    out = tables / "track_a_s1_review_volume_by_period.parquet"
    df.to_parquet(out, index=False)
    logger.info("Wrote %s (%d rows)", out, len(df))
    return df


def plot_star_distribution(df: pd.DataFrame, figures: Path) -> None:
    """Stacked bar chart of star-rating percentage by year."""
    pivot = df.groupby(["review_year", "review_stars"])["review_count"].sum().unstack(fill_value=0)
    pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

    fig, ax = plt.subplots(figsize=(12, 6))
    pct.plot(kind="bar", stacked=True, ax=ax, colormap="RdYlGn")
    ax.set_xlabel("Year")
    ax.set_ylabel("Percentage of Reviews")
    ax.set_title("Star Rating Distribution Over Time")
    ax.legend(title="Stars", bbox_to_anchor=(1.05, 1), loc="upper left")
    fig.tight_layout()
    out = figures / "track_a_s1_star_distribution_over_time.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    logger.info("Wrote %s", out)


def plot_volume_timeline(df: pd.DataFrame, figures: Path) -> None:
    """Dual-axis chart: monthly review count + mean stars."""
    fig, ax1 = plt.subplots(figsize=(14, 6))
    ax1.bar(df["period"], df["review_count"], width=25, alpha=0.6, label="Review Count")
    ax1.set_xlabel("Month")
    ax1.set_ylabel("Review Count", color="tab:blue")
    ax1.tick_params(axis="y", labelcolor="tab:blue")

    ax2 = ax1.twinx()
    ax2.plot(df["period"], df["mean_stars"], color="tab:red", linewidth=1.5, label="Mean Stars")
    ax2.set_ylabel("Mean Stars", color="tab:red")
    ax2.tick_params(axis="y", labelcolor="tab:red")

    fig.suptitle("Monthly Review Volume and Mean Stars")
    fig.tight_layout()
    out = figures / "track_a_s1_review_volume_timeline.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    logger.info("Wrote %s", out)


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 1: Temporal Profile")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(args.config)

    curated = _resolve(config, "curated_dir")
    tables = _resolve(config, "tables_dir")
    figures = _resolve(config, "figures_dir")
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)

    db_path = _resolve(config, "db_path")
    con = connect_duckdb(config, db_path=db_path, read_only=True)
    try:
        stars_df = run_star_distribution(con, curated, tables)
        volume_df = run_monthly_volume(con, curated, tables)
    finally:
        con.close()

    plot_star_distribution(stars_df, figures)
    plot_volume_timeline(volume_df, figures)
    logger.info("Stage 1 complete.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    main()
