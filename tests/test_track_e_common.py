"""Unit tests for Track E shared helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.eda.track_e.common import (
    assign_price_tier,
    assign_review_volume_tier,
    enforce_min_group_size,
    resolve_paths,
    write_parquet,
)


def _config() -> dict[str, object]:
    return {
        "paths": {
            "curated_dir": "data/curated",
            "tables_dir": "outputs/tables",
            "figures_dir": "outputs/figures",
            "logs_dir": "outputs/logs",
        },
        "subgroups": {
            "price_tier_labels": {1: "low", 2: "medium", 3: "high", 4: "premium"},
            "price_tier_missing_label": "missing",
        },
    }


def test_resolve_paths_uses_repo_relative_paths() -> None:
    """Track E paths should resolve base config-relative locations."""
    paths = resolve_paths(_config())

    assert paths.curated_dir.name == "curated"
    assert paths.tables_dir.name == "tables"
    assert paths.review_fact_path == paths.curated_dir / "review_fact.parquet"


def test_enforce_min_group_size_drops_small_groups_and_keeps_threshold() -> None:
    """Rows below the minimum should be removed while threshold rows remain."""
    df = pd.DataFrame(
        {
            "subgroup_value": ["small", "edge", "large"],
            "business_count": [1, 10, 12],
        }
    )

    filtered = enforce_min_group_size(df, "business_count", 10)

    assert filtered["subgroup_value"].tolist() == ["edge", "large"]


def test_assign_price_tier_and_review_volume_tier_follow_config() -> None:
    """Tier assignment should respect configured labels and boundaries."""
    config = _config()

    assert assign_price_tier(2, config) == "medium"
    assert assign_price_tier(None, config) == "missing"
    assert assign_review_volume_tier(3, [10, 50]) == "<10"
    assert assign_review_volume_tier(10, [10, 50]) == "10-50"
    assert assign_review_volume_tier(50, [10, 50]) == "50+"


def test_write_parquet_rejects_banned_and_demographic_columns(tmp_path: Path) -> None:
    """Track E parquet writes must block banned output columns."""
    with pytest.raises(ValueError, match="review_text"):
        write_parquet(
            pd.DataFrame({"review_text": ["hello"]}),
            tmp_path / "bad_text.parquet",
        )

    with pytest.raises(ValueError, match="gender"):
        write_parquet(
            pd.DataFrame({"gender": ["x"]}),
            tmp_path / "bad_demo.parquet",
        )


def test_write_parquet_allows_clean_dataframes(tmp_path: Path) -> None:
    """Clean aggregate outputs should be written successfully."""
    out_path = tmp_path / "clean.parquet"

    write_parquet(
        pd.DataFrame({"subgroup_type": ["city"], "review_count": [12]}),
        out_path,
    )

    assert out_path.exists()
