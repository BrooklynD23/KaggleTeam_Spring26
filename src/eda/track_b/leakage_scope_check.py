"""Stage 7: Leakage and scope validation for Track B."""

from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path

import duckdb
import pandas as pd

from src.common.config import load_config
from src.common.db import connect_duckdb
from src.eda.track_b.common import (
    TEMPORAL_CLAIM_PATTERNS,
    TEXT_ARTIFACT_SUFFIXES,
    TrackBPaths,
    ensure_output_dirs,
    list_track_b_artifacts,
    load_snapshot_metadata,
    resolve_paths,
)

logger = logging.getLogger(__name__)

BANNED_SIMULTANEOUS_COLUMNS = {"funny", "cool"}
# Case-insensitive column name patterns for raw review text (checked via lower())
BANNED_RAW_TEXT_COLUMNS = {"text", "review_text", "raw_text", "review_body"}


def _record(
    finding_name: str,
    category: str,
    status: str,
    detail: str,
    artifact_path: str,
) -> dict[str, str]:
    return {
        "finding_name": finding_name,
        "category": category,
        "status": status,
        "detail": detail,
        "artifact_path": artifact_path,
    }


def _describe_parquet_columns(
    con: duckdb.DuckDBPyConnection,
    parquet_path: Path,
) -> list[str]:
    """Return parquet column names via DuckDB schema introspection."""
    pq_str = str(parquet_path).replace("\\", "/")
    return [
        str(row[0])
        for row in con.execute(
            f"DESCRIBE SELECT * FROM read_parquet('{pq_str}')"
        ).fetchall()
    ]


def _check_parquet_schemas(
    con: duckdb.DuckDBPyConnection,
    paths: TrackBPaths,
) -> list[dict[str, str]]:
    """Check all track_b_*.parquet artifacts for banned columns and raw text.

    Required artifacts (s4, s5) produce FAIL if missing.  All discovered
    track_b_*.parquet files are scanned for banned simultaneous-observation
    columns and raw-text column names.
    """
    findings: list[dict[str, str]] = []
    required_artifacts = {
        paths.tables_dir / "track_b_s4_label_candidates.parquet",
        paths.tables_dir / "track_b_s5_feature_correlates.parquet",
    }
    # Discover all current track_b_*.parquet artifacts
    discovered_artifacts = set(paths.tables_dir.glob("track_b_*.parquet"))
    all_artifacts = sorted(required_artifacts | discovered_artifacts)

    for parquet_path in all_artifacts:
        if not parquet_path.is_file():
            if parquet_path in required_artifacts:
                findings.append(
                    _record(
                        finding_name=f"missing_artifact::{parquet_path.name}",
                        category="artifact_presence",
                        status="FAIL",
                        detail="Required Track B artifact is missing.",
                        artifact_path=str(parquet_path),
                    )
                )
            continue

        columns = {column.lower() for column in _describe_parquet_columns(con, parquet_path)}
        banned_columns = sorted(columns & BANNED_SIMULTANEOUS_COLUMNS)
        if banned_columns:
            findings.append(
                _record(
                    finding_name=f"banned_columns::{parquet_path.name}",
                    category="banned_columns",
                    status="FAIL",
                    detail="Found banned simultaneous-observation columns: "
                    + ", ".join(banned_columns),
                    artifact_path=str(parquet_path),
                )
            )
        else:
            findings.append(
                _record(
                    finding_name=f"banned_columns::{parquet_path.name}",
                    category="banned_columns",
                    status="PASS",
                    detail="No banned simultaneous-observation columns found.",
                    artifact_path=str(parquet_path),
                )
            )

        raw_text_columns = sorted(columns & BANNED_RAW_TEXT_COLUMNS)
        if raw_text_columns:
            findings.append(
                _record(
                    finding_name=f"raw_text_columns::{parquet_path.name}",
                    category="raw_text",
                    status="FAIL",
                    detail="Found raw text columns: " + ", ".join(raw_text_columns),
                    artifact_path=str(parquet_path),
                )
            )
        else:
            findings.append(
                _record(
                    finding_name=f"raw_text_columns::{parquet_path.name}",
                    category="raw_text",
                    status="PASS",
                    detail="No raw review text columns found in parquet schema.",
                    artifact_path=str(parquet_path),
                )
            )

    return findings


def _check_age_scope(
    con: duckdb.DuckDBPyConnection,
    paths: TrackBPaths,
) -> list[dict[str, str]]:
    """Verify labels remain constrained to a single age bucket."""
    findings: list[dict[str, str]] = []
    label_candidates_path = paths.tables_dir / "track_b_s4_label_candidates.parquet"
    if not label_candidates_path.is_file():
        return [
            _record(
                finding_name="age_scope::missing_label_candidates",
                category="age_scope",
                status="FAIL",
                detail="Stage 4 label candidates are required for age-scope validation.",
                artifact_path=str(label_candidates_path),
            )
        ]

    pq_str = str(label_candidates_path).replace("\\", "/")
    row = con.execute(
        f"""
        SELECT
            COUNT(*) AS row_count,
            COUNT(DISTINCT review_id) AS unique_review_ids,
            COUNT(*) FILTER (WHERE age_bucket IS NULL) AS null_age_bucket_rows
        FROM read_parquet('{pq_str}')
        """
    ).fetchone()
    if row is None:
        raise RuntimeError("Age-scope validation query returned no rows")

    duplicate_rows = int(row[0]) - int(row[1])
    null_age_rows = int(row[2])
    if duplicate_rows > 0 or null_age_rows > 0:
        findings.append(
            _record(
                finding_name="age_scope::label_rows",
                category="age_scope",
                status="FAIL",
                detail=(
                    f"duplicate_review_rows={duplicate_rows}, "
                    f"null_age_bucket_rows={null_age_rows}"
                ),
                artifact_path=str(label_candidates_path),
            )
        )
    else:
        findings.append(
            _record(
                finding_name="age_scope::label_rows",
                category="age_scope",
                status="PASS",
                detail="Each label row carries exactly one non-null age bucket.",
                artifact_path=str(label_candidates_path),
            )
        )

    source_path = Path(__file__).with_name("label_construction.py")
    source_text = source_path.read_text(encoding="utf-8")
    required_snippets = [
        "PARTITION BY group_type, group_id, age_bucket",
        "snapshot.age_bucket = business_groups.age_bucket",
        "snapshot.age_bucket = category_groups.age_bucket",
    ]
    missing_snippets = [snippet for snippet in required_snippets if snippet not in source_text]
    if missing_snippets:
        findings.append(
            _record(
                finding_name="age_scope::code_path",
                category="age_scope",
                status="FAIL",
                detail="Missing age-control code markers: " + "; ".join(missing_snippets),
                artifact_path=str(source_path),
            )
        )
    else:
        findings.append(
            _record(
                finding_name="age_scope::code_path",
                category="age_scope",
                status="PASS",
                detail="Label-construction code paths keep partitions and joins inside age buckets.",
                artifact_path=str(source_path),
            )
        )

    return findings


def _check_temporal_claims(paths: TrackBPaths) -> list[dict[str, str]]:
    """Scan Track B text artifacts for unsupported temporal claims."""
    findings: list[dict[str, str]] = []
    target_artifacts = [
        artifact
        for artifact in list_track_b_artifacts(paths)
        if artifact.suffix.lower() in TEXT_ARTIFACT_SUFFIXES
        and not artifact.name.startswith("track_b_s7_")
    ]
    if not target_artifacts:
        return [
            _record(
                finding_name="temporal_claims::scan_scope",
                category="temporal_claims",
                status="PASS",
                detail="No text artifacts were present to scan before Stage 7 output generation.",
                artifact_path="",
            )
        ]

    found_match = False
    for artifact in target_artifacts:
        try:
            contents = artifact.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            contents = artifact.read_text(encoding="utf-8", errors="ignore")

        for finding_name, pattern in TEMPORAL_CLAIM_PATTERNS.items():
            match = re.search(pattern, contents, re.IGNORECASE)
            if match:
                found_match = True
                findings.append(
                    _record(
                        finding_name=f"temporal_claim::{finding_name}",
                        category="temporal_claims",
                        status="FAIL",
                        detail=f"Matched prohibited pattern '{finding_name}'.",
                        artifact_path=str(artifact),
                    )
                )

    if not found_match:
        findings.append(
            _record(
                finding_name="temporal_claims::scan_scope",
                category="temporal_claims",
                status="PASS",
                detail="No prohibited temporal claims found in Track B text artifacts.",
                artifact_path="",
            )
        )
    return findings


def _write_log(
    report_df: pd.DataFrame,
    log_path: Path,
    metadata: dict[str, str],
) -> None:
    """Write the Stage 7 log file with compact findings."""
    lines = [
        "Track B Stage 7 Leakage / Scope Check",
        f"snapshot_reference_date={metadata['snapshot_reference_date']}",
        f"dataset_release_tag={metadata['dataset_release_tag']}",
        "",
    ]
    for row in report_df.itertuples(index=False):
        lines.append(
            f"[{row.status}] {row.category} {row.finding_name} :: "
            f"{row.artifact_path} :: {row.detail}"
        )
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 7: Leakage and Scope Check")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(args.config)

    paths = resolve_paths(config)
    ensure_output_dirs(paths)
    metadata = load_snapshot_metadata(paths)

    con = connect_duckdb(config)
    try:
        findings = []
        findings.extend(_check_parquet_schemas(con, paths))
        findings.extend(_check_age_scope(con, paths))
        findings.extend(_check_temporal_claims(paths))
    finally:
        con.close()

    report_df = pd.DataFrame(findings)
    report_out = paths.tables_dir / "track_b_s7_leakage_scope_report.parquet"
    report_df.to_parquet(report_out, index=False)
    logger.info("Wrote %s (%d rows)", report_out, len(report_df))

    log_out = paths.logs_dir / "track_b_s7_leakage_scope_check.log"
    _write_log(report_df, log_out, metadata)
    logger.info("Wrote %s", log_out)

    failures = report_df.loc[report_df["status"] == "FAIL"]
    if not failures.empty:
        failure_names = ", ".join(sorted(failures["finding_name"].tolist()))
        raise RuntimeError(f"Track B Stage 7 failed: {failure_names}")

    logger.info("Stage 7 complete.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    main()
