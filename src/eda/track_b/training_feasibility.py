"""Stage 6: Pairwise and listwise training-feasibility checks for Track B."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from src.common.config import load_config
from src.common.db import connect_duckdb
from src.eda.track_b.common import TrackBPaths, ensure_output_dirs, resolve_paths

logger = logging.getLogger(__name__)


def _load_stage4_labels(
    con: duckdb.DuckDBPyConnection,
    label_candidates_path: Path,
) -> None:
    """Create a temp view over Stage 4 label candidates."""
    if not label_candidates_path.is_file():
        raise FileNotFoundError(
            f"Missing Stage 4 label candidates: {label_candidates_path}"
        )

    pq_str = str(label_candidates_path).replace("\\", "/")
    con.execute(
        f"""
        CREATE OR REPLACE TEMP VIEW track_b_label_candidates AS
        SELECT *
        FROM read_parquet('{pq_str}')
        """
    )


def _compute_group_level_stats(
    con: duckdb.DuckDBPyConnection,
) -> pd.DataFrame:
    """Compute group-level raw, tied, and valid pair counts."""
    return con.execute(
        """
        WITH tie_counts AS (
            SELECT
                group_type,
                group_id,
                age_bucket,
                SUM(value_count * (value_count - 1) / 2) AS tied_pairs
            FROM (
                SELECT
                    group_type,
                    group_id,
                    age_bucket,
                    useful,
                    COUNT(*) AS value_count
                FROM track_b_label_candidates
                GROUP BY group_type, group_id, age_bucket, useful
            )
            GROUP BY group_type, group_id, age_bucket
        )
        SELECT
            labels.group_type,
            labels.group_id,
            labels.age_bucket,
            COUNT(*) AS group_size,
            COUNT(*) * (COUNT(*) - 1) / 2 AS raw_pairs,
            COALESCE(tie_counts.tied_pairs, 0) AS tied_pairs,
            COUNT(*) * (COUNT(*) - 1) / 2 - COALESCE(tie_counts.tied_pairs, 0)
                AS valid_pairs,
            COUNT(DISTINCT useful) AS distinct_useful_count,
            COUNT(DISTINCT binary_useful) AS binary_class_count,
            COUNT(DISTINCT top_decile_label) AS top_decile_class_count,
            COUNT(DISTINCT graded_useful) AS graded_class_count,
            MAX(within_group_percentile) - MIN(within_group_percentile)
                AS percentile_range
        FROM track_b_label_candidates AS labels
        LEFT JOIN tie_counts
          ON labels.group_type = tie_counts.group_type
         AND labels.group_id = tie_counts.group_id
         AND labels.age_bucket = tie_counts.age_bucket
        GROUP BY
            labels.group_type,
            labels.group_id,
            labels.age_bucket,
            tie_counts.tied_pairs
        ORDER BY labels.group_type, labels.age_bucket, labels.group_id
        """
    ).fetchdf()


def _load_stage3_group_counts(paths: TrackBPaths) -> pd.DataFrame:
    """Load Stage 3 qualifying-group counts for coverage comparisons."""
    frames: list[pd.DataFrame] = []
    artifact_specs = [
        ("business", paths.tables_dir / "track_b_s3_group_sizes_by_business_age.parquet"),
        ("category", paths.tables_dir / "track_b_s3_group_sizes_by_category_age.parquet"),
    ]
    for group_type, artifact_path in artifact_specs:
        if not artifact_path.is_file():
            continue
        df = pd.read_parquet(artifact_path)
        if "qualifies" not in df.columns:
            continue
        filtered = (
            df.loc[df["qualifies"]]
            .groupby("age_bucket", as_index=False)
            .size()
            .rename(columns={"size": "qualifying_groups_available"})
        )
        filtered["group_type"] = group_type
        frames.append(filtered)

    if not frames:
        return pd.DataFrame(
            columns=["group_type", "age_bucket", "qualifying_groups_available"]
        )
    return pd.concat(frames, ignore_index=True)


def _aggregate_pairwise_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate pairwise metrics from group-level stats."""
    return (
        df.groupby(["group_type", "age_bucket"], as_index=False)
        .agg(
            represented_groups=("group_id", "count"),
            raw_pairs=("raw_pairs", "sum"),
            tied_pairs=("tied_pairs", "sum"),
            valid_pairs=("valid_pairs", "sum"),
            avg_raw_pairs=("raw_pairs", "mean"),
            avg_valid_pairs=("valid_pairs", "mean"),
            pct_groups_with_valid_pairs=("valid_pairs", lambda s: float((s > 0).mean())),
        )
    )


def _aggregate_listwise_stats(
    df: pd.DataFrame,
    stage3_group_counts: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate listwise metrics from group-level stats."""
    stats = (
        df.groupby(["group_type", "age_bucket"], as_index=False)
        .agg(
            represented_groups=("group_id", "count"),
            total_reviews=("group_size", "sum"),
            avg_list_length=("group_size", "mean"),
            median_list_length=("group_size", "median"),
            pct_non_degenerate_useful=("distinct_useful_count", lambda s: float((s > 1).mean())),
            pct_non_degenerate_binary=("binary_class_count", lambda s: float((s > 1).mean())),
            pct_non_degenerate_top_decile=("top_decile_class_count", lambda s: float((s > 1).mean())),
            pct_non_degenerate_graded=("graded_class_count", lambda s: float((s > 1).mean())),
        )
    )
    stats = stats.merge(
        stage3_group_counts,
        on=["group_type", "age_bucket"],
        how="left",
    )
    stats["qualifying_groups_available"] = stats[
        "qualifying_groups_available"
    ].fillna(stats["represented_groups"])
    stats["represented_group_fraction"] = (
        stats["represented_groups"] / stats["qualifying_groups_available"]
    )
    return stats


def build_pairwise_stats(
    group_level: pd.DataFrame,
    config: dict[str, Any],
) -> pd.DataFrame:
    """Aggregate pairwise feasibility metrics by group type and age bucket."""
    detailed = _aggregate_pairwise_stats(group_level)
    overall_input = group_level.copy()
    overall_input["age_bucket"] = "ALL"
    overall = _aggregate_pairwise_stats(overall_input)
    stats = pd.concat([detailed, overall], ignore_index=True)
    min_groups = int(config.get("quality", {}).get("min_qualifying_groups", 1000))
    stats["meets_min_group_gate"] = stats["represented_groups"] >= min_groups
    stats["feasibility_signoff"] = stats["meets_min_group_gate"] & (stats["valid_pairs"] > 0)
    stats["valid_pair_fraction"] = stats["valid_pairs"] / stats["raw_pairs"].where(
        stats["raw_pairs"] > 0, 1
    )
    return stats.sort_values(["group_type", "age_bucket"]).reset_index(drop=True)


def build_listwise_stats(
    group_level: pd.DataFrame,
    stage3_group_counts: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate listwise training statistics and label degeneracy rates."""
    detailed = _aggregate_listwise_stats(group_level, stage3_group_counts)
    overall_input = group_level.copy()
    overall_input["age_bucket"] = "ALL"
    overall_stage3 = (
        stage3_group_counts.groupby("group_type", as_index=False)[
            "qualifying_groups_available"
        ]
        .sum()
    )
    overall_stage3["age_bucket"] = "ALL"
    overall = _aggregate_listwise_stats(overall_input, overall_stage3)
    stats = pd.concat([detailed, overall], ignore_index=True)
    return stats.sort_values(["group_type", "age_bucket"]).reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 6: Training Feasibility")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(args.config)

    paths = resolve_paths(config)
    ensure_output_dirs(paths)

    label_candidates_path = paths.tables_dir / "track_b_s4_label_candidates.parquet"
    con = connect_duckdb(config)
    try:
        _load_stage4_labels(con, label_candidates_path)
        group_level = _compute_group_level_stats(con)
    finally:
        con.close()

    stage3_group_counts = _load_stage3_group_counts(paths)
    pairwise_stats = build_pairwise_stats(group_level, config)
    listwise_stats = build_listwise_stats(group_level, stage3_group_counts)

    pairwise_out = paths.tables_dir / "track_b_s6_pairwise_stats.parquet"
    pairwise_stats.to_parquet(pairwise_out, index=False)
    logger.info("Wrote %s (%d rows)", pairwise_out, len(pairwise_stats))

    listwise_out = paths.tables_dir / "track_b_s6_listwise_stats.parquet"
    listwise_stats.to_parquet(listwise_out, index=False)
    logger.info("Wrote %s (%d rows)", listwise_out, len(listwise_stats))
    logger.info("Stage 6 complete.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    main()
