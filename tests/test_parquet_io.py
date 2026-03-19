"""Regression tests for the shared Polars parquet I/O layer."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import polars as pl
import pytest

from src.common.parquet_io import collect_frame, read_parquet_pandas, scan_parquet


@pytest.fixture()
def sample_parquet(tmp_path: Path) -> Path:
    """Write a small parquet file and return its path."""
    df = pl.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "name": ["a", "b", "c", "d", "e"],
            "value": [10.0, 20.0, 30.0, 40.0, 50.0],
        }
    )
    path = tmp_path / "sample.parquet"
    df.write_parquet(path)
    return path


def test_scan_parquet_returns_lazy_frame(sample_parquet: Path) -> None:
    lf = scan_parquet(sample_parquet)
    assert isinstance(lf, pl.LazyFrame)


def test_scan_parquet_with_columns(sample_parquet: Path) -> None:
    lf = scan_parquet(sample_parquet, columns=["id", "value"])
    df = lf.collect()
    assert df.columns == ["id", "value"]
    assert len(df) == 5


def test_scan_parquet_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        scan_parquet(tmp_path / "does_not_exist.parquet")


def test_collect_frame_materializes(sample_parquet: Path) -> None:
    lf = scan_parquet(sample_parquet)
    df = collect_frame(lf)
    assert isinstance(df, pl.DataFrame)
    assert len(df) == 5


def test_read_parquet_pandas_returns_pandas(sample_parquet: Path) -> None:
    df = read_parquet_pandas(sample_parquet)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 5
    assert set(df.columns) == {"id", "name", "value"}


def test_read_parquet_pandas_column_subset(sample_parquet: Path) -> None:
    df = read_parquet_pandas(sample_parquet, columns=["id"])
    assert list(df.columns) == ["id"]
    assert len(df) == 5


def test_read_parquet_pandas_with_filter(sample_parquet: Path) -> None:
    df = read_parquet_pandas(
        sample_parquet,
        filters=pl.col("value") > 25,
    )
    assert len(df) == 3
    assert all(v > 25 for v in df["value"])
