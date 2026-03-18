"""Stage 8: Track D leakage check with hard-gate behavior."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import duckdb
import pandas as pd

from src.common.config import load_config
from src.eda.track_d.common import TrackDPaths, ensure_output_dirs, list_track_d_artifacts, read_text, resolve_paths

logger = logging.getLogger(__name__)

BANNED_OUTPUT_COLUMNS = {
    "stars",
    "review_count",
    "average_stars",
    "fans",
    "elite",
    "is_open",
    "text",
    "review_text",
    "raw_text",
}


def _record(finding_name: str, category: str, status: str, detail: str, artifact_path: str) -> dict[str, str]:
    return {
        "finding_name": finding_name,
        "category": category,
        "status": status,
        "detail": detail,
        "artifact_path": artifact_path,
    }


def _describe_parquet_columns(con: duckdb.DuckDBPyConnection, parquet_path: Path) -> list[str]:
    return [
        str(row[0]).lower()
        for row in con.execute("DESCRIBE SELECT * FROM read_parquet(?)", [str(parquet_path)]).fetchall()
    ]


def _check_required_artifacts(paths: TrackDPaths) -> list[dict[str, str]]:
    required = [
        paths.tables_dir / "track_d_s2_business_cold_start_cohort.parquet",
        paths.tables_dir / "track_d_s3_business_early_signals.parquet",
        paths.tables_dir / "track_d_s4_popularity_baseline_asof.parquet",
        paths.tables_dir / "track_d_s5_user_cold_start_cohort.parquet",
        paths.tables_dir / "track_d_s6_user_warmup_profile.parquet",
        paths.tables_dir / "track_d_s7_eval_cohorts.parquet",
        paths.tables_dir / "track_d_s7_eval_candidate_members.parquet",
    ]
    findings: list[dict[str, str]] = []
    for artifact in required:
        findings.append(
            _record(
                f"artifact_presence::{artifact.name}",
                "artifact_presence",
                "PASS" if artifact.is_file() else "FAIL",
                "Required artifact is present." if artifact.is_file() else "Required artifact is missing.",
                str(artifact),
            )
        )
    return findings


def _check_parquet_schemas(con: duckdb.DuckDBPyConnection, paths: TrackDPaths) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for artifact in sorted(paths.tables_dir.glob("track_d_*.parquet")):
        columns = set(_describe_parquet_columns(con, artifact))
        bad_cols = sorted(columns & BANNED_OUTPUT_COLUMNS)
        findings.append(
            _record(
                f"schema::{artifact.name}",
                "schema",
                "FAIL" if bad_cols else "PASS",
                f"Found banned output columns: {', '.join(bad_cols)}" if bad_cols else "No banned output columns found.",
                str(artifact),
            )
        )
    return findings


def _check_source_paths(paths: TrackDPaths, banned_fields: list[str]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for source_path in sorted(Path(__file__).parent.glob("*.py")):
        contents = read_text(source_path)
        for banned_field in banned_fields:
            status = "FAIL" if banned_field in contents else "PASS"
            detail = f"Found banned field reference: {banned_field}" if status == "FAIL" else f"No direct reference to {banned_field}"
            findings.append(
                _record(
                    f"source::{source_path.name}::{banned_field}",
                    "source_scan",
                    status,
                    detail,
                    str(source_path),
                )
            )

        if "yelp_academic_dataset_" in contents:
            findings.append(
                _record(
                    f"source::{source_path.name}::raw_json_read",
                    "source_scan",
                    "FAIL",
                    "Track D source reads raw JSON directly instead of curated artifacts.",
                    str(source_path),
                )
            )
    return findings


def _check_candidate_contamination(con: duckdb.DuckDBPyConnection, paths: TrackDPaths) -> list[dict[str, str]]:
    members_path = paths.tables_dir / "track_d_s7_eval_candidate_members.parquet"
    if not members_path.is_file():
        return []

    columns = _describe_parquet_columns(con, members_path)
    if "was_seen_previously" not in columns:
        return [
            _record(
                "candidate_contamination::missing_flag",
                "temporal_integrity",
                "FAIL",
                "Candidate member artifact is missing was_seen_previously audit flag.",
                str(members_path),
            )
        ]

    seen_count = con.execute(
        """
        SELECT COUNT(*)
        FROM read_parquet(?)
        WHERE COALESCE(was_seen_previously, FALSE)
        """,
        [str(members_path)],
    ).fetchone()[0]
    return [
        _record(
            "candidate_contamination::seen_candidates",
            "temporal_integrity",
            "FAIL" if int(seen_count) > 0 else "PASS",
            f"Previously seen candidate rows={int(seen_count)}",
            str(members_path),
        )
    ]


def _write_log(report_df: pd.DataFrame, log_path: Path) -> None:
    lines = ["Track D Stage 8 Leakage Check", ""]
    for row in report_df.itertuples(index=False):
        lines.append(f"[{row.status}] {row.category} {row.finding_name} :: {row.detail}")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def maybe_raise_on_failures(report_df: pd.DataFrame, hard_gate: bool = True) -> None:
    """Raise a blocking error when failures exist and the gate is enabled."""
    failures = report_df.loc[report_df["status"] == "FAIL"]
    if not failures.empty and hard_gate:
        failure_names = ", ".join(sorted(failures["finding_name"].tolist()))
        raise RuntimeError(
            f"Track D leakage check FAILED on: {failure_names}. Fix upstream stages before proceeding to summary."
        )


def run(config: dict[str, object]) -> pd.DataFrame:
    paths = resolve_paths(config)  # type: ignore[arg-type]
    ensure_output_dirs(paths)
    banned_fields = list(config.get("leakage", {}).get("banned_fields", []))  # type: ignore[union-attr]

    findings = _check_required_artifacts(paths)
    con = duckdb.connect()
    try:
        findings.extend(_check_parquet_schemas(con, paths))
        findings.extend(_check_candidate_contamination(con, paths))
    finally:
        con.close()

    findings.extend(_check_source_paths(paths, [str(value) for value in banned_fields]))
    report_df = pd.DataFrame(findings)

    report_out = paths.tables_dir / "track_d_s8_leakage_report.parquet"
    report_df.to_parquet(report_out, index=False)
    logger.info("Wrote %s (%d rows)", report_out, len(report_df))

    log_out = paths.logs_dir / "track_d_s8_leakage_check.log"
    _write_log(report_df, log_out)
    logger.info("Wrote %s", log_out)

    maybe_raise_on_failures(
        report_df,
        bool(config.get("leakage", {}).get("hard_gate", True)),  # type: ignore[union-attr]
    )
    return report_df


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 8: Leakage Check")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(args.config)
    run(config)
    logger.info("Stage 8 complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    main()
