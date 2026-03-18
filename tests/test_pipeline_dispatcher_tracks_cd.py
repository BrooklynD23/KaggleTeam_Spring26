"""Regression coverage for Track C/D dispatcher wiring."""

from __future__ import annotations

from scripts import pipeline_dispatcher as dispatcher


def test_required_imports_include_langdetect() -> None:
    """Track C language profiling must be dependency-gated by the dispatcher."""
    assert "langdetect" in dispatcher.REQUIRED_IMPORTS


def test_shared_build_review_fact_outputs_cover_all_curated_dependencies() -> None:
    """Shared curation must verify artifacts consumed by Tracks C and D."""
    shared_stage = next(
        stage
        for stage in dispatcher.PIPELINES[dispatcher.APPROACH_SHARED]
        if stage.stage_id == "build_review_fact"
    )
    outputs = set(shared_stage.required_outputs)
    assert "data/curated/user.parquet" in outputs
    assert "data/curated/tip.parquet" in outputs
    assert "data/curated/checkin.parquet" in outputs
    assert "data/curated/checkin_expanded.parquet" in outputs


def test_track_c_and_track_d_are_registered() -> None:
    """Dispatcher should expose Track C/D as first-class approaches."""
    assert dispatcher.APPROACH_TRACK_C in dispatcher.APPROACH_CHOICES
    assert dispatcher.APPROACH_TRACK_D in dispatcher.APPROACH_CHOICES
    assert dispatcher.APPROACH_TRACK_C in dispatcher.PIPELINES
    assert dispatcher.APPROACH_TRACK_D in dispatcher.PIPELINES


def test_track_d_pipeline_includes_leakage_hard_gate_stage() -> None:
    """Track D should stop on the blocking leakage stage before summary output."""
    track_d_stage_ids = [
        stage.stage_id for stage in dispatcher.PIPELINES[dispatcher.APPROACH_TRACK_D]
    ]
    assert "leakage_check" in track_d_stage_ids
    assert track_d_stage_ids[-2:] == ["leakage_check", "summary_report"]
