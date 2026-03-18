"""Build the review_fact table and Track B view, export to Parquet.

Usage:
    python -m src.curate.build_review_fact --config configs/base.yaml
"""

import argparse
import json
import logging
import time
from pathlib import Path
from typing import Any

import duckdb

from src.common.config import load_config

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

REVIEW_FACT_SQL = """\
CREATE OR REPLACE TABLE review_fact AS
SELECT
    r.review_id,
    r.user_id,
    r.business_id,
    r.stars AS review_stars,
    r.review_date,
    r.useful,
    LENGTH(r.text) AS text_char_count,
    ARRAY_LENGTH(STRING_SPLIT(TRIM(r.text), ' ')) AS text_word_count,
    b.city,
    b.state,
    b.categories,
    b.latitude,
    b.longitude,
    u.yelping_since,
    EXTRACT(YEAR FROM r.review_date) AS review_year,
    EXTRACT(MONTH FROM r.review_date) AS review_month,
    DATEDIFF('day', u.yelping_since, r.review_date) AS user_tenure_days
FROM review r
JOIN business b ON r.business_id = b.business_id
JOIN "user" u ON r.user_id = u.user_id
WHERE r.review_date IS NOT NULL AND r.stars IS NOT NULL
"""

REVIEW_FACT_TRACK_B_SQL = """\
CREATE OR REPLACE VIEW review_fact_track_b AS
SELECT
    rf.*,
    b.is_open,
    u.fans,
    u.elite
FROM review_fact rf
JOIN business b ON rf.business_id = b.business_id
JOIN "user" u ON rf.user_id = u.user_id
"""

ENTITY_TABLES = ["business", "user", "review", "tip", "checkin"]

CHECKIN_EXPANDED_SQL = """\
SELECT
    c.business_id,
    CAST(TRY_CAST(TRIM(unnested.value) AS TIMESTAMP) AS DATE) AS checkin_date
FROM checkin c,
     UNNEST(STRING_SPLIT(c.checkin_dates, ',')) AS unnested(value)
WHERE TRIM(unnested.value) != ''
  AND TRY_CAST(TRIM(unnested.value) AS TIMESTAMP) IS NOT NULL
"""

CHECKIN_INVALID_SQL = """\
SELECT
    c.business_id,
    TRIM(unnested.value) AS raw_checkin_value
FROM checkin c,
     UNNEST(STRING_SPLIT(c.checkin_dates, ',')) AS unnested(value)
WHERE TRIM(unnested.value) != ''
  AND TRY_CAST(TRIM(unnested.value) AS TIMESTAMP) IS NULL
ORDER BY c.business_id, raw_checkin_value
"""


def _validate_row_loss(
    con: duckdb.DuckDBPyConnection,
    max_loss_fraction: float,
    logs_dir: Path,
) -> str:
    """Validate row loss between raw review and review_fact.

    Returns 'PASS' or 'FAIL'.
    """
    raw_count: int = con.execute("SELECT COUNT(*) FROM review").fetchone()[0]  # type: ignore[index]
    fact_count: int = con.execute("SELECT COUNT(*) FROM review_fact").fetchone()[0]  # type: ignore[index]
    dropped = raw_count - fact_count

    if raw_count == 0:
        logger.warning("Raw review table is empty")
        return "FAIL"

    loss_fraction = dropped / raw_count
    logger.info(
        "Row-loss validation: raw=%d, fact=%d, dropped=%d (%.4f%%)",
        raw_count, fact_count, dropped, loss_fraction * 100,
    )

    if loss_fraction > max_loss_fraction:
        logger.error(
            "FAIL: row loss %.4f%% exceeds threshold %.4f%%",
            loss_fraction * 100, max_loss_fraction * 100,
        )
    if dropped > 0:
        logs_dir.mkdir(parents=True, exist_ok=True)
        orphan_rows = con.execute(
            """
            SELECT
                r.review_id,
                TRIM(
                    BOTH ';' FROM CONCAT(
                        CASE WHEN b.business_id IS NULL THEN 'missing_business;' ELSE '' END,
                        CASE WHEN u.user_id IS NULL THEN 'missing_user;' ELSE '' END,
                        CASE WHEN r.review_date IS NULL THEN 'null_review_date;' ELSE '' END,
                        CASE WHEN r.stars IS NULL THEN 'null_review_stars;' ELSE '' END
                    )
                ) AS missing_reason
            FROM review r
            LEFT JOIN business b ON r.business_id = b.business_id
            LEFT JOIN "user" u ON r.user_id = u.user_id
            WHERE
                b.business_id IS NULL
                OR u.user_id IS NULL
                OR r.review_date IS NULL
                OR r.stars IS NULL
            ORDER BY r.review_id
            """
        ).fetchall()

        orphan_log = logs_dir / "review_fact_orphans.jsonl"
        with open(orphan_log, "w", encoding="utf-8") as fh:
            for review_id, missing_reason in orphan_rows:
                record = {
                    "review_id": review_id,
                    "missing_reason": missing_reason,
                }
                fh.write(json.dumps(record) + "\n")

        logger.warning(
            "%d reviews dropped; orphan log written to %s",
            dropped, orphan_log,
        )

    if loss_fraction > max_loss_fraction:
        return "FAIL"

    logger.info("Row-loss validation: PASS")
    return "PASS"


def _export_parquet(
    con: duckdb.DuckDBPyConnection,
    table_or_query: str,
    output_path: Path,
    compression: str = "zstd",
) -> None:
    """Export a table or query result to a Parquet file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    file_str = str(output_path).replace("\\", "/")

    # If it looks like a table/view name (no spaces), use COPY
    if " " not in table_or_query:
        table_ref = f'"{table_or_query}"' if table_or_query == "user" else table_or_query
        sql = (
            f"COPY {table_ref} TO '{file_str}' "
            f"(FORMAT PARQUET, COMPRESSION '{compression}')"
        )
    else:
        sql = (
            f"COPY ({table_or_query}) TO '{file_str}' "
            f"(FORMAT PARQUET, COMPRESSION '{compression}')"
        )

    con.execute(sql)
    logger.info("Exported Parquet: %s", output_path)


def _build_snapshot_metadata(
    con: duckdb.DuckDBPyConnection,
    curated_dir: Path,
) -> dict[str, str]:
    """Compute and export snapshot_metadata.json."""
    row = con.execute(
        "SELECT GREATEST("
        "  COALESCE((SELECT MAX(review_date) FROM review), DATE '1900-01-01'),"
        "  COALESCE((SELECT MAX(tip_date) FROM tip), DATE '1900-01-01')"
        ")::VARCHAR"
    ).fetchone()
    reference_date: str = row[0] if row and row[0] else "unknown"  # type: ignore[index]

    metadata = {
        "snapshot_reference_date": reference_date,
        "dataset_release_tag": "yelp_academic_2022",
        "computed_from": "MAX(review_date, tip_date)",
    }

    curated_dir.mkdir(parents=True, exist_ok=True)
    meta_path = curated_dir / "snapshot_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2)

    logger.info("Wrote snapshot metadata to %s: %s", meta_path, metadata)
    return metadata


def _export_checkin_expanded(
    con: duckdb.DuckDBPyConnection,
    curated_dir: Path,
    logs_dir: Path,
    compression: str,
) -> None:
    """Export per-date checkin rows and log any invalid timestamp values."""
    invalid_rows = con.execute(CHECKIN_INVALID_SQL).fetchall()
    if invalid_rows:
        logs_dir.mkdir(parents=True, exist_ok=True)
        invalid_path = logs_dir / "checkin_expanded_invalid_rows.jsonl"
        with open(invalid_path, "w", encoding="utf-8") as fh:
            for business_id, raw_value in invalid_rows:
                fh.write(
                    json.dumps(
                        {
                            "business_id": business_id,
                            "raw_checkin_value": raw_value,
                        }
                    )
                    + "\n"
                )
        logger.warning(
            "Dropped %d invalid check-in timestamps; details written to %s",
            len(invalid_rows),
            invalid_path,
        )

    _export_parquet(
        con,
        CHECKIN_EXPANDED_SQL,
        curated_dir / "checkin_expanded.parquet",
        compression,
    )


def run(config: dict[str, Any]) -> None:
    """Execute the full curation pipeline."""
    paths_cfg = config["paths"]
    quality_cfg = config.get("quality", {})

    db_path = PROJECT_ROOT / paths_cfg["db_path"]
    curated_dir = PROJECT_ROOT / paths_cfg["curated_dir"]
    logs_dir = PROJECT_ROOT / paths_cfg["logs_dir"]
    compression = config.get("ingestion", {}).get("parquet_compression", "zstd")
    max_loss = quality_cfg.get("review_fact_max_row_loss_fraction", 0.001)

    if not db_path.is_file():
        raise FileNotFoundError(f"DuckDB database not found: {db_path}")

    con = duckdb.connect(str(db_path))
    temp_dir = Path("/tmp/kaggleteam_duckdb_tmp")
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_dir_str = str(temp_dir).replace("\\", "/")
    con.execute(f"PRAGMA temp_directory='{temp_dir_str}'")
    logger.info("DuckDB temp_directory=%s", temp_dir)
    try:
        # Step 1: Build review_fact table
        logger.info("Building review_fact table...")
        t0 = time.perf_counter()
        con.execute(REVIEW_FACT_SQL)
        elapsed = time.perf_counter() - t0

        fact_count: int = con.execute(
            "SELECT COUNT(*) FROM review_fact"
        ).fetchone()[0]  # type: ignore[index]
        logger.info("review_fact: %d rows in %.1f seconds", fact_count, elapsed)

        # Step 2: Build review_fact_track_b view
        logger.info("Building review_fact_track_b view...")
        con.execute(REVIEW_FACT_TRACK_B_SQL)
        track_b_count: int = con.execute(
            "SELECT COUNT(*) FROM review_fact_track_b"
        ).fetchone()[0]  # type: ignore[index]
        logger.info("review_fact_track_b: %d rows", track_b_count)

        # Step 3: Row-loss validation
        status = _validate_row_loss(con, max_loss, logs_dir)
        if status == "FAIL":
            raise RuntimeError("Row-loss validation failed; review_fact exports aborted")

        # Step 4: Export Parquet files
        curated_dir.mkdir(parents=True, exist_ok=True)

        _export_parquet(con, "review_fact", curated_dir / "review_fact.parquet", compression)
        _export_parquet(
            con,
            "SELECT * FROM review_fact_track_b",
            curated_dir / "review_fact_track_b.parquet",
            compression,
        )

        for entity in ENTITY_TABLES:
            _export_parquet(
                con, entity, curated_dir / f"{entity}.parquet", compression,
            )

        _export_checkin_expanded(con, curated_dir, logs_dir, compression)

        # Step 5: Snapshot metadata
        _build_snapshot_metadata(con, curated_dir)
    finally:
        con.close()
    logger.info("Curation pipeline complete")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Build review_fact table and export Parquet files",
    )
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to YAML config file",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    config = load_config(args.config)
    log_level = config.get("log_level", "INFO")
    logging.getLogger().setLevel(getattr(logging, log_level))

    run(config)


if __name__ == "__main__":
    main()
