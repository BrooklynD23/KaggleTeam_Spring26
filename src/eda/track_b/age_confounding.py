"""Stage 2: Age confounding analysis for Track B."""

import argparse
import logging
from pathlib import Path

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


def run_age_effect_summary(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Summarize usefulness behavior within each configured age bucket."""
    return con.execute(
        """
        SELECT
            age_bucket,
            MIN(review_age_days) AS min_age_days,
            MAX(review_age_days) AS max_age_days,
            COUNT(*) AS review_count,
            ROUND(AVG(useful), 4) AS mean_useful,
            MEDIAN(useful) AS median_useful,
            ROUND(AVG(CASE WHEN useful = 0 THEN 1.0 ELSE 0.0 END), 4) AS pct_zero_useful,
            ROUND(AVG(text_word_count), 2) AS mean_text_word_count
        FROM review_usefulness_snapshot
        GROUP BY age_bucket
        ORDER BY MIN(review_age_days)
        """
    ).fetchdf()


def plot_useful_by_age_bucket(df: pd.DataFrame, paths: TrackBPaths) -> None:
    """Plot mean useful votes by age bucket with review counts annotated."""
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(df["age_bucket"], df["mean_useful"], color="steelblue", alpha=0.85)
    ax.set_xlabel("Age Bucket")
    ax.set_ylabel("Mean Useful Votes")
    ax.set_title("Track B: Mean Useful Votes by Age Bucket")
    ax.tick_params(axis="x", rotation=25)

    for bar, count in zip(bars, df["review_count"], strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"n={int(count)}",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    fig.tight_layout()
    out = paths.figures_dir / "track_b_s2_useful_by_age_bucket.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    logger.info("Wrote %s", out)


def plot_textlen_vs_useful_within_age(
    con: duckdb.DuckDBPyConnection,
    paths: TrackBPaths,
) -> None:
    """Plot text length vs useful votes on an age-stratified sample."""
    df = con.execute(
        """
        SELECT
            age_bucket,
            text_word_count,
            useful
        FROM review_usefulness_snapshot
        WHERE text_word_count IS NOT NULL
        USING SAMPLE 50000
        """
    ).fetchdf()

    fig, ax = plt.subplots(figsize=(11, 7))
    for age_bucket, bucket_df in df.groupby("age_bucket", sort=False):
        ax.scatter(
            bucket_df["text_word_count"].clip(upper=1200),
            bucket_df["useful"].clip(upper=100),
            s=6,
            alpha=0.15,
            label=age_bucket,
        )

    ax.set_xlabel("Text Word Count (capped at 1200)")
    ax.set_ylabel("Useful Votes (capped at 100)")
    ax.set_title("Track B: Text Length vs Useful Votes Within Age Buckets")
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    out = paths.figures_dir / "track_b_s2_textlen_vs_useful_within_age.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    logger.info("Wrote %s", out)


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 2: Age Confounding")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(args.config)

    paths = resolve_paths(config)
    ensure_output_dirs(paths)

    con = connect_duckdb(config)
    try:
        create_snapshot_view(con, config, paths)
        summary = run_age_effect_summary(con)
        plot_textlen_vs_useful_within_age(con, paths)
    finally:
        con.close()

    # Mark all configured buckets as candidates; Stage 3 is the authoritative filter
    summary["recommended_for_modeling"] = True
    out = paths.tables_dir / "track_b_s2_age_effect_summary.parquet"
    summary.to_parquet(out, index=False)
    logger.info("Wrote %s (%d rows)", out, len(summary))
    plot_useful_by_age_bucket(summary, paths)
    logger.info("Stage 2 complete.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    main()
