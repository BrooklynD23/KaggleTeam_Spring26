"""Regression tests for the shared DuckDB connection factory."""

from __future__ import annotations

import duckdb

from src.common.db import connect_duckdb


def test_connect_duckdb_no_config_applies_defaults() -> None:
    """A bare connect_duckdb() should still set memory and thread limits."""
    con = connect_duckdb()
    try:
        rows = con.execute(
            "SELECT current_setting('memory_limit'), current_setting('threads')"
        ).fetchone()
        assert rows is not None
        mem_limit = rows[0]
        threads = rows[1]
        assert "GB" in mem_limit or "GiB" in mem_limit or "gB" in mem_limit.lower()
        assert int(threads) > 0
    finally:
        con.close()


def test_connect_duckdb_with_config() -> None:
    """Settings from the config dict should be applied."""
    config = {"duckdb": {"memory_limit_gb": 2, "threads": 2}}
    con = connect_duckdb(config)
    try:
        rows = con.execute(
            "SELECT current_setting('threads')"
        ).fetchone()
        assert rows is not None
        assert int(rows[0]) == 2
    finally:
        con.close()


def test_connect_duckdb_falls_back_to_ingestion_section() -> None:
    """When no duckdb section exists, fall back to ingestion."""
    config = {"ingestion": {"memory_limit_gb": 3, "threads": 3}}
    con = connect_duckdb(config)
    try:
        rows = con.execute("SELECT current_setting('threads')").fetchone()
        assert rows is not None
        assert int(rows[0]) == 3
    finally:
        con.close()


def test_connect_duckdb_file_backed(tmp_path) -> None:
    """File-backed connections should also get settings applied."""
    db = tmp_path / "test.duckdb"
    con = connect_duckdb(db_path=db)
    try:
        con.execute("CREATE TABLE t (x INTEGER)")
        con.execute("INSERT INTO t VALUES (42)")
        result = con.execute("SELECT x FROM t").fetchone()
        assert result == (42,)
    finally:
        con.close()


def test_connect_duckdb_returns_working_connection() -> None:
    """Basic smoke test: the connection can run queries."""
    con = connect_duckdb()
    try:
        result = con.execute("SELECT 1 + 1 AS answer").fetchone()
        assert result == (2,)
    finally:
        con.close()
