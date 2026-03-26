"""Regression coverage for Track C/D and photo-intake dispatcher wiring."""

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


def test_track_c_track_d_and_photo_intake_are_registered() -> None:
    """Dispatcher should expose Track C/D and photo intake as approaches."""
    assert dispatcher.APPROACH_TRACK_C in dispatcher.APPROACH_CHOICES
    assert dispatcher.APPROACH_TRACK_D in dispatcher.APPROACH_CHOICES
    assert dispatcher.APPROACH_PHOTO_INTAKE in dispatcher.APPROACH_CHOICES
    assert dispatcher.APPROACH_TRACK_C in dispatcher.PIPELINES
    assert dispatcher.APPROACH_TRACK_D in dispatcher.PIPELINES
    assert dispatcher.APPROACH_PHOTO_INTAKE in dispatcher.PIPELINES


def test_photo_intake_pipeline_has_single_runtime_stage_with_contract_outputs() -> None:
    """Photo intake should run as an independent single-stage branch."""
    stages = dispatcher.PIPELINES[dispatcher.APPROACH_PHOTO_INTAKE]
    assert len(stages) == 1
    stage = stages[0]
    assert stage.stage_id == "photo_intake_runtime"
    assert stage.module == "src.multimodal.photo_intake"
    assert stage.config_path == "configs/multimodal.yaml"
    assert set(stage.required_outputs) == {
        "outputs/multimodal/photo_intake/manifest.json",
        "outputs/multimodal/photo_intake/validation_report.json",
        "outputs/multimodal/photo_intake/photo_metadata.parquet",
        "outputs/multimodal/photo_intake/image_path_manifest.parquet",
    }


def test_photo_intake_skips_shared_prerequisites_gate(tmp_path) -> None:
    """Photo intake should not force-run shared ingestion prerequisites."""
    state = {"approaches": {}}
    should_continue, exit_code, interpreter = dispatcher.maybe_run_shared_prerequisites(
        repo_root=tmp_path,
        state=state,
        state_path=tmp_path / "state.json",
        selected_approach=dispatcher.APPROACH_PHOTO_INTAKE,
        auto_yes=False,
        interpreter=None,
    )
    assert should_continue is True
    assert exit_code == 0
    assert interpreter is None


def test_track_d_pipeline_includes_leakage_hard_gate_stage() -> None:
    """Track D should stop on the blocking leakage stage before summary output."""
    track_d_stage_ids = [
        stage.stage_id for stage in dispatcher.PIPELINES[dispatcher.APPROACH_TRACK_D]
    ]
    assert "leakage_check" in track_d_stage_ids
    assert track_d_stage_ids[-2:] == ["leakage_check", "summary_report"]
