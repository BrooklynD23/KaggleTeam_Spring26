"""Shared Polars-based parquet I/O layer.

Provides lazy-scan readers that replace ad-hoc ``duckdb.connect()`` →
``read_parquet()`` → ``fetchdf()`` one-liners with Polars lazy frames
that benefit from predicate pushdown and projection pushdown.

When YELP_POLARS_ENGINE=gpu is set (by the pipeline launcher when
cudf-polars is installed), collect operations use engine="gpu" for
GPU-accelerated execution.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pandas as pd
import polars as pl

logger = logging.getLogger(__name__)

_GPU_ENGINE_ENV = "YELP_POLARS_ENGINE"


def _preferred_collect_engine() -> str | None:
    """Return 'gpu' when GPU acceleration is requested, else None (default)."""
    if os.environ.get(_GPU_ENGINE_ENV, "").strip().lower() == "gpu":
        return "gpu"
    return None


def scan_parquet(
    path: Path | str,
    columns: list[str] | None = None,
) -> pl.LazyFrame:
    """Return a Polars lazy frame backed by a parquet file.

    Predicate and projection pushdown are applied automatically when
    the lazy frame is collected.

    Args:
        path: Path to a ``.parquet`` file.
        columns: Optional column subset to select (projection pushdown).
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Parquet file not found: {p}")
    lf = pl.scan_parquet(p)
    if columns is not None:
        lf = lf.select(columns)
    return lf


def collect_frame(
    lf: pl.LazyFrame,
    *,
    streaming: bool = False,
) -> pl.DataFrame:
    """Materialize a lazy frame, optionally in streaming or GPU mode.

    Use ``streaming=True`` when the intermediate result set is large
    and you want Polars to process it in batches. When
    YELP_POLARS_ENGINE=gpu is set, uses GPU acceleration (unless
    streaming is requested).
    """
    if streaming:
        return lf.collect(engine="streaming")
    engine = _preferred_collect_engine()
    if engine == "gpu":
        try:
            return lf.collect(engine="gpu")
        except Exception as e:
            logger.warning("GPU collect failed, falling back to CPU: %s", e)
    return lf.collect()


def read_parquet_pandas(
    path: Path | str,
    columns: list[str] | None = None,
    filters: pl.Expr | None = None,
) -> pd.DataFrame:
    """Read a parquet file into a pandas DataFrame via Polars.

    This replaces the DuckDB pattern of ``duckdb.connect()`` →
    ``read_parquet()`` → ``fetchdf()`` with a zero-DuckDB path that
    still gets predicate and projection pushdown through Polars.

    Args:
        path: Path to a ``.parquet`` file.
        columns: Optional column subset (projection pushdown).
        filters: Optional Polars filter expression (predicate pushdown).

    Returns:
        A pandas DataFrame.
    """
    lf = scan_parquet(path, columns=columns)
    if filters is not None:
        lf = lf.filter(filters)
    engine = _preferred_collect_engine()
    if engine == "gpu":
        try:
            return lf.collect(engine="gpu").to_pandas()
        except Exception as e:
            logger.warning("GPU collect failed, falling back to CPU: %s", e)
    return lf.collect().to_pandas()
