"""Post-ingestion schema validation checks on DuckDB tables.

Usage:
    python -m src.validate.schema_checks --config configs/base.yaml
"""

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb

from src.common.config import load_config

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Key columns per entity that must have low null rates.
KEY_COLUMNS: dict[str, list[str]] = {
    "business": ["business_id", "name", "city", "state", "stars"],
    "review": ["review_id", "user_id", "business_id", "stars", "review_date"],
    "user": ["user_id", "name", "yelping_since"],
    "tip": ["user_id", "business_id", "text", "tip_date"],
    "checkin": ["business_id", "checkin_dates"],
}

# Columns to check date ranges on (entity -> column name).
DATE_COLUMNS: dict[str, str] = {
    "review": "review_date",
    "user": "yelping_since",
    "tip": "tip_date",
}

NULL_THRESHOLD = 0.01  # 1%


@dataclass(frozen=True)
class EntityReport:
    """Validation report for a single entity."""

    entity: str
    row_count: int
    null_rates: dict[str, float]
    min_date: str | None
    max_date: str | None
    status: str


def _check_entity(
    con: duckdb.DuckDBPyConnection,
    entity: str,
) -> EntityReport:
    """Run row count, null rate, and date range checks for one entity."""
    table_name = f'"{entity}"' if entity == "user" else entity
    row_count: int = con.execute(
        f"SELECT COUNT(*) FROM {table_name}"
    ).fetchone()[0]  # type: ignore[index]

    # Null rates for key columns
    key_cols = KEY_COLUMNS.get(entity, [])
    null_rates: dict[str, float] = {}
    for col in key_cols:
        null_count: int = con.execute(
            f'SELECT COUNT(*) FROM {table_name} WHERE "{col}" IS NULL'
        ).fetchone()[0]  # type: ignore[index]
        null_rates[col] = null_count / row_count if row_count > 0 else 0.0

    # Date range
    min_date: str | None = None
    max_date: str | None = None
    if entity in DATE_COLUMNS:
        date_col = DATE_COLUMNS[entity]
        row = con.execute(
            f"SELECT MIN({date_col})::VARCHAR, MAX({date_col})::VARCHAR "
            f"FROM {table_name}"
        ).fetchone()
        if row:
            min_date, max_date = row[0], row[1]

    # Determine status
    failed_cols = [
        col for col, rate in null_rates.items() if rate > NULL_THRESHOLD
    ]
    status = "FAIL" if failed_cols else "PASS"

    if failed_cols:
        logger.warning(
            "Entity '%s' FAIL: columns with >%.1f%% nulls: %s",
            entity, NULL_THRESHOLD * 100, failed_cols,
        )

    return EntityReport(
        entity=entity,
        row_count=row_count,
        null_rates=null_rates,
        min_date=min_date,
        max_date=max_date,
        status=status,
    )


def run(config: dict[str, Any]) -> list[EntityReport]:
    """Run schema checks on all entities."""
    paths_cfg = config["paths"]
    db_path = PROJECT_ROOT / paths_cfg["db_path"]

    if not db_path.is_file():
        raise FileNotFoundError(f"DuckDB database not found: {db_path}")

    con = duckdb.connect(str(db_path), read_only=True)
    entities: list[dict[str, Any]] = config["entities"]
    reports: list[EntityReport] = []

    for ent in entities:
        name = ent["name"]
        report = _check_entity(con, name)
        reports.append(report)

        logger.info(
            "Entity '%s': rows=%d, status=%s, date_range=[%s, %s]",
            report.entity, report.row_count, report.status,
            report.min_date, report.max_date,
        )
        for col, rate in report.null_rates.items():
            logger.info("  %s null rate: %.4f%%", col, rate * 100)

    con.close()

    overall = "PASS" if all(r.status == "PASS" for r in reports) else "FAIL"
    logger.info("Overall schema check status: %s", overall)

    return reports


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run post-ingestion schema validation checks",
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
