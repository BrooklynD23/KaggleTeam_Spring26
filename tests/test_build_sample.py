"""Unit tests for build_sample.py."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl
import pytest

from src.curate.build_sample import _stratified_sample, run


def test_stratified_sample_deterministic() -> None:
    """Same seed produces same sample."""
    df = pl.DataFrame({
        "id": range(100),
        "review_year": [2019] * 50 + [2020] * 50,
        "review_stars": [3] * 100,
    })
    a = _stratified_sample(df, ["review_year", "review_stars"], 20, seed=42)
    b = _stratified_sample(df, ["review_year", "review_stars"], 20, seed=42)
    assert a["id"].sort().to_list() == b["id"].sort().to_list()


def test_stratified_sample_preserves_strata() -> None:
    """Sample contains rows from each stratum."""
    df = pl.DataFrame({
        "id": range(100),
        "review_year": [2019] * 50 + [2020] * 50,
        "review_stars": [3] * 100,
    })
    out = _stratified_sample(df, ["review_year", "review_stars"], 20, seed=42)
    years = out["review_year"].unique().to_list()
    assert 2019 in years
    assert 2020 in years


def test_stratified_sample_size_capped() -> None:
    """Sample size does not exceed requested n."""
    df = pl.DataFrame({
        "id": range(50),
        "review_year": [2019] * 50,
        "review_stars": [3] * 50,
    })
    out = _stratified_sample(df, ["review_year", "review_stars"], 100, seed=42)
    assert len(out) == 50


def test_build_sample_integration(tmp_path: Path) -> None:
    """Full run with minimal curated data: ID filtering, manifest, metadata copy."""
    curated = tmp_path / "curated"
    curated.mkdir()
    sample_dir = tmp_path / "sample"
    sample_dir.mkdir()

    # Minimal review_fact
    rf = pl.DataFrame({
        "review_id": ["r1", "r2", "r3", "r4", "r5"],
        "user_id": ["u1", "u2", "u1", "u3", "u2"],
        "business_id": ["b1", "b2", "b1", "b3", "b2"],
        "review_year": [2019, 2019, 2020, 2020, 2020],
        "review_stars": [3.0, 4.0, 3.0, 5.0, 4.0],
    })
    rf.write_parquet(curated / "review_fact.parquet", compression="zstd")

    # review_fact_track_b (superset)
    rftb = rf.with_columns(pl.lit(1).alias("is_open"), pl.lit(0).alias("fans"))
    rftb.write_parquet(curated / "review_fact_track_b.parquet", compression="zstd")

    # Entity tables
    pl.DataFrame({"business_id": ["b1", "b2", "b3"], "city": ["A", "B", "C"]}).write_parquet(
        curated / "business.parquet", compression="zstd"
    )
    pl.DataFrame({"user_id": ["u1", "u2", "u3"], "name": ["x", "y", "z"]}).write_parquet(
        curated / "user.parquet", compression="zstd"
    )
    pl.DataFrame({
        "review_id": ["r1", "r2", "r3", "r4", "r5"],
        "text": ["a", "b", "c", "d", "e"],
    }).write_parquet(curated / "review.parquet", compression="zstd")
    pl.DataFrame({
        "business_id": ["b1"], "user_id": ["u1"], "text": ["tip"],
    }).write_parquet(curated / "tip.parquet", compression="zstd")
    pl.DataFrame({"business_id": ["b1", "b2"], "checkin_dates": ["2020-01-01", "2020-01-02"]}).write_parquet(
        curated / "checkin.parquet", compression="zstd"
    )
    pl.DataFrame({"business_id": ["b1"], "checkin_date": ["2020-01-01"]}).write_parquet(
        curated / "checkin_expanded.parquet", compression="zstd"
    )

    with open(curated / "snapshot_metadata.json", "w") as f:
        json.dump({"snapshot_reference_date": "2022-01-19"}, f)

    config = {
        "paths": {"curated_dir": str(curated), "logs_dir": str(tmp_path / "logs")},
        "sample": {"sample_dir": str(sample_dir), "sample_size": 3, "sample_strata": ["review_year", "review_stars"]},
        "random_seed": 42,
    }

    run(config)

    # Manifest exists with row_counts
    manifest = json.loads((sample_dir / "sample_manifest.json").read_text())
    assert "sample_size" in manifest
    assert "row_counts" in manifest
    assert manifest["row_counts"]["review_fact"] == 3

    # review_fact_track_b retained (semi-join)
    rftb_out = pl.read_parquet(sample_dir / "review_fact_track_b.parquet")
    rf_out = pl.read_parquet(sample_dir / "review_fact.parquet")
    assert set(rftb_out["review_id"].to_list()) == set(rf_out["review_id"].to_list())

    # ID filtering: business only has sampled business_ids
    biz_out = pl.read_parquet(sample_dir / "business.parquet")
    sampled_biz = set(rf_out["business_id"].to_list())
    assert set(biz_out["business_id"].to_list()).issubset(sampled_biz)

    # snapshot_metadata copied
    assert (sample_dir / "snapshot_metadata.json").is_file()
    meta = json.loads((sample_dir / "snapshot_metadata.json").read_text())
    assert meta["snapshot_reference_date"] == "2022-01-19"
