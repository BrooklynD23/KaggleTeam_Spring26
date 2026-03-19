"""Shared DuckDB connection factory.

Every module that opens a DuckDB connection should use ``connect_duckdb``
instead of calling ``duckdb.connect()`` directly.  This ensures that
memory_limit, threads, temp_directory, and preserve_insertion_order are
applied consistently across the entire pipeline.
"""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Any

import duckdb

logger = logging.getLogger(__name__)


def _duckdb_settings(config: dict[str, Any] | None) -> dict[str, Any]:
    """Extract DuckDB runtime settings from *config* with sensible defaults.

    Reads from ``config["duckdb"]`` first, falling back to
    ``config["ingestion"]`` for backward compatibility with older configs.
    """
    if config is None:
        return {
            "memory_limit_gb": 8,
            "threads": os.cpu_count() or 4,
            "preserve_insertion_order": False,
        }

    duckdb_cfg = config.get("duckdb", {})
    ingest_cfg = config.get("ingestion", {})

    return {
        "memory_limit_gb": int(
            duckdb_cfg.get("memory_limit_gb", ingest_cfg.get("memory_limit_gb", 8))
        ),
        "threads": int(
            duckdb_cfg.get("threads", ingest_cfg.get("threads", os.cpu_count() or 4))
        ),
        "preserve_insertion_order": bool(
            duckdb_cfg.get("preserve_insertion_order", False)
        ),
    }


def connect_duckdb(
    config: dict[str, Any] | None = None,
    *,
    db_path: str | Path | None = None,
    read_only: bool = False,
) -> duckdb.DuckDBPyConnection:
    """Create a DuckDB connection with standardized runtime settings.

    When *config* is provided, settings are read from the ``duckdb`` key
    (falling back to ``ingestion`` for backward compatibility).  Without
    config, sensible defaults (8 GB, all CPU cores) are applied.

    Args:
        config: Loaded pipeline config dict (optional).
        db_path: Path to a persistent DuckDB file.  ``None`` → in-memory.
        read_only: Open the file in read-only mode (file-backed only).

    Returns:
        A configured ``duckdb.DuckDBPyConnection``.
    """
    settings = _duckdb_settings(config)

    if db_path is not None:
        con = duckdb.connect(str(db_path), read_only=read_only)
    else:
        con = duckdb.connect()

    con.execute(f"SET memory_limit = '{settings['memory_limit_gb']}GB'")
    con.execute(f"SET threads = {settings['threads']}")
    con.execute(
        f"SET preserve_insertion_order = {str(settings['preserve_insertion_order']).lower()}"
    )

    temp_dir = Path(tempfile.gettempdir()) / "kaggleteam_duckdb_tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_dir_str = str(temp_dir).replace("\\", "/")
    con.execute(f"PRAGMA temp_directory='{temp_dir_str}'")

    logger.info(
        "DuckDB connection: memory_limit=%dGB threads=%d "
        "preserve_insertion_order=%s temp_dir=%s",
        settings["memory_limit_gb"],
        settings["threads"],
        settings["preserve_insertion_order"],
        temp_dir,
    )

    return con
