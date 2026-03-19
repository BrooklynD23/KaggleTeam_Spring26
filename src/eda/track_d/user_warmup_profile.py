"""Stage 6: D2 warm-up profile and feature coverage.

Rewritten to use a single-pass inequality join instead of repeated per-date
full scans of review_fact.parquet.
"""

from __future__ import annotations

import argparse
import logging
import time

import duckdb
import pandas as pd

from src.common.config import load_config
from src.common.db import connect_duckdb
from src.eda.track_d.common import ensure_output_dirs, feature_coverage_frame, resolve_paths

logger = logging.getLogger(__name__)

WARMUP_COLS = [
    "prior_categories",
    "prior_cities",
    "prior_avg_stars",
    "prior_review_length_mean",
    "prior_unique_business_count",
]

_WARMUP_SQL = """
WITH prior_agg AS (
    SELECT
        c.user_id,
        c.as_of_date,
        STRING_AGG(DISTINCT TRIM(SPLIT_PART(r.categories, ',', 1)), '|')
            AS prior_categories,
        STRING_AGG(DISTINCT r.city, '|')
            AS prior_cities,
        AVG(r.review_stars)
            AS prior_avg_stars,
        AVG(r.text_word_count)
            AS prior_review_length_mean,
        COUNT(DISTINCT r.business_id)
            AS prior_unique_business_count
    FROM cohort_tbl c
    JOIN rf_tbl r
        ON r.user_id = c.user_id
        AND r.review_date IS NOT NULL
        AND r.review_date < c.as_of_date
    GROUP BY c.user_id, c.as_of_date
)
SELECT
    c.*,
    pa.prior_categories,
    pa.prior_cities,
    pa.prior_avg_stars,
    pa.prior_review_length_mean,
    pa.prior_unique_business_count
FROM cohort_tbl c
LEFT JOIN prior_agg pa
    ON c.user_id = pa.user_id
    AND c.as_of_date = pa.as_of_date
"""


def build_user_warmup_profile_sql(
    con: duckdb.DuckDBPyConnection,
    cohort_path: str,
    review_fact_path: str,
) -> pd.DataFrame:
    """Build as-of aggregate user warm-up features in a single pass.

    Instead of scanning review_fact once per as_of_date, this loads both
    tables once and uses an inequality join (r.review_date < c.as_of_date)
    to compute all dates in one query.
    """
    t0 = time.perf_counter()

    con.execute(
        f"CREATE OR REPLACE TEMP TABLE cohort_tbl AS "
        f"SELECT * FROM read_parquet('{cohort_path}')"
    )
    cohort_rows = con.execute("SELECT COUNT(*) FROM cohort_tbl").fetchone()[0]  # type: ignore[index]
    logger.info("Loaded cohort: %d rows (%.1fs)", cohort_rows, time.perf_counter() - t0)

    distinct_dates = con.execute(
        "SELECT DISTINCT as_of_date::VARCHAR FROM cohort_tbl ORDER BY 1"
    ).fetchall()
    logger.info("Distinct as_of_dates: %s", [d[0] for d in distinct_dates])

    t1 = time.perf_counter()
    user_ids_cte = "SELECT DISTINCT user_id FROM cohort_tbl"
    con.execute(
        f"CREATE OR REPLACE TEMP TABLE rf_tbl AS "
        f"SELECT r.user_id, r.review_date, r.review_stars, r.text_word_count, "
        f"       r.business_id, r.categories, r.city "
        f"FROM read_parquet('{review_fact_path}') r "
        f"WHERE r.user_id IN ({user_ids_cte}) "
        f"  AND r.review_date IS NOT NULL"
    )
    rf_rows = con.execute("SELECT COUNT(*) FROM rf_tbl").fetchone()[0]  # type: ignore[index]
    logger.info(
        "Loaded review_fact (filtered to cohort users): %d rows (%.1fs)",
        rf_rows, time.perf_counter() - t1,
    )

    t2 = time.perf_counter()
    df = con.execute(_WARMUP_SQL).fetchdf()
    logger.info(
        "Warmup aggregation: %d result rows (%.1fs)",
        len(df), time.perf_counter() - t2,
    )

    con.execute("DROP TABLE IF EXISTS cohort_tbl")
    con.execute("DROP TABLE IF EXISTS rf_tbl")

    zero_mask = df["prior_total_interaction_count"].fillna(0).astype(int) == 0
    for col in WARMUP_COLS:
        if col in df.columns:
            df.loc[zero_mask, col] = pd.NA

    logger.info("Total warmup profile build: %.1fs", time.perf_counter() - t0)
    return df


def summarize_feature_coverage(warmup_df: pd.DataFrame) -> pd.DataFrame:
    """Summarize D2 warm-up feature coverage by cohort label."""
    coverage_features = [
        "prior_categories",
        "prior_cities",
        "prior_avg_stars",
        "prior_review_length_mean",
        "prior_unique_business_count",
    ]
    if "prior_primary_category_entropy" in warmup_df.columns:
        coverage_features.append("prior_primary_category_entropy")
    summary = feature_coverage_frame(
        warmup_df,
        "cohort_label",
        coverage_features,
        subtrack="D2",
    )
    if not summary.empty:
        summary = summary.rename(columns={"cohort_label": "segment_label"})
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 6: User Warm-Up Profile")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(args.config)
    paths = resolve_paths(config)
    ensure_output_dirs(paths)

    cohort_pq = str(paths.tables_dir / "track_d_s5_user_cold_start_cohort.parquet").replace("\\", "/")
    rf_pq = str(paths.review_fact_path).replace("\\", "/")

    con = connect_duckdb(config)
    try:
        warmup_df = build_user_warmup_profile_sql(con, cohort_pq, rf_pq)
    finally:
        con.close()
    coverage_df = summarize_feature_coverage(warmup_df)

    warmup_out = paths.tables_dir / "track_d_s6_user_warmup_profile.parquet"
    warmup_df.to_parquet(warmup_out, index=False)
    logger.info("Wrote %s (%d rows)", warmup_out, len(warmup_df))

    coverage_out = paths.tables_dir / "track_d_s6_user_feature_coverage.parquet"
    coverage_df.to_parquet(coverage_out, index=False)
    logger.info("Wrote %s (%d rows)", coverage_out, len(coverage_df))
    logger.info("Stage 6 complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    main()
