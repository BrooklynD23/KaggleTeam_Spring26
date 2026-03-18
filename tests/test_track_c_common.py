"""Regression tests for Track C helper contracts."""

from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd

from src.eda.track_c.common import (
    TrackCPaths,
    drop_raw_text_columns,
    load_review_text_sample,
    scan_track_c_text_leaks,
    write_parquet,
)


def test_load_review_text_sample_uses_review_fact_semijoin(tmp_path: Path) -> None:
    """Track C text loading must semijoin against curated review ids."""
    executed_sqls: list[str] = []
    executed_params: list[list[str]] = []
    result = MagicMock()
    result.fetchdf.return_value = pd.DataFrame()
    con = MagicMock()

    def side_effect(sql: str, params=None) -> MagicMock:
        executed_sqls.append(sql)
        executed_params.append(params or [])
        return result

    con.execute.side_effect = side_effect

    review_path = tmp_path / "review.parquet"
    review_fact_path = tmp_path / "review_fact.parquet"
    review_path.touch()
    review_fact_path.touch()

    load_review_text_sample(con, review_path, review_fact_path, 100, 42)

    assert any(
        ("$2" in sql or len(params) >= 2)
        for sql, params in zip(executed_sqls, executed_params)
    )


def test_drop_raw_text_columns_removes_banned_names() -> None:
    """Raw text columns must be removed before parquet export."""
    df = pd.DataFrame(
        {
            "review_id": ["r1"],
            "text": ["hello"],
            "review_text": ["world"],
            "raw_text": ["!"],
            "city": ["Phoenix"],
        }
    )
    cleaned = drop_raw_text_columns(df)
    assert list(cleaned.columns) == ["review_id", "city"]


def test_write_parquet_raises_on_banned_text_columns(tmp_path: Path) -> None:
    """write_parquet must reject any DataFrame that contains banned text columns."""
    import pytest

    df_with_text = pd.DataFrame({"review_id": ["r1"], "review_text": ["hello world"]})
    with pytest.raises(ValueError, match="review_text"):
        write_parquet(df_with_text, tmp_path / "should_not_exist.parquet")
    assert not (tmp_path / "should_not_exist.parquet").exists()


def test_write_parquet_allows_clean_dataframe(tmp_path: Path) -> None:
    """write_parquet must accept DataFrames with no banned text columns."""
    df_clean = pd.DataFrame({"review_id": ["r1"], "city": ["Phoenix"], "review_stars": [4.0]})
    out = tmp_path / "clean.parquet"
    write_parquet(df_clean, out)
    assert out.exists()


def test_scan_track_c_text_leaks_flags_banned_columns(tmp_path: Path) -> None:
    """The Track C summary scan should find text columns but stay soft."""
    tables_dir = tmp_path / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"city": ["Phoenix"], "text": ["hello"]}).to_parquet(
        tables_dir / "track_c_test.parquet",
        index=False,
    )

    paths = TrackCPaths(
        curated_dir=tmp_path,
        tables_dir=tables_dir,
        figures_dir=tmp_path / "figures",
        logs_dir=tmp_path / "logs",
        review_fact_path=tmp_path / "review_fact.parquet",
        review_path=tmp_path / "review.parquet",
        business_path=tmp_path / "business.parquet",
        checkin_path=tmp_path / "checkin.parquet",
        checkin_expanded_path=tmp_path / "checkin_expanded.parquet",
        snapshot_metadata_path=tmp_path / "snapshot_metadata.json",
    )

    findings = scan_track_c_text_leaks(paths)

    assert findings
    assert findings[0]["status"] == "FAIL"
