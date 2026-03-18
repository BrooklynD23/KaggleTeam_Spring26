"""Regression tests for split-loading helpers."""

from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

from src.common.artifacts import load_candidate_splits, load_splits_strict


def _make_mock_con(df: pd.DataFrame) -> MagicMock:
    result = MagicMock()
    result.fetchdf.return_value = df
    con = MagicMock()
    con.execute.return_value = result
    return con


def test_normalises_legacy_t1_date_t2_date(tmp_path: Path) -> None:
    """Legacy t1_date/t2_date columns must be mapped to canonical t1/t2."""
    # Build a fake parquet with legacy column names
    legacy_df = pd.DataFrame(
        {
            "candidate_id": ["candidate_1"],
            "t1_date": ["2020-01-01"],
            "t2_date": ["2021-01-01"],
            "recommended": [True],
        }
    )
    parquet_path = tmp_path / "track_a_s5_candidate_splits.parquet"
    legacy_df.to_parquet(parquet_path, index=False)

    import duckdb

    con = duckdb.connect()
    try:
        t1, t2, source = load_candidate_splits(con, tmp_path, {})
    finally:
        con.close()

    assert t1 == "2020-01-01", f"Expected t1='2020-01-01', got {t1!r}"
    assert t2 == "2021-01-01", f"Expected t2='2021-01-01', got {t2!r}"
    assert source == "track_a_s5_candidate_splits.parquet"


def test_reads_canonical_t1_t2(tmp_path: Path) -> None:
    """Canonical t1/t2 columns must be read without renaming."""
    df = pd.DataFrame(
        {
            "candidate_id": ["candidate_1"],
            "t1": ["2020-06-01"],
            "t2": ["2021-06-01"],
            "recommended": [True],
        }
    )
    parquet_path = tmp_path / "track_a_s5_candidate_splits.parquet"
    df.to_parquet(parquet_path, index=False)

    import duckdb

    con = duckdb.connect()
    try:
        t1, t2, source = load_candidate_splits(con, tmp_path, {})
    finally:
        con.close()

    assert t1 == "2020-06-01"
    assert t2 == "2021-06-01"


def test_falls_back_to_config_when_no_parquet(tmp_path: Path) -> None:
    """When no parquet exists, config split values must be returned."""
    import duckdb

    config = {"splits": {"t1": "2019-01-01", "t2": "2020-01-01"}}
    con = duckdb.connect()
    try:
        t1, t2, source = load_candidate_splits(con, tmp_path, config)
    finally:
        con.close()

    assert t1 == "2019-01-01"
    assert t2 == "2020-01-01"
    assert source == "config"


def test_load_splits_strict_reads_parquet_when_present(tmp_path: Path) -> None:
    """Strict loading should still accept the materialized Stage 5 artifact."""
    df = pd.DataFrame(
        {
            "candidate_id": ["candidate_1"],
            "t1": ["2020-08-01"],
            "t2": ["2021-02-01"],
            "recommended": [True],
        }
    )
    parquet_path = tmp_path / "track_a_s5_candidate_splits.parquet"
    df.to_parquet(parquet_path, index=False)

    import duckdb

    config = {"splits": {"require_stage5_artifact": True}}
    con = duckdb.connect()
    try:
        t1, t2, source = load_splits_strict(con, tmp_path, config)
    finally:
        con.close()

    assert t1 == "2020-08-01"
    assert t2 == "2021-02-01"
    assert source == "track_a_s5_candidate_splits.parquet"


def test_load_splits_strict_raises_when_required_artifact_is_missing(tmp_path: Path) -> None:
    """Track D strict mode must fail rather than use placeholder config dates."""
    import duckdb

    config = {
        "splits": {
            "t1": "2019-06-01",
            "t2": "2020-09-01",
            "require_stage5_artifact": True,
        }
    }
    con = duckdb.connect()
    try:
        with pytest.raises(RuntimeError, match="Track D requires Track A Stage 5 split artifact"):
            load_splits_strict(con, tmp_path, config)
    finally:
        con.close()


def test_load_splits_strict_allows_config_fallback_when_not_required(tmp_path: Path) -> None:
    """Strict helper should still behave like the legacy loader when disabled."""
    import duckdb

    config = {
        "splits": {
            "t1": "2019-06-01",
            "t2": "2020-09-01",
            "require_stage5_artifact": False,
        }
    }
    con = duckdb.connect()
    try:
        t1, t2, source = load_splits_strict(con, tmp_path, config)
    finally:
        con.close()

    assert t1 == "2019-06-01"
    assert t2 == "2020-09-01"
    assert source == "config"
