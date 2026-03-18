"""Regression tests for checkin_expanded parquet export."""

from __future__ import annotations

import json
from pathlib import Path

import duckdb

from src.curate.build_review_fact import _export_checkin_expanded


def test_export_checkin_expanded_splits_dates_and_logs_invalid_values(
    tmp_path: Path,
) -> None:
    """Expanded checkins should keep valid timestamps and log invalid ones."""
    curated_dir = tmp_path / "curated"
    logs_dir = tmp_path / "logs"

    con = duckdb.connect()
    try:
        con.execute(
            """
            CREATE TABLE checkin (
                business_id VARCHAR,
                checkin_dates VARCHAR
            )
            """
        )
        con.execute(
            """
            INSERT INTO checkin VALUES
                ('biz_1', '2016-04-26 19:49:16, 2016-08-30 18:36:57'),
                ('biz_2', '2018-01-01 00:00:00, not-a-date, 2018-02-02 12:00:00'),
                ('biz_3', NULL)
            """
        )

        _export_checkin_expanded(con, curated_dir, logs_dir, compression="zstd")
    finally:
        con.close()

    expanded_path = curated_dir / "checkin_expanded.parquet"
    assert expanded_path.is_file()

    con = duckdb.connect()
    try:
        rows = con.execute(
            """
            SELECT business_id, checkin_date::VARCHAR
            FROM read_parquet(?)
            ORDER BY business_id, checkin_date
            """,
            [str(expanded_path)],
        ).fetchall()
    finally:
        con.close()

    assert rows == [
        ("biz_1", "2016-04-26"),
        ("biz_1", "2016-08-30"),
        ("biz_2", "2018-01-01"),
        ("biz_2", "2018-02-02"),
    ]

    invalid_log = logs_dir / "checkin_expanded_invalid_rows.jsonl"
    assert invalid_log.is_file()
    payloads = [
        json.loads(line)
        for line in invalid_log.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert payloads == [
        {"business_id": "biz_2", "raw_checkin_value": "not-a-date"},
    ]
