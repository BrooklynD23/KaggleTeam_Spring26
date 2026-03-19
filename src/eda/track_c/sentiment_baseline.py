"""Stage 4: Sentiment baseline for Track C."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import duckdb
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import spearmanr

from src.common.config import load_config
from src.common.db import connect_duckdb
from src.eda.track_c.common import (
    drop_raw_text_columns,
    ensure_output_dirs,
    load_analyzable_cities,
    load_review_text_sample,
    month_label,
    resolve_paths,
    save_placeholder_figure,
    sentiment_score,
    write_parquet,
)

matplotlib.use("Agg")

logger = logging.getLogger(__name__)


def build_sentiment_aggregate(
    con: duckdb.DuckDBPyConnection,
    review_path: str,
    review_fact_path: str,
    sample_size: int,
    seed: int,
    engine: str,
    analyzable_cities: set[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compute review-level sentiment then aggregate to city-month."""
    sample_df = load_review_text_sample(
        con,
        Path(review_path),
        Path(review_fact_path),
        sample_size,
        seed,
    )
    if sample_df.empty:
        empty = pd.DataFrame(
            columns=[
                "city",
                "normalized_city",
                "state",
                "year_month",
                "mean_sentiment",
                "std_sentiment",
                "review_count",
                "mean_stars",
            ]
        )
        return empty, pd.DataFrame(columns=["review_stars", "sentiment"])

    sample_df["sentiment"] = sample_df["review_text"].astype(str).apply(
        lambda text: sentiment_score(text, engine=engine)
    )
    sample_df["normalized_city"] = sample_df["city"].astype(str).str.strip().str.lower()
    sample_df["year_month"] = [
        month_label(year, month)
        for year, month in zip(sample_df["review_year"], sample_df["review_month"], strict=True)
    ]
    if analyzable_cities:
        sample_df = sample_df.loc[
            sample_df["normalized_city"].isin(analyzable_cities)
        ].copy()
    aggregate = (
        sample_df.groupby(
            ["city", "normalized_city", "state", "year_month"],
            dropna=False,
            as_index=False,
        )
        .agg(
            mean_sentiment=("sentiment", "mean"),
            std_sentiment=("sentiment", "std"),
            review_count=("review_id", "count"),
            mean_stars=("review_stars", "mean"),
        )
        .sort_values(["city", "year_month"])
    )
    review_level = drop_raw_text_columns(
        sample_df.loc[:, ["review_stars", "sentiment"]]
    )
    return aggregate, review_level


def plot_sentiment_vs_stars(review_level: pd.DataFrame, output_path: str) -> None:
    """Plot review-level stars against computed sentiment."""
    from pathlib import Path

    if review_level.empty:
        save_placeholder_figure(Path(output_path), "Track C: Sentiment vs Stars")
        return
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(review_level["review_stars"], review_level["sentiment"], alpha=0.12, s=6)
    ax.set_xlabel("Review Stars")
    ax.set_ylabel("Sentiment Score")
    ax.set_title("Track C: Sentiment Proxy vs Star Ratings")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    logger.info("Wrote %s", output_path)


def plot_top_city_timeseries(aggregate_df: pd.DataFrame, output_path: str) -> None:
    """Plot sentiment time series for the top cities."""
    from pathlib import Path

    if aggregate_df.empty:
        save_placeholder_figure(Path(output_path), "Track C: Top-City Sentiment Over Time")
        return
    top_cities = (
        aggregate_df.groupby("city")["review_count"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .index.tolist()
    )
    fig, ax = plt.subplots(figsize=(12, 6))
    for city in top_cities:
        city_df = aggregate_df.loc[aggregate_df["city"] == city].sort_values("year_month")
        ax.plot(city_df["year_month"], city_df["mean_sentiment"], label=city)
    ax.set_title("Track C: Sentiment Time Series for Top Cities")
    ax.set_ylabel("Mean Sentiment")
    ax.tick_params(axis="x", rotation=45)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    logger.info("Wrote %s", output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 4: Sentiment Baseline")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(args.config)

    paths = resolve_paths(config)
    ensure_output_dirs(paths)
    analyzable_cities = load_analyzable_cities(paths)

    sample_size = int(config.get("nlp", {}).get("sample_size", 100_000))
    seed = int(config.get("nlp", {}).get("random_seed", 42))
    engine = str(config.get("nlp", {}).get("sentiment_engine", "textblob"))
    min_corr = float(
        config.get("quality", {}).get("sentiment_star_correlation_min", 0.3)
    )

    con = connect_duckdb(config)
    try:
        aggregate_df, review_level = build_sentiment_aggregate(
            con,
            str(paths.review_path),
            str(paths.review_fact_path),
            sample_size,
            seed,
            engine,
            analyzable_cities,
        )
    finally:
        con.close()

    if not review_level.empty:
        corr = spearmanr(review_level["review_stars"], review_level["sentiment"]).statistic
        if corr is not None and float(corr) < min_corr:
            logger.warning(
                "Track C sentiment/star Spearman correlation %.4f is below threshold %.4f",
                float(corr),
                min_corr,
            )

    write_parquet(
        aggregate_df,
        paths.tables_dir / "track_c_s4_sentiment_by_city_month.parquet",
    )
    plot_sentiment_vs_stars(
        review_level,
        str(paths.figures_dir / "track_c_s4_sentiment_vs_stars.png"),
    )
    plot_top_city_timeseries(
        aggregate_df,
        str(paths.figures_dir / "track_c_s4_sentiment_timeseries_top_cities.png"),
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    main()
