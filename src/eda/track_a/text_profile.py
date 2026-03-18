"""Stage 2: Text profile using Track A-safe text length proxies."""

import argparse
import logging
from pathlib import Path
from typing import Any

import duckdb
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from src.common.config import load_config

matplotlib.use("Agg")

logger = logging.getLogger(__name__)


def _resolve(config: dict[str, Any], key: str) -> Path:
    return Path(config["paths"][key])


def compute_text_length_stats(
    con: duckdb.DuckDBPyConnection,
    review_fact_path: Path,
    tables: Path,
    min_nonempty_rate: float,
) -> pd.DataFrame:
    """Compute text-length summary statistics from Track A-safe derived columns."""
    sql = """
        SELECT
            review_stars,
            COUNT(*) AS n_reviews,
            AVG(text_word_count) AS mean_words,
            MEDIAN(text_word_count) AS median_words,
            STDDEV_SAMP(text_word_count) AS std_words,
            MIN(text_word_count) AS min_words,
            MAX(text_word_count) AS max_words,
            AVG(text_char_count) AS mean_chars,
            MEDIAN(text_char_count) AS median_chars,
            STDDEV_SAMP(text_char_count) AS std_chars,
            AVG(CASE WHEN text_word_count > 0 THEN 1.0 ELSE 0.0 END) AS nonempty_text_rate
        FROM read_parquet($1)
        GROUP BY review_stars
        ORDER BY review_stars
    """
    df = con.execute(sql, [str(review_fact_path)]).fetchdf()
    out = tables / "track_a_s2_text_length_stats.parquet"
    df.to_parquet(out, index=False)
    logger.info("Wrote %s (%d rows)", out, len(df))

    overall_rate = con.execute(
        """
        SELECT AVG(CASE WHEN text_word_count > 0 THEN 1.0 ELSE 0.0 END)
        FROM read_parquet($1)
        """,
        [str(review_fact_path)],
    ).fetchone()[0]
    if overall_rate is not None and float(overall_rate) < min_nonempty_rate:
        logger.warning(
            "Text non-empty rate %.4f is below configured threshold %.4f",
            float(overall_rate),
            min_nonempty_rate,
        )

    return df


def compute_sentiment(
    con: duckdb.DuckDBPyConnection,
    review_path: Path,
    review_fact_path: Path,
    config: dict[str, Any],
    tables: Path,
) -> pd.DataFrame | None:
    """Optionally compute aggregate sentiment from raw review text only.

    Restricts sampling to review_ids present in review_fact so that only
    curated, Track A-safe reviews are included (data-governance semijoin).
    """
    if not review_path.is_file():
        logger.warning("Missing %s; skipping optional sentiment proxy stage.", review_path)
        return None

    try:
        from textblob import TextBlob
    except ImportError:
        logger.warning("TextBlob not installed; skipping optional sentiment proxy stage.")
        return None

    sample_size = int(config.get("eda", {}).get("sentiment_sample_size", 50_000))
    # Semijoin against review_fact to restrict to curated review_ids only
    sql = f"""
        SELECT
            r.review_id,
            r.stars AS review_stars,
            r.text AS review_text
        FROM read_parquet($1) AS r
        WHERE r.review_id IN (SELECT review_id FROM read_parquet($2))
          AND r.text IS NOT NULL AND LENGTH(TRIM(r.text)) > 0
        USING SAMPLE {sample_size} ROWS
    """
    sample_df = con.execute(sql, [str(review_path), str(review_fact_path)]).fetchdf()
    if sample_df.empty:
        logger.warning("Sentiment sample is empty; skipping optional sentiment output.")
        return None

    sample_df["polarity"] = sample_df["review_text"].apply(
        lambda text: TextBlob(str(text)).sentiment.polarity
    )
    sample_df = sample_df.drop(columns=["review_id", "review_text"])

    sentiment_df = (
        sample_df.groupby("review_stars", dropna=False)["polarity"]
        .agg(["count", "mean", "median", "std"])
        .reset_index()
        .rename(columns={"count": "sample_size", "mean": "mean_polarity", "std": "std_polarity"})
    )
    out = tables / "track_a_s2_sentiment_by_star.parquet"
    sentiment_df.to_parquet(out, index=False)
    logger.info("Wrote %s (%d rows)", out, len(sentiment_df))
    return sentiment_df


def plot_text_length_boxplot(
    con: duckdb.DuckDBPyConnection,
    review_fact_path: Path,
    figures: Path,
) -> None:
    """Boxplot of text word counts by star rating."""
    sql = """
        SELECT review_stars, text_word_count
        FROM read_parquet($1)
        WHERE text_word_count IS NOT NULL
        USING SAMPLE 200000 ROWS
    """
    df = con.execute(sql, [str(review_fact_path)]).fetchdf()
    if df.empty:
        logger.warning("No rows available for text length boxplot.")
        return

    ordered_stars = sorted(df["review_stars"].dropna().unique())
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.boxplot(
        [df.loc[df["review_stars"] == star, "text_word_count"].values for star in ordered_stars],
        labels=ordered_stars,
        showfliers=False,
    )
    ax.set_xlabel("Star Rating")
    ax.set_ylabel("Word Count")
    ax.set_title("Track A: Text Length by Star Rating")
    fig.tight_layout()
    out = figures / "track_a_s2_text_length_by_star.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    logger.info("Wrote %s", out)


def plot_text_length_histogram(
    con: duckdb.DuckDBPyConnection,
    review_fact_path: Path,
    figures: Path,
) -> None:
    """Histogram of text word counts."""
    sql = """
        SELECT text_word_count
        FROM read_parquet($1)
        WHERE text_word_count IS NOT NULL
        USING SAMPLE 500000 ROWS
    """
    df = con.execute(sql, [str(review_fact_path)]).fetchdf()
    if df.empty:
        logger.warning("No rows available for text length histogram.")
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(df["text_word_count"].clip(upper=1000), bins=100, edgecolor="black", alpha=0.7)
    ax.set_xlabel("Word Count (capped at 1000)")
    ax.set_ylabel("Frequency")
    ax.set_title("Track A: Review Text Length Distribution")
    fig.tight_layout()
    out = figures / "track_a_s2_text_length_distribution.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    logger.info("Wrote %s", out)


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 2: Text Profile")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(args.config)

    curated = _resolve(config, "curated_dir")
    tables = _resolve(config, "tables_dir")
    figures = _resolve(config, "figures_dir")
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)

    review_fact_path = curated / "review_fact.parquet"
    review_path = curated / "review.parquet"
    nonempty_threshold = float(config.get("quality", {}).get("text_nonnull_threshold", 0.99))

    con = duckdb.connect()
    try:
        compute_text_length_stats(con, review_fact_path, tables, nonempty_threshold)
        compute_sentiment(con, review_path, review_fact_path, config, tables)
        plot_text_length_boxplot(con, review_fact_path, figures)
        plot_text_length_histogram(con, review_fact_path, figures)
    finally:
        con.close()

    logger.info("Stage 2 complete.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    main()
