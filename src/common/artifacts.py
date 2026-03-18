"""Shared artifact-loading helpers for EDA pipeline stages."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import duckdb

logger = logging.getLogger(__name__)


def load_candidate_splits(
    con: duckdb.DuckDBPyConnection,
    tables_dir: Path,
    config: dict[str, Any],
) -> tuple[str, str, str]:
    """Return (t1, t2, source) for the recommended candidate split.

    Normalises both the legacy ``t1_date``/``t2_date`` schema written by
    older Stage 5 runs and the canonical ``t1``/``t2`` schema produced by
    current Stage 5 runs.  Falls back to config values when no parquet is
    present.

    Args:
        con: Open DuckDB connection (not closed by this function).
        tables_dir: Directory that may contain
            ``track_a_s5_candidate_splits.parquet``.
        config: Loaded pipeline configuration dict.

    Returns:
        Tuple of ``(t1_str, t2_str, source_label)`` where ``source_label``
        is the parquet filename or ``"config"``.
    """
    candidate_path = tables_dir / "track_a_s5_candidate_splits.parquet"
    if candidate_path.is_file():
        df = con.execute(
            "SELECT * FROM read_parquet(?)",
            [str(candidate_path)],
        ).fetchdf()

        # Normalise legacy column names: t1_date -> t1, t2_date -> t2
        rename_map: dict[str, str] = {}
        if "t1_date" in df.columns and "t1" not in df.columns:
            rename_map["t1_date"] = "t1"
        if "t2_date" in df.columns and "t2" not in df.columns:
            rename_map["t2_date"] = "t2"
        if rename_map:
            df = df.rename(columns=rename_map)
            logger.debug(
                "Normalised legacy split columns %s -> canonical t1/t2",
                list(rename_map.keys()),
            )

        for marker in ("recommended", "is_recommended", "selected"):
            if marker in df.columns:
                selected = df[df[marker].fillna(False).astype(bool)]
                if not selected.empty and {"t1", "t2"}.issubset(df.columns):
                    row = selected.iloc[0]
                    return str(row["t1"]), str(row["t2"]), candidate_path.name

        if {"t1", "t2"}.issubset(df.columns) and not df.empty:
            row = df.iloc[0]
            return str(row["t1"]), str(row["t2"]), candidate_path.name

    splits = config.get("splits", {})
    return str(splits.get("t1", "")), str(splits.get("t2", "")), "config"


def load_splits_strict(
    con: duckdb.DuckDBPyConnection,
    tables_dir: Path,
    config: dict[str, Any],
) -> tuple[str, str, str]:
    """Load candidate splits, optionally refusing config-placeholder fallback.

    Track D depends on Track A Stage 5's materialized candidate split artifact.
    When ``splits.require_stage5_artifact`` is true and the split source falls
    back to config placeholders, this helper raises a runtime error instead of
    silently proceeding with placeholder dates.
    """
    t1, t2, source = load_candidate_splits(con, tables_dir, config)
    require_stage5_artifact = bool(
        config.get("splits", {}).get("require_stage5_artifact", False)
    )
    if source == "config" and require_stage5_artifact:
        raise RuntimeError(
            "Track D requires Track A Stage 5 split artifact "
            "(track_a_s5_candidate_splits.parquet) but it was not found. "
            "Run Track A through Stage 5 before running Track D. "
            f"Placeholder dates t1={t1}, t2={t2} were NOT used."
        )
    return t1, t2, source
