"""Stage 3: User and business history profiles with strict earlier-date semantics."""

import argparse
import logging
from pathlib import Path
from typing import Any

import duckdb
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.common.config import load_config
from src.common.db import connect_duckdb

matplotlib.use("Agg")

logger = logging.getLogger(__name__)


def _resolve(config: dict[str, Any], key: str) -> Path:
    return Path(config["paths"][key])


# ---------------------------------------------------------------------------
# User history
# ---------------------------------------------------------------------------

_LOAD_RF_SQL = """
CREATE OR REPLACE TEMP TABLE rf_cache AS
SELECT * FROM read_parquet('{path}')
"""

_USER_DAY_STATS_SQL = """
CREATE OR REPLACE TEMP TABLE user_day_stats AS
SELECT
    user_id,
    review_date,
    COUNT(*)                     AS reviews_on_day,
    SUM(review_stars)            AS stars_sum_on_day,
    SUM(review_stars * review_stars) AS stars_sq_sum_on_day
FROM rf_cache
GROUP BY user_id, review_date
"""

_USER_DAY_HISTORY_SQL = """
CREATE OR REPLACE TEMP TABLE user_day_history AS
SELECT
    user_id,
    review_date,
    SUM(reviews_on_day) OVER w AS cumul_reviews,
    SUM(stars_sum_on_day) OVER w AS cumul_stars_sum,
    SUM(stars_sq_sum_on_day) OVER w AS cumul_stars_sq_sum
FROM user_day_stats
WINDOW w AS (
    PARTITION BY user_id
    ORDER BY review_date
    ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
)
"""

_USER_HISTORY_ASOF_SQL = """
CREATE OR REPLACE TEMP TABLE user_history_asof AS
SELECT
    rf.review_id,
    rf.user_id,
    rf.review_date,
    COALESCE(udh.cumul_reviews, 0)   AS user_prior_review_count,
    CASE WHEN COALESCE(udh.cumul_reviews, 0) > 0
         THEN udh.cumul_stars_sum / udh.cumul_reviews
         ELSE NULL END               AS user_prior_avg_stars,
    CASE WHEN COALESCE(udh.cumul_reviews, 0) > 1
         THEN SQRT(
              (udh.cumul_stars_sq_sum - (udh.cumul_stars_sum * udh.cumul_stars_sum) / udh.cumul_reviews)
              / (udh.cumul_reviews - 1)
         )
         ELSE NULL END               AS user_prior_std_stars
FROM rf_cache rf
LEFT JOIN user_day_history udh
  ON rf.user_id = udh.user_id
  AND rf.review_date = udh.review_date
"""

# ---------------------------------------------------------------------------
# Business history
# ---------------------------------------------------------------------------

_BIZ_DAY_STATS_SQL = """
CREATE OR REPLACE TEMP TABLE biz_day_stats AS
SELECT
    business_id,
    review_date,
    COUNT(*)                     AS reviews_on_day,
    SUM(review_stars)            AS stars_sum_on_day,
    SUM(review_stars * review_stars) AS stars_sq_sum_on_day
FROM rf_cache
GROUP BY business_id, review_date
"""

_BIZ_DAY_HISTORY_SQL = """
CREATE OR REPLACE TEMP TABLE biz_day_history AS
SELECT
    business_id,
    review_date,
    SUM(reviews_on_day) OVER w AS cumul_reviews,
    SUM(stars_sum_on_day) OVER w AS cumul_stars_sum,
    SUM(stars_sq_sum_on_day) OVER w AS cumul_stars_sq_sum
FROM biz_day_stats
WINDOW w AS (
    PARTITION BY business_id
    ORDER BY review_date
    ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
)
"""

_BIZ_HISTORY_ASOF_SQL = """
CREATE OR REPLACE TEMP TABLE biz_history_asof AS
SELECT
    rf.review_id,
    rf.business_id,
    rf.review_date,
    COALESCE(bdh.cumul_reviews, 0)   AS biz_prior_review_count,
    CASE WHEN COALESCE(bdh.cumul_reviews, 0) > 0
         THEN bdh.cumul_stars_sum / bdh.cumul_reviews
         ELSE NULL END               AS biz_prior_avg_stars,
    CASE WHEN COALESCE(bdh.cumul_reviews, 0) > 1
         THEN SQRT(
              (bdh.cumul_stars_sq_sum - (bdh.cumul_stars_sum * bdh.cumul_stars_sum) / bdh.cumul_reviews)
              / (bdh.cumul_reviews - 1)
         )
         ELSE NULL END               AS biz_prior_std_stars
FROM rf_cache rf
LEFT JOIN biz_day_history bdh
  ON rf.business_id = bdh.business_id
  AND rf.review_date = bdh.review_date
"""

# ---------------------------------------------------------------------------
# Profile query
# ---------------------------------------------------------------------------

_PROFILE_SQL = """
SELECT
    CASE
        WHEN user_prior_review_count = 0 THEN '0 (first review)'
        WHEN user_prior_review_count BETWEEN 1 AND 4 THEN '1-4'
        WHEN user_prior_review_count BETWEEN 5 AND 19 THEN '5-19'
        WHEN user_prior_review_count BETWEEN 20 AND 99 THEN '20-99'
        ELSE '100+'
    END AS bucket,
    COUNT(*)                          AS n_reviews,
    AVG(user_prior_avg_stars)         AS mean_prior_avg_stars,
    AVG(user_prior_std_stars)         AS mean_prior_std_stars
FROM user_history_asof
GROUP BY bucket
ORDER BY
    CASE bucket
        WHEN '0 (first review)' THEN 0
        WHEN '1-4' THEN 1
        WHEN '5-19' THEN 2
        WHEN '20-99' THEN 3
        ELSE 4
    END
"""


def load_review_fact_cache(con: duckdb.DuckDBPyConnection, parquet_path: str) -> None:
    """Load review_fact into a temp table so all queries read from memory."""
    pq = str(parquet_path).replace("\\", "/")
    con.execute(_LOAD_RF_SQL.format(path=pq))
    rows = con.execute("SELECT COUNT(*) FROM rf_cache").fetchone()[0]  # type: ignore[index]
    logger.info("Cached review_fact: %d rows", rows)


def build_user_history(con: duckdb.DuckDBPyConnection) -> None:
    """Build user as-of history temp tables (requires rf_cache)."""
    con.execute(_USER_DAY_STATS_SQL)
    con.execute(_USER_DAY_HISTORY_SQL)
    con.execute(_USER_HISTORY_ASOF_SQL)
    logger.info("Built user_history_asof temp table.")


def build_business_history(con: duckdb.DuckDBPyConnection) -> None:
    """Build business as-of history temp tables (requires rf_cache)."""
    con.execute(_BIZ_DAY_STATS_SQL)
    con.execute(_BIZ_DAY_HISTORY_SQL)
    con.execute(_BIZ_HISTORY_ASOF_SQL)
    logger.info("Built biz_history_asof temp table.")


def export_history_tables(con: duckdb.DuckDBPyConnection, tables: Path) -> None:
    """Persist Track A-owned history artifacts for later stages."""
    user_out = tables / "track_a_s3_user_history_asof.parquet"
    user_out_str = str(user_out).replace("\\", "/")
    con.execute(
        f"COPY user_history_asof TO '{user_out_str}' (FORMAT PARQUET, COMPRESSION ZSTD)"
    )
    logger.info("Exported %s", user_out)

    biz_out = tables / "track_a_s3_business_history_asof.parquet"
    biz_out_str = str(biz_out).replace("\\", "/")
    con.execute(
        f"COPY biz_history_asof TO '{biz_out_str}' (FORMAT PARQUET, COMPRESSION ZSTD)"
    )
    logger.info("Exported %s", biz_out)


def profile_user_history(con: duckdb.DuckDBPyConnection, tables: Path) -> pd.DataFrame:
    """Bucket user prior review counts and write profile table."""
    df = con.execute(_PROFILE_SQL).fetchdf()
    out = tables / "track_a_s3_user_history_depth.parquet"
    df.to_parquet(out, index=False)
    logger.info("Wrote %s (%d rows)", out, len(df))
    return df


def plot_prior_count_cdf(con: duckdb.DuckDBPyConnection, figures: Path) -> None:
    """CDF of user_prior_review_count."""
    df = con.execute(
        "SELECT user_prior_review_count FROM user_history_asof"
    ).fetchdf()
    if df.empty:
        logger.warning("No rows available for prior-count CDF.")
        return
    values = np.sort(df["user_prior_review_count"].values)
    cdf = np.arange(1, len(values) + 1) / len(values)

    fig, ax = plt.subplots(figsize=(10, 6))
    # Subsample for plotting efficiency
    step = max(1, len(values) // 10_000)
    ax.plot(values[::step], cdf[::step], linewidth=1.2)
    ax.set_xlabel("User Prior Review Count")
    ax.set_ylabel("CDF")
    ax.set_title("CDF of User Prior Review Count")
    ax.set_xscale("symlog")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    out = figures / "track_a_s3_user_prior_review_count_dist.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    logger.info("Wrote %s", out)


def plot_tenure_vs_rating_var(
    con: duckdb.DuckDBPyConnection,
    figures: Path,
) -> None:
    """Scatter: user tenure vs prior rating std (sampled). Requires rf_cache."""
    sql = """
        SELECT
            rf.user_tenure_days,
            uha.user_prior_std_stars
        FROM user_history_asof uha
        JOIN rf_cache rf USING (review_id)
        WHERE rf.user_tenure_days IS NOT NULL
          AND uha.user_prior_std_stars IS NOT NULL
        USING SAMPLE 50000 ROWS
    """
    df = con.execute(sql).fetchdf()
    if df.empty:
        logger.warning("No rows available for tenure-vs-variance plot.")
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(
        df["user_tenure_days"],
        df["user_prior_std_stars"],
        alpha=0.1, s=3,
    )
    ax.set_xlabel("User Tenure Days")
    ax.set_ylabel("Prior Rating Std Dev")
    ax.set_title("Track A: User Tenure vs Prior Rating Variability")
    ax.set_xscale("symlog")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    out = figures / "track_a_s3_user_tenure_vs_rating_var.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    logger.info("Wrote %s", out)


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 3: User History Profile")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(args.config)

    curated = _resolve(config, "curated_dir")
    tables = _resolve(config, "tables_dir")
    figures = _resolve(config, "figures_dir")
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)

    parquet_path = str(curated / "review_fact.parquet")

    con = connect_duckdb(config)
    try:
        load_review_fact_cache(con, parquet_path)
        build_user_history(con)
        build_business_history(con)
        export_history_tables(con, tables)
        profile_user_history(con, tables)
        plot_prior_count_cdf(con, figures)
        plot_tenure_vs_rating_var(con, figures)
    finally:
        con.close()

    logger.info("Stage 3 complete.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    main()
