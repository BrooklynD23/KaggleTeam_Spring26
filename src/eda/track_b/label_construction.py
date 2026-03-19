"""Stage 4: Snapshot-safe label construction for Track B."""

from __future__ import annotations

import argparse
import logging

import duckdb
import pandas as pd

from src.common.config import load_config
from src.common.db import connect_duckdb
from src.eda.track_b.common import (
    TrackBPaths,
    create_snapshot_view,
    ensure_output_dirs,
    resolve_paths,
)

logger = logging.getLogger(__name__)


def _read_group_summary(con: duckdb.DuckDBPyConnection, path: str, key_column: str) -> None:
    """Materialize qualifying groups from a Stage 3 artifact."""
    pq_str = str(path).replace("\\", "/")
    con.execute(
        f"""
        CREATE OR REPLACE TEMP VIEW qualifying_{key_column}_groups AS
        SELECT
            group_id AS {key_column},
            age_bucket,
            group_type,
            qualifies
        FROM read_parquet('{pq_str}')
        WHERE qualifies
        """
    )


def _graded_case_expression() -> str:
    """Return the default graded-useful label scheme."""
    return """
        CASE
            WHEN useful = 0 THEN '0'
            WHEN useful = 1 THEN '1'
            WHEN useful BETWEEN 2 AND 4 THEN '2-4'
            WHEN useful BETWEEN 5 AND 9 THEN '5-9'
            ELSE '10+'
        END
    """


def build_label_candidates(
    con: duckdb.DuckDBPyConnection,
    paths: TrackBPaths,
) -> pd.DataFrame:
    """Create the Stage 4 label candidate table."""
    business_groups_path = paths.tables_dir / "track_b_s3_group_sizes_by_business_age.parquet"
    category_groups_path = paths.tables_dir / "track_b_s3_group_sizes_by_category_age.parquet"
    if not business_groups_path.is_file():
        raise FileNotFoundError(f"Missing Stage 3 business groups: {business_groups_path}")
    if not category_groups_path.is_file():
        raise FileNotFoundError(f"Missing Stage 3 category groups: {category_groups_path}")

    _read_group_summary(con, str(business_groups_path), "business_id")
    _read_group_summary(con, str(category_groups_path), "primary_category")

    graded_case = _graded_case_expression()
    return con.execute(
        f"""
        WITH assigned_groups AS (
            SELECT
                snapshot.review_id,
                snapshot.useful,
                snapshot.age_bucket,
                CASE
                    WHEN business_groups.business_id IS NOT NULL THEN 'business'
                    ELSE 'category'
                END AS group_type,
                CASE
                    WHEN business_groups.business_id IS NOT NULL THEN snapshot.business_id
                    ELSE snapshot.primary_category
                END AS group_id
            FROM review_usefulness_snapshot AS snapshot
            LEFT JOIN qualifying_business_id_groups AS business_groups
                ON snapshot.business_id = business_groups.business_id
               AND snapshot.age_bucket = business_groups.age_bucket
            LEFT JOIN qualifying_primary_category_groups AS category_groups
                ON snapshot.primary_category = category_groups.primary_category
               AND snapshot.age_bucket = category_groups.age_bucket
            WHERE business_groups.business_id IS NOT NULL
               OR category_groups.primary_category IS NOT NULL
        )
        SELECT
            review_id,
            group_type,
            group_id,
            age_bucket,
            useful,
            CASE WHEN useful > 0 THEN 1 ELSE 0 END AS binary_useful,
            {graded_case} AS graded_useful,
            ROUND(
                CUME_DIST() OVER (
                    PARTITION BY group_type, group_id, age_bucket
                    ORDER BY useful
                ),
                6
            ) AS within_group_percentile,
            CASE
                WHEN CUME_DIST() OVER (
                    PARTITION BY group_type, group_id, age_bucket
                    ORDER BY useful
                ) >= 0.9
                THEN 1
                ELSE 0
            END AS top_decile_label
        FROM assigned_groups
        ORDER BY group_type, group_id, age_bucket, review_id
        """
    ).fetchdf()


def _compute_group_tie_rate(group_df: pd.DataFrame, col: str) -> float:
    """Fraction of within-group pairs that are tied on column ``col``."""
    n = len(group_df)
    if n < 2:
        return 1.0
    total_pairs = n * (n - 1) / 2
    tied = sum(c * (c - 1) / 2 for c in group_df[col].value_counts())
    return tied / total_pairs if total_pairs > 0 else 1.0


def build_label_scheme_summary(
    candidates: pd.DataFrame,
    config: dict[str, object],
) -> pd.DataFrame:
    """Rank Stage 4 label schemes by measured criteria; config only as tie-break.

    Priority order (descending importance):
    1. passes_balance_gate  — max_class_fraction < 0.95
    2. non_degenerate_fraction — fraction of groups with > 1 distinct label value
    3. mean_tie_rate (asc)  — lower tied-pair fraction is better for ranking
    4. max_class_fraction (asc) — more balanced is better
    5. config rank           — configured primary/secondary as final tie-break
    """
    if candidates.empty:
        return pd.DataFrame(
            columns=[
                "scheme_name", "scheme_type", "labeled_reviews",
                "distinct_label_count", "max_class_fraction", "positive_fraction",
                "non_degenerate_fraction", "mean_tie_rate",
                "passes_balance_gate", "recommended_primary", "recommended_secondary",
            ]
        )

    label_cfg = config["labels"]
    total_rows = len(candidates)
    group_keys = ["group_type", "group_id", "age_bucket"]

    scheme_columns: dict[str, str] = {
        "binary_useful": "binary",
        "graded_useful": "categorical",
        "top_decile_label": "binary",
        "within_group_percentile": "continuous",
    }

    summary_rows: list[dict[str, object]] = []
    for column, scheme_type in scheme_columns.items():
        counts = candidates[column].value_counts(normalize=False, dropna=False)
        max_class_fraction = (
            round(float(counts.max() / total_rows), 6) if total_rows > 0 else 1.0
        )
        positive_fraction = (
            round(float(candidates[column].mean()), 6)
            if scheme_type == "binary" and total_rows > 0
            else 0.0
        )

        group_distinct = candidates.groupby(group_keys)[column].nunique()
        non_degenerate_fraction = (
            round(float((group_distinct > 1).mean()), 6)
            if len(group_distinct) > 0
            else 0.0
        )

        col_name = column
        group_tie_rates = candidates.groupby(group_keys).apply(
            lambda g: _compute_group_tie_rate(g, col_name)
        )
        mean_tie_rate = (
            round(float(group_tie_rates.mean()), 6) if len(group_tie_rates) > 0 else 1.0
        )

        passes_balance_gate = bool(max_class_fraction < 0.95)

        config_rank = (
            0
            if column == label_cfg["primary"]
            else 1
            if column == label_cfg["secondary"]
            else 2
        )

        summary_rows.append(
            {
                "scheme_name": column,
                "scheme_type": scheme_type,
                "labeled_reviews": int(total_rows),
                "distinct_label_count": int(counts.shape[0]),
                "max_class_fraction": max_class_fraction,
                "positive_fraction": positive_fraction,
                "non_degenerate_fraction": non_degenerate_fraction,
                "mean_tie_rate": mean_tie_rate,
                "passes_balance_gate": passes_balance_gate,
                "_config_rank": config_rank,
            }
        )

    summary_df = pd.DataFrame(summary_rows)
    summary_df = summary_df.sort_values(
        [
            "passes_balance_gate",
            "non_degenerate_fraction",
            "mean_tie_rate",
            "max_class_fraction",
            "_config_rank",
        ],
        ascending=[False, False, True, True, True],
    ).reset_index(drop=True)

    summary_df["recommended_primary"] = False
    summary_df["recommended_secondary"] = False
    if len(summary_df) >= 1:
        summary_df.loc[0, "recommended_primary"] = True
    if len(summary_df) >= 2:
        summary_df.loc[1, "recommended_secondary"] = True

    return summary_df.drop(columns=["_config_rank"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 4: Label Construction")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(args.config)

    paths = resolve_paths(config)
    ensure_output_dirs(paths)

    # Enforce Stage 3 gate: abort early if no buckets are recommended
    recommended_buckets_path = paths.tables_dir / "track_b_s3_recommended_age_buckets.parquet"
    if recommended_buckets_path.is_file():
        rec_df = pd.read_parquet(recommended_buckets_path)
        if "recommended_for_modeling" in rec_df.columns:
            recommended_buckets = set(
                rec_df.loc[rec_df["recommended_for_modeling"], "age_bucket"]
            )
            if not recommended_buckets:
                raise RuntimeError(
                    "Stage 3 filtered all age buckets below the qualifying-groups gate. "
                    "No age buckets are recommended for modeling. "
                    "Inspect 'track_b_s3_recommended_age_buckets.parquet' for details."
                )

    con = connect_duckdb(config)
    try:
        create_snapshot_view(con, config, paths)
        candidates = build_label_candidates(con, paths)
    finally:
        con.close()

    summary = build_label_scheme_summary(candidates, config)

    candidates_out = paths.tables_dir / "track_b_s4_label_candidates.parquet"
    candidates.to_parquet(candidates_out, index=False)
    logger.info("Wrote %s (%d rows)", candidates_out, len(candidates))

    summary_out = paths.tables_dir / "track_b_s4_label_scheme_summary.parquet"
    summary.to_parquet(summary_out, index=False)
    logger.info("Wrote %s (%d rows)", summary_out, len(summary))
    logger.info("Stage 4 complete.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    main()
