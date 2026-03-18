"""Regression tests for Track D leakage hard-gate behavior."""

from __future__ import annotations
from pathlib import Path

import duckdb
import pandas as pd
import pytest

from src.eda.track_d.common import TrackDPaths
from src.eda.track_d.leakage_check import (
    _check_candidate_contamination,
    _check_parquet_schemas,
    maybe_raise_on_failures,
)


def test_maybe_raise_on_failures_blocks_when_hard_gate_enabled() -> None:
    report_df = pd.DataFrame(
        [
            {"finding_name": "alpha", "status": "PASS"},
            {"finding_name": "beta", "status": "FAIL"},
        ]
    )

    with pytest.raises(RuntimeError, match="beta"):
        maybe_raise_on_failures(report_df, hard_gate=True)


def test_maybe_raise_on_failures_allows_failures_when_gate_disabled() -> None:
    report_df = pd.DataFrame(
        [
            {"finding_name": "beta", "status": "FAIL"},
        ]
    )

    maybe_raise_on_failures(report_df, hard_gate=False)


def _make_paths(tmp_path: Path) -> TrackDPaths:
    tables_dir = tmp_path / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)
    return TrackDPaths(
        curated_dir=tmp_path / "curated",
        tables_dir=tables_dir,
        figures_dir=tmp_path / "figures",
        logs_dir=tmp_path / "logs",
        review_fact_path=tmp_path / "curated" / "review_fact.parquet",
        business_path=tmp_path / "curated" / "business.parquet",
        tip_path=tmp_path / "curated" / "tip.parquet",
        checkin_path=tmp_path / "curated" / "checkin.parquet",
        checkin_expanded_path=tmp_path / "curated" / "checkin_expanded.parquet",
    )


def test_check_parquet_schemas_flags_banned_column(tmp_path: Path) -> None:
    """Schema scanner must flag parquet files that contain banned output columns."""
    paths = _make_paths(tmp_path)
    bad_artifact = paths.tables_dir / "track_d_s2_business_cold_start_cohort.parquet"
    pd.DataFrame({"business_id": ["b1"], "stars": [4.5]}).to_parquet(bad_artifact, index=False)

    con = duckdb.connect()
    try:
        findings = _check_parquet_schemas(con, paths)
    finally:
        con.close()

    failed = [f for f in findings if f["status"] == "FAIL"]
    assert failed, "Expected at least one FAIL finding for the banned column 'stars'"
    assert any("stars" in f["detail"] for f in failed)


def test_check_candidate_contamination_flags_seen_candidates(tmp_path: Path) -> None:
    """Contamination scanner must flag candidates where was_seen_previously is True."""
    paths = _make_paths(tmp_path)
    members_path = paths.tables_dir / "track_d_s7_eval_candidate_members.parquet"
    pd.DataFrame(
        [
            {"candidate_business_id": "b1", "was_seen_previously": False},
            {"candidate_business_id": "b2", "was_seen_previously": True},
        ]
    ).to_parquet(members_path, index=False)

    con = duckdb.connect()
    try:
        findings = _check_candidate_contamination(con, paths)
    finally:
        con.close()

    failed = [f for f in findings if f["status"] == "FAIL"]
    assert failed, "Expected FAIL when was_seen_previously=True candidates exist"
    assert any("1" in f["detail"] for f in failed)
