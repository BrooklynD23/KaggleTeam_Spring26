"""Stage 6: Leakage Audit for Track A."""

import argparse
import logging
import re
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from src.common.artifacts import load_candidate_splits
from src.common.config import load_config

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
TRACK_A_DIR = PROJECT_ROOT / "src" / "eda" / "track_a"

# All directories reachable from Track A (excludes track_b and build artifacts)
TRACK_A_SCAN_DIRS = [
    PROJECT_ROOT / "src" / "eda" / "track_a",
    PROJECT_ROOT / "src" / "common",
    PROJECT_ROOT / "src" / "ingest",
    PROJECT_ROOT / "src" / "curate",
    PROJECT_ROOT / "src" / "validate",
]

BANNED_FEATURES = (
    "business.stars",
    "business.review_count",
    "business.is_open",
    "user.average_stars",
    "user.review_count",
    "user.fans",
    "user.elite",
)
FORBIDDEN_SOURCE = "review_fact_track_b"
FORBIDDEN_COLUMNS = {
    "stars",
    "review_count",
    "is_open",
    "average_stars",
    "fans",
    "elite",
    "text",
}
RAW_ENTITY_JOIN_PATTERN = re.compile(
    r"JOIN\s+(?:read_parquet\([^)]*(?:business|user)\.parquet\)|business\b|\"user\"\b)",
    re.IGNORECASE | re.MULTILINE,
)
SAME_DAY_HISTORY_PATTERN = re.compile(
    r"OVER\s*\([^\)]*ORDER\s+BY[^\)]*review_date[^\)]*,\s*review_id",
    re.IGNORECASE | re.DOTALL,
)


def _resolve_path(config: dict[str, Any], key: str) -> Path:
    path = Path(config["paths"][key])
    return path if path.is_absolute() else PROJECT_ROOT / path


def _schema_checks(
    con: duckdb.DuckDBPyConnection,
    review_fact_path: Path,
) -> list[dict[str, Any]]:
    schema = con.execute(
        "DESCRIBE SELECT * FROM read_parquet(?)",
        [str(review_fact_path)],
    ).fetchdf()
    columns = set(schema["column_name"].tolist())
    forbidden_present = sorted(columns & FORBIDDEN_COLUMNS)
    return [
        {
            "check_name": "curated_schema_banned_columns",
            "status": "FAIL" if forbidden_present else "PASS",
            "severity": "error" if forbidden_present else "info",
            "finding_count": len(forbidden_present),
            "detail": (
                "Unexpected columns present in review_fact: "
                + ", ".join(forbidden_present)
                if forbidden_present
                else "Track A-safe review_fact schema excludes banned snapshot and text columns."
            ),
            "source_path": str(review_fact_path),
        }
    ]


def _iter_scan_paths() -> list[Path]:
    """Yield all .py files reachable from Track A, excluding leakage_audit.py itself."""
    seen: set[Path] = set()
    paths: list[Path] = []
    for scan_dir in TRACK_A_SCAN_DIRS:
        if not scan_dir.is_dir():
            continue
        for path in sorted(scan_dir.rglob("*.py")):
            if path.name == "leakage_audit.py":
                continue
            if path in seen:
                continue
            seen.add(path)
            paths.append(path)
    return paths


def _scan_code_paths() -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for path in _iter_scan_paths():
        content = path.read_text(encoding="utf-8")
        banned_hits = [feature for feature in BANNED_FEATURES if feature in content]
        if FORBIDDEN_SOURCE in content:
            findings.append(
                {
                    "check_name": "forbidden_track_b_source_access",
                    "status": "FAIL",
                    "severity": "error",
                    "finding_count": 1,
                    "detail": "Found review_fact_track_b reference in Track A code.",
                    "source_path": str(path),
                }
            )

        if banned_hits:
            findings.append(
                {
                    "check_name": "banned_feature_reference",
                    "status": "FAIL",
                    "severity": "error",
                    "finding_count": len(banned_hits),
                    "detail": "Found banned feature references: " + ", ".join(banned_hits),
                    "source_path": str(path),
                }
            )

        if RAW_ENTITY_JOIN_PATTERN.search(content):
            findings.append(
                {
                    "check_name": "raw_entity_join_path",
                    "status": "FAIL",
                    "severity": "error",
                    "finding_count": 1,
                    "detail": "Found a direct join against raw business/user sources in Track A code.",
                    "source_path": str(path),
                }
            )

        if SAME_DAY_HISTORY_PATTERN.search(content):
            findings.append(
                {
                    "check_name": "same_day_ordering_surrogate",
                    "status": "FAIL",
                    "severity": "error",
                    "finding_count": 1,
                    "detail": (
                        "Found review_id as same-day tiebreaker inside a window OVER() clause, "
                        "which violates strictly earlier-date history semantics."
                    ),
                    "source_path": str(path),
                }
            )

    if findings:
        return findings

    return [
        {
            "check_name": "code_path_scan",
            "status": "PASS",
            "severity": "info",
            "finding_count": 0,
            "detail": (
                "No banned fields, review_fact_track_b access, raw entity joins, or "
                "same-day history window patterns found in Track A-reachable code."
            ),
            "source_path": str(PROJECT_ROOT / "src"),
        }
    ]


def _overlap_checks(
    con: duckdb.DuckDBPyConnection,
    review_fact_path: Path,
    t1: str,
    t2: str,
) -> list[dict[str, Any]]:
    query = """
        WITH split_reviews AS (
            SELECT
                user_id,
                business_id,
                CASE
                    WHEN review_date < CAST(? AS DATE) THEN 'train'
                    WHEN review_date < CAST(? AS DATE) THEN 'validation'
                    ELSE 'test'
                END AS split_name
            FROM read_parquet(?)
        ),
        split_presence AS (
            SELECT
                user_id,
                business_id,
                MAX(CASE WHEN split_name = 'train' THEN 1 ELSE 0 END) AS in_train,
                MAX(CASE WHEN split_name = 'validation' THEN 1 ELSE 0 END) AS in_validation,
                MAX(CASE WHEN split_name = 'test' THEN 1 ELSE 0 END) AS in_test
            FROM split_reviews
            GROUP BY user_id, business_id
        )
        SELECT
            SUM(CASE WHEN in_train = 1 AND in_validation = 1 THEN 1 ELSE 0 END) AS train_validation_pairs,
            SUM(CASE WHEN in_train = 1 AND in_test = 1 THEN 1 ELSE 0 END) AS train_test_pairs,
            SUM(CASE WHEN in_validation = 1 AND in_test = 1 THEN 1 ELSE 0 END) AS validation_test_pairs,
            SUM(CASE WHEN in_train = 1 AND in_validation = 1 AND in_test = 1 THEN 1 ELSE 0 END) AS all_split_pairs
        FROM split_presence
    """
    row = con.execute(
        query,
        [t1, t2, str(review_fact_path)],
    ).fetchone()
    overlap_counts = {
        "train_validation_pairs": int(row[0]) if row else 0,
        "train_test_pairs": int(row[1]) if row else 0,
        "validation_test_pairs": int(row[2]) if row else 0,
        "all_split_pairs": int(row[3]) if row else 0,
    }
    overlap_total = sum(overlap_counts.values())
    return [
        {
            "check_name": "cross_split_user_business_overlap",
            "status": "WARN" if overlap_total else "PASS",
            "severity": "warning" if overlap_total else "info",
            "finding_count": overlap_total,
            "detail": (
                "Overlap counts by split pair: "
                + ", ".join(f"{key}={value}" for key, value in overlap_counts.items())
            ),
            "source_path": str(review_fact_path),
        }
    ]


def _write_log(
    report: pd.DataFrame,
    log_path: Path,
    split_source: str,
    t1: str,
    t2: str,
) -> None:
    lines = [
        "Track A Stage 6 Leakage Audit",
        f"Selected split source: {split_source}",
        f"T1={t1}",
        f"T2={t2}",
        "",
    ]
    for row in report.itertuples(index=False):
        lines.append(
            f"[{row.status}] {row.check_name} ({row.severity}) count={row.finding_count}"
        )
        lines.append(f"  source: {row.source_path}")
        lines.append(f"  detail: {row.detail}")
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(config: dict[str, Any]) -> pd.DataFrame:
    curated_dir = _resolve_path(config, "curated_dir")
    tables_dir = _resolve_path(config, "tables_dir")
    logs_dir = _resolve_path(config, "logs_dir")
    review_fact_path = curated_dir / "review_fact.parquet"

    tables_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()
    try:
        t1, t2, split_source = load_candidate_splits(con, tables_dir, config)
        rows = []
        rows.extend(_schema_checks(con, review_fact_path))
        rows.extend(_scan_code_paths())
        rows.extend(_overlap_checks(con, review_fact_path, t1, t2))
        report = pd.DataFrame(rows)
    finally:
        con.close()

    report_path = tables_dir / "track_a_s6_leakage_report.parquet"
    log_path = logs_dir / "track_a_s6_leakage_audit.log"
    report.to_parquet(report_path, index=False)
    _write_log(report, log_path, split_source, t1, t2)
    logger.info("Wrote %s", report_path)
    logger.info("Wrote %s", log_path)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 6: Leakage Audit")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    config = load_config(args.config)
    run(config)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    main()
