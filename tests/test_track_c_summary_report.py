"""Regression tests for Track C summary rendering."""

from pathlib import Path

import pandas as pd

from src.eda.track_c.common import TrackCPaths
from src.eda.track_c.summary_report import build_summary


def test_build_summary_mentions_text_leak_scan(tmp_path: Path) -> None:
    """Summary should always include the soft text leak section."""
    tables_dir = tmp_path / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"city": ["Phoenix"], "is_analyzable": [True]}).to_parquet(
        tables_dir / "track_c_s1_city_coverage.parquet",
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

    summary = build_summary(paths)

    assert "## Text Leak Scan" in summary
    assert "city/state only" in summary
