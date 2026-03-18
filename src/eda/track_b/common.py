"""Shared helpers for Track B stage scripts."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import duckdb

logger = logging.getLogger(__name__)

REQUIRED_METADATA_FIELDS = ("snapshot_reference_date", "dataset_release_tag")
TEMPORAL_CLAIM_PATTERNS = {
    "future_prediction_claim": r"predict\s+future",
    "vote_growth_claim": r"vote\s+growth",
    "future_usefulness_claim": r"future\s+useful(ness)?",
    "temporal_target_claim": r"temporal\s+target",
    "vote_trend_claim": r"vote.*(trajectory|trend|accumulate)",
    "usefulness_at_time_claim": r"usefulness.at.time",
    "vote_reconstruction_claim": r"reconstruct.*(vote|useful)",
}
TEXT_ARTIFACT_SUFFIXES = {".md", ".log", ".txt", ".json", ".csv"}


@dataclass(frozen=True)
class TrackBPaths:
    """Resolved filesystem locations used by Track B."""

    curated_dir: Path
    tables_dir: Path
    figures_dir: Path
    logs_dir: Path
    review_fact_track_b_path: Path
    snapshot_metadata_path: Path


def resolve_paths(config: dict[str, Any]) -> TrackBPaths:
    """Resolve configured Track B paths."""
    curated_dir = Path(config["paths"]["curated_dir"])
    tables_dir = Path(config["paths"]["tables_dir"])
    figures_dir = Path(config["paths"]["figures_dir"])
    logs_dir = Path(config["paths"]["logs_dir"])
    return TrackBPaths(
        curated_dir=curated_dir,
        tables_dir=tables_dir,
        figures_dir=figures_dir,
        logs_dir=logs_dir,
        review_fact_track_b_path=curated_dir / "review_fact_track_b.parquet",
        snapshot_metadata_path=curated_dir / "snapshot_metadata.json",
    )


def ensure_output_dirs(paths: TrackBPaths) -> None:
    """Create Track B output directories if needed."""
    paths.tables_dir.mkdir(parents=True, exist_ok=True)
    paths.figures_dir.mkdir(parents=True, exist_ok=True)
    paths.logs_dir.mkdir(parents=True, exist_ok=True)


def load_snapshot_metadata(paths: TrackBPaths) -> dict[str, str]:
    """Load and validate snapshot metadata."""
    if not paths.snapshot_metadata_path.is_file():
        raise FileNotFoundError(
            f"Missing snapshot metadata: {paths.snapshot_metadata_path}"
        )

    with open(paths.snapshot_metadata_path, "r", encoding="utf-8") as fh:
        metadata = json.load(fh)

    missing = [
        field for field in REQUIRED_METADATA_FIELDS if not metadata.get(field)
    ]
    if missing:
        raise ValueError(
            "snapshot_metadata.json is missing required fields: "
            + ", ".join(sorted(missing))
        )

    try:
        date.fromisoformat(str(metadata["snapshot_reference_date"]))
    except ValueError as exc:
        raise ValueError(
            "snapshot_reference_date must be ISO-8601 formatted"
        ) from exc

    dataset_release_tag = str(metadata["dataset_release_tag"]).strip()
    if not dataset_release_tag:
        raise ValueError("dataset_release_tag must be a non-empty string")

    return {key: str(value) for key, value in metadata.items()}


def build_age_bucket_case(
    thresholds: list[int],
    labels: list[str],
    column_name: str = "review_age_days",
) -> str:
    """Build a SQL CASE expression for age buckets."""
    if len(labels) != len(thresholds) + 1:
        raise ValueError(
            "age bucket labels must be exactly one longer than thresholds"
        )

    lines = ["CASE"]
    for threshold, label in zip(thresholds, labels, strict=True):
        lines.append(f"    WHEN {column_name} <= {threshold} THEN '{label}'")
    lines.append(f"    ELSE '{labels[-1]}'")
    lines.append("END")
    return "\n".join(lines)


def create_snapshot_view(
    con: duckdb.DuckDBPyConnection,
    config: dict[str, Any],
    paths: TrackBPaths,
    view_name: str = "review_usefulness_snapshot",
) -> dict[str, str]:
    """Create an age-enriched Track B snapshot temp view from curated Parquet."""
    if not paths.review_fact_track_b_path.is_file():
        raise FileNotFoundError(
            f"Missing Track B curated input: {paths.review_fact_track_b_path}"
        )

    metadata = load_snapshot_metadata(paths)
    age_cfg = config["age_buckets"]
    age_case = build_age_bucket_case(
        thresholds=age_cfg["thresholds_days"],
        labels=age_cfg["labels"],
    )
    snapshot_date = metadata["snapshot_reference_date"]

    sql = f"""
        CREATE OR REPLACE TEMP VIEW {view_name} AS
        SELECT
            base.*,
            TRIM(SPLIT_PART(base.categories, ',', 1)) AS primary_category,
            {age_case} AS age_bucket,
            CASE
                WHEN base.elite IS NULL
                    OR TRIM(base.elite) = ''
                    OR LOWER(TRIM(base.elite)) = 'none'
                THEN 0
                ELSE 1
            END AS elite_flag
        FROM (
            SELECT
                review_id,
                user_id,
                business_id,
                review_stars,
                review_date,
                useful,
                text_char_count,
                text_word_count,
                city,
                state,
                categories,
                latitude,
                longitude,
                yelping_since,
                review_year,
                review_month,
                user_tenure_days,
                is_open,
                fans,
                elite,
                DATEDIFF('day', review_date, DATE '{snapshot_date}') AS review_age_days
            FROM read_parquet(?)
        ) AS base
    """
    con.execute(sql, [str(paths.review_fact_track_b_path)])
    logger.info(
        "Created temp view %s from %s",
        view_name,
        paths.review_fact_track_b_path,
    )
    return metadata


def list_track_b_artifacts(paths: TrackBPaths) -> list[Path]:
    """Return current Track B artifact paths in tables and logs."""
    artifacts = list(paths.tables_dir.glob("track_b_*")) + list(
        paths.logs_dir.glob("track_b_*")
    )
    return sorted(path for path in artifacts if path.is_file())
