"""Regression: Stage 7 must scan all track_b_*.parquet, not just s4 and s5."""

from pathlib import Path

import pandas as pd
import pytest

from src.eda.track_b.leakage_scope_check import BANNED_RAW_TEXT_COLUMNS


def test_banned_raw_text_columns_includes_review_body() -> None:
    """BANNED_RAW_TEXT_COLUMNS must include 'review_body' (case-insensitive match)."""
    assert "review_body" in BANNED_RAW_TEXT_COLUMNS, (
        "'review_body' must be in BANNED_RAW_TEXT_COLUMNS so it is caught during Stage 7 scan."
    )


def test_banned_raw_text_columns_includes_core_names() -> None:
    """BANNED_RAW_TEXT_COLUMNS must include text, review_text, and raw_text."""
    for name in ("text", "review_text", "raw_text"):
        assert name in BANNED_RAW_TEXT_COLUMNS, (
            f"'{name}' must be in BANNED_RAW_TEXT_COLUMNS."
        )


def test_check_parquet_schemas_scans_beyond_s4_and_s5(tmp_path: Path) -> None:
    """_check_parquet_schemas must include all track_b_*.parquet, not just s4/s5."""
    import duckdb
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class FakePaths:
        tables_dir: Path
        figures_dir: Path
        logs_dir: Path
        curated_dir: Path
        review_fact_track_b_path: Path
        snapshot_metadata_path: Path

    tables = tmp_path / "tables"
    tables.mkdir()

    # Create required artifacts with no banned columns
    for name in [
        "track_b_s4_label_candidates.parquet",
        "track_b_s5_feature_correlates.parquet",
    ]:
        pd.DataFrame({"review_id": ["r1"], "age_bucket": ["0-180"]}).to_parquet(
            tables / name, index=False
        )

    # Create an extra artifact with a banned simultaneous-observation column
    extra_path = tables / "track_b_s3_group_sizes_by_business_age.parquet"
    pd.DataFrame({"group_id": ["g1"], "funny": [5]}).to_parquet(extra_path, index=False)

    paths = FakePaths(
        tables_dir=tables,
        figures_dir=tmp_path / "figures",
        logs_dir=tmp_path / "logs",
        curated_dir=tmp_path / "curated",
        review_fact_track_b_path=tmp_path / "curated" / "review_fact_track_b.parquet",
        snapshot_metadata_path=tmp_path / "curated" / "snapshot_metadata.json",
    )

    from src.eda.track_b.leakage_scope_check import _check_parquet_schemas

    con = duckdb.connect()
    try:
        findings = _check_parquet_schemas(con, paths)  # type: ignore[arg-type]
    finally:
        con.close()

    # The extra artifact has a banned column — it must appear in findings
    extra_fail = [
        f for f in findings
        if "track_b_s3_group_sizes_by_business_age" in f["artifact_path"]
        and f["status"] == "FAIL"
    ]
    assert extra_fail, (
        "_check_parquet_schemas must scan all track_b_*.parquet, not only s4 and s5. "
        "The extra artifact with a banned 'funny' column must produce a FAIL finding."
    )
