"""Stage 5: Feature correlates within age buckets for Track B."""

from __future__ import annotations

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


def run_numeric_feature_correlates(
    con: duckdb.DuckDBPyConnection,
) -> pd.DataFrame:
    """Compute age-controlled numeric feature associations with useful votes."""
    return con.execute(
        """
        WITH feature_metrics AS (
            SELECT
                age_bucket,
                COUNT(*) AS review_count,
                CORR(useful::DOUBLE, text_word_count::DOUBLE) AS corr_text_word_count,
                CORR(useful::DOUBLE, text_char_count::DOUBLE) AS corr_text_char_count,
                CORR(useful::DOUBLE, review_stars::DOUBLE) AS corr_review_stars,
                CORR(useful::DOUBLE, fans::DOUBLE) AS corr_fans,
                CORR(useful::DOUBLE, user_tenure_days::DOUBLE) AS corr_user_tenure_days
            FROM review_usefulness_snapshot
            GROUP BY age_bucket
        )
        SELECT
            age_bucket,
            review_count,
            'text_word_count' AS feature_name,
            'numeric' AS feature_kind,
            'pearson_correlation' AS metric_name,
            corr_text_word_count AS metric_value,
            NULL::VARCHAR AS subgroup_value,
            NULL::DOUBLE AS subgroup_mean_useful
        FROM feature_metrics
        UNION ALL
        SELECT
            age_bucket,
            review_count,
            'text_char_count',
            'numeric',
            'pearson_correlation',
            corr_text_char_count,
            NULL::VARCHAR,
            NULL::DOUBLE
        FROM feature_metrics
        UNION ALL
        SELECT
            age_bucket,
            review_count,
            'review_stars',
            'numeric',
            'pearson_correlation',
            corr_review_stars,
            NULL::VARCHAR,
            NULL::DOUBLE
        FROM feature_metrics
        UNION ALL
        SELECT
            age_bucket,
            review_count,
            'fans',
            'numeric',
            'pearson_correlation',
            corr_fans,
            NULL::VARCHAR,
            NULL::DOUBLE
        FROM feature_metrics
        UNION ALL
        SELECT
            age_bucket,
            review_count,
            'user_tenure_days',
            'numeric',
            'pearson_correlation',
            corr_user_tenure_days,
            NULL::VARCHAR,
            NULL::DOUBLE
        FROM feature_metrics
        ORDER BY age_bucket, feature_name
        """
    ).fetchdf()


def run_binary_feature_effects(
    con: duckdb.DuckDBPyConnection,
) -> pd.DataFrame:
    """Compute mean useful differences for binary snapshot-safe features."""
    return con.execute(
        """
        WITH binary_metrics AS (
            SELECT
                age_bucket,
                COUNT(*) AS review_count,
                AVG(CASE WHEN elite_flag = 1 THEN useful::DOUBLE END)
                    AS elite_mean_useful,
                AVG(CASE WHEN elite_flag = 0 THEN useful::DOUBLE END)
                    AS non_elite_mean_useful,
                SUM(CASE WHEN elite_flag = 1 THEN 1 ELSE 0 END)
                    AS elite_review_count,
                SUM(CASE WHEN elite_flag = 0 THEN 1 ELSE 0 END)
                    AS non_elite_review_count,
                AVG(CASE WHEN is_open = 1 THEN useful::DOUBLE END)
                    AS open_mean_useful,
                AVG(CASE WHEN is_open = 0 THEN useful::DOUBLE END)
                    AS closed_mean_useful,
                SUM(CASE WHEN is_open = 1 THEN 1 ELSE 0 END)
                    AS open_review_count,
                SUM(CASE WHEN is_open = 0 THEN 1 ELSE 0 END)
                    AS closed_review_count
            FROM review_usefulness_snapshot
            GROUP BY age_bucket
        )
        SELECT
            age_bucket,
            review_count,
            'elite_flag' AS feature_name,
            'binary' AS feature_kind,
            'mean_useful_delta' AS metric_name,
            elite_mean_useful - non_elite_mean_useful AS metric_value,
            'elite=1_vs_0' AS subgroup_value,
            elite_mean_useful AS subgroup_mean_useful
        FROM binary_metrics
        UNION ALL
        SELECT
            age_bucket,
            review_count,
            'is_open',
            'binary',
            'mean_useful_delta',
            open_mean_useful - closed_mean_useful,
            'is_open=1_vs_0',
            open_mean_useful
        FROM binary_metrics
        ORDER BY age_bucket, feature_name
        """
    ).fetchdf()


def run_category_effects(
    con: duckdb.DuckDBPyConnection,
) -> pd.DataFrame:
    """Surface the highest-volume categories within each age bucket."""
    return con.execute(
        """
        WITH grouped_categories AS (
            SELECT
                age_bucket,
                primary_category,
                COUNT(*) AS review_count,
                AVG(useful::DOUBLE) AS mean_useful
            FROM review_usefulness_snapshot
            WHERE primary_category IS NOT NULL AND primary_category <> ''
            GROUP BY age_bucket, primary_category
        ),
        category_stats AS (
            SELECT
                *,
                ROW_NUMBER() OVER (
                    PARTITION BY age_bucket
                    ORDER BY review_count DESC, primary_category
                ) AS size_rank
            FROM grouped_categories
        ),
        age_baseline AS (
            SELECT
                age_bucket,
                AVG(useful::DOUBLE) AS baseline_mean_useful
            FROM review_usefulness_snapshot
            GROUP BY age_bucket
        )
        SELECT
            category_stats.age_bucket,
            category_stats.review_count,
            'primary_category' AS feature_name,
            'category' AS feature_kind,
            'relative_mean_useful' AS metric_name,
            category_stats.mean_useful - age_baseline.baseline_mean_useful
                AS metric_value,
            category_stats.primary_category AS subgroup_value,
            category_stats.mean_useful AS subgroup_mean_useful
        FROM category_stats
        JOIN age_baseline USING (age_bucket)
        WHERE size_rank <= 5
        ORDER BY age_bucket, review_count DESC, subgroup_value
        """
    ).fetchdf()


def plot_stars_vs_useful_within_age(
    con: duckdb.DuckDBPyConnection,
    paths: TrackBPaths,
) -> None:
    """Plot mean useful votes by review stars inside each age bucket."""
    df = con.execute(
        """
        SELECT
            age_bucket,
            review_stars,
            AVG(useful::DOUBLE) AS mean_useful
        FROM review_usefulness_snapshot
        GROUP BY age_bucket, review_stars
        ORDER BY age_bucket, review_stars
        """
    ).fetchdf()

    fig, ax = plt.subplots(figsize=(11, 7))
    for age_bucket, bucket_df in df.groupby("age_bucket", sort=False):
        ax.plot(
            bucket_df["review_stars"],
            bucket_df["mean_useful"],
            marker="o",
            linewidth=1.8,
            label=age_bucket,
        )

    ax.set_xlabel("Review Stars")
    ax.set_ylabel("Mean Useful Votes")
    ax.set_title("Track B: Review Stars vs Useful Votes Within Age Buckets")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    out = paths.figures_dir / "track_b_s5_stars_vs_useful_within_age.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    logger.info("Wrote %s", out)


def plot_elite_vs_useful_within_age(
    con: duckdb.DuckDBPyConnection,
    paths: TrackBPaths,
) -> None:
    """Plot elite versus non-elite mean useful votes by age bucket."""
    df = con.execute(
        """
        SELECT
            age_bucket,
            elite_flag,
            AVG(useful::DOUBLE) AS mean_useful
        FROM review_usefulness_snapshot
        GROUP BY age_bucket, elite_flag
        ORDER BY age_bucket, elite_flag
        """
    ).fetchdf()

    pivot = (
        df.pivot(index="age_bucket", columns="elite_flag", values="mean_useful")
        .fillna(0.0)
        .rename(columns={0: "non_elite", 1: "elite"})
    )

    fig, ax = plt.subplots(figsize=(11, 7))
    pivot.plot(kind="bar", ax=ax, color=["#6c8ebf", "#c96c5b"])
    ax.set_xlabel("Age Bucket")
    ax.set_ylabel("Mean Useful Votes")
    ax.set_title("Track B: Elite Status vs Useful Votes Within Age Buckets")
    ax.tick_params(axis="x", rotation=25)
    ax.legend(title="Reviewer Segment")
    fig.tight_layout()
    out = paths.figures_dir / "track_b_s5_elite_vs_useful_within_age.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    logger.info("Wrote %s", out)


def build_feature_correlates(
    con: duckdb.DuckDBPyConnection,
) -> pd.DataFrame:
    """Build the combined Stage 5 feature correlate table."""
    frames = [
        run_numeric_feature_correlates(con),
        run_binary_feature_effects(con),
        run_category_effects(con),
    ]
    return pd.concat(frames, ignore_index=True)


def _load_recommended_buckets(tables_dir: "Path") -> set[str] | None:
    """Return recommended age buckets from Stage 3, or None if artifact absent."""
    from pathlib import Path as _Path

    recommended_path = _Path(str(tables_dir)) / "track_b_s3_recommended_age_buckets.parquet"
    if not recommended_path.is_file():
        return None
    df = pd.read_parquet(recommended_path)
    if "recommended_for_modeling" not in df.columns:
        return None
    return set(df.loc[df["recommended_for_modeling"], "age_bucket"].tolist())


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 5: Feature Correlates")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(args.config)

    paths = resolve_paths(config)
    ensure_output_dirs(paths)

    recommended_buckets = _load_recommended_buckets(paths.tables_dir)
    if recommended_buckets is not None and not recommended_buckets:
        raise RuntimeError(
            "Stage 3 filtered all age buckets below the qualifying-groups gate. "
            "No age buckets are available for feature correlation analysis. "
            "Inspect 'track_b_s3_recommended_age_buckets.parquet' for details."
        )

    con = connect_duckdb(config)
    try:
        create_snapshot_view(con, config, paths)
        if recommended_buckets is not None:
            bucket_sql = ", ".join(f"'{b}'" for b in sorted(recommended_buckets))
            con.execute(
                f"CREATE TEMP TABLE _snapshot_filtered AS "
                f"SELECT * FROM review_usefulness_snapshot "
                f"WHERE age_bucket IN ({bucket_sql})"
            )
            con.execute("DROP VIEW IF EXISTS review_usefulness_snapshot")
            con.execute(
                "CREATE TEMP VIEW review_usefulness_snapshot AS "
                "SELECT * FROM _snapshot_filtered"
            )
        correlates = build_feature_correlates(con)
        plot_stars_vs_useful_within_age(con, paths)
        plot_elite_vs_useful_within_age(con, paths)
    finally:
        con.close()

    out = paths.tables_dir / "track_b_s5_feature_correlates.parquet"
    correlates.to_parquet(out, index=False)
    logger.info("Wrote %s (%d rows)", out, len(correlates))
    logger.info("Stage 5 complete.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    main()
