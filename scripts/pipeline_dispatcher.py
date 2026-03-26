#!/usr/bin/env python3
"""Interactive orchestrator for the shared, Track A, and Track B pipelines."""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

APPROACH_SHARED = "shared"
APPROACH_TRACK_A = "track_a"
APPROACH_TRACK_B = "track_b"
APPROACH_TRACK_C = "track_c"
APPROACH_TRACK_D = "track_d"
APPROACH_TRACK_E = "track_e"
APPROACH_PHOTO_INTAKE = "photo_intake"
APPROACH_CHOICES = (
    APPROACH_SHARED,
    APPROACH_TRACK_A,
    APPROACH_TRACK_B,
    APPROACH_TRACK_C,
    APPROACH_TRACK_D,
    APPROACH_TRACK_E,
    APPROACH_PHOTO_INTAKE,
)

REPO_ROOT_MARKERS = (
    ("requirements.txt", "file"),
    ("configs/base.yaml", "file"),
    ("src", "dir"),
)

REQUIRED_IMPORTS = (
    "duckdb",
    "pandas",
    "polars",
    "pyarrow",
    "matplotlib",
    "seaborn",
    "scipy",
    "sklearn",
    "textblob",
    "langdetect",
    "yaml",
)

STATE_RELATIVE_PATH = Path("outputs/logs/orchestrator/state.json")
ORCHESTRATOR_ROOT_RELATIVE = Path("outputs/logs/orchestrator")
RUNTIME_WINDOWS = "windows"
RUNTIME_WSL = "wsl"
RUNTIME_LINUX = "linux"

SCHEMA_CHECKS_WRAPPER = """
import logging
import sys

from pathlib import Path

repo_root = Path(sys.argv[1])
config_path = sys.argv[2]
sys.path.insert(0, str(repo_root))

from src.common.config import load_config
from src.validate.schema_checks import run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

config = load_config(config_path)
log_level = str(config.get("log_level", "INFO")).upper()
logging.getLogger().setLevel(getattr(logging, log_level, logging.INFO))

reports = run(config)
if any(getattr(report, "status", None) == "FAIL" for report in reports):
    logging.error("Schema checks failed; exiting non-zero.")
    raise SystemExit(1)
"""


class DispatcherError(RuntimeError):
    """Raised when the dispatcher cannot continue safely."""


@dataclass(frozen=True)
class StageDefinition:
    """Static definition for one pipeline stage."""

    stage_id: str
    runner: str
    config_path: str
    required_outputs: tuple[str, ...]
    module: str | None = None


@dataclass(frozen=True)
class StageAssessment:
    """Current completion state for one stage."""

    stage: StageDefinition
    outputs_exist: bool
    state_status: str | None
    complete: bool


@dataclass(frozen=True)
class PipelineAssessment:
    """Assessment of a full pipeline approach."""

    approach: str
    stages: tuple[StageAssessment, ...]

    @property
    def first_incomplete_index(self) -> int | None:
        for index, assessment in enumerate(self.stages):
            if not assessment.complete:
                return index
        return None

    @property
    def all_complete(self) -> bool:
        return self.first_incomplete_index is None

    @property
    def any_complete(self) -> bool:
        return any(stage.complete for stage in self.stages)


@dataclass(frozen=True)
class RunDecision:
    """Execution decision for a selected approach."""

    should_run: bool
    start_index: int | None = None


PIPELINES: dict[str, tuple[StageDefinition, ...]] = {
    APPROACH_SHARED: (
        StageDefinition(
            stage_id="load_yelp_json",
            runner="module",
            module="src.ingest.load_yelp_json",
            config_path="configs/base.yaml",
            required_outputs=("data/yelp.duckdb",),
        ),
        StageDefinition(
            stage_id="schema_checks",
            runner="schema_checks",
            config_path="configs/base.yaml",
            required_outputs=(
                "outputs/logs/orchestrator/shared/schema_checks.ok.json",
            ),
        ),
        StageDefinition(
            stage_id="build_review_fact",
            runner="module",
            module="src.curate.build_review_fact",
            config_path="configs/base.yaml",
            required_outputs=(
                "data/curated/review_fact.parquet",
                "data/curated/review_fact_track_b.parquet",
                "data/curated/review.parquet",
                "data/curated/business.parquet",
                "data/curated/user.parquet",
                "data/curated/tip.parquet",
                "data/curated/checkin.parquet",
                "data/curated/checkin_expanded.parquet",
                "data/curated/snapshot_metadata.json",
            ),
        ),
    ),
    APPROACH_TRACK_A: (
        StageDefinition(
            stage_id="temporal_profile",
            runner="module",
            module="src.eda.track_a.temporal_profile",
            config_path="configs/track_a.yaml",
            required_outputs=(
                "outputs/tables/track_a_s1_stars_by_year_month.parquet",
                "outputs/tables/track_a_s1_review_volume_by_period.parquet",
                "outputs/figures/track_a_s1_star_distribution_over_time.png",
                "outputs/figures/track_a_s1_review_volume_timeline.png",
            ),
        ),
        StageDefinition(
            stage_id="text_profile",
            runner="module",
            module="src.eda.track_a.text_profile",
            config_path="configs/track_a.yaml",
            required_outputs=(
                "outputs/tables/track_a_s2_text_length_stats.parquet",
                "outputs/figures/track_a_s2_text_length_by_star.png",
                "outputs/figures/track_a_s2_text_length_distribution.png",
            ),
        ),
        StageDefinition(
            stage_id="user_history_profile",
            runner="module",
            module="src.eda.track_a.user_history_profile",
            config_path="configs/track_a.yaml",
            required_outputs=(
                "outputs/tables/track_a_s3_user_history_asof.parquet",
                "outputs/tables/track_a_s3_business_history_asof.parquet",
                "outputs/tables/track_a_s3_user_history_depth.parquet",
                "outputs/figures/track_a_s3_user_prior_review_count_dist.png",
                "outputs/figures/track_a_s3_user_tenure_vs_rating_var.png",
            ),
        ),
        StageDefinition(
            stage_id="business_attr_profile",
            runner="module",
            module="src.eda.track_a.business_attr_profile",
            config_path="configs/track_a.yaml",
            required_outputs=(
                "outputs/tables/track_a_s4_attr_completeness_by_category.parquet",
                "outputs/tables/track_a_s4_attr_completeness_by_city.parquet",
                "outputs/figures/track_a_s4_attr_null_rate_heatmap.png",
            ),
        ),
        StageDefinition(
            stage_id="split_selection",
            runner="module",
            module="src.eda.track_a.split_selection",
            config_path="configs/track_a.yaml",
            required_outputs=(
                "outputs/tables/track_a_s5_candidate_splits.parquet",
                "outputs/tables/track_a_s5_split_star_balance.parquet",
                "outputs/figures/track_a_s5_split_comparison.png",
            ),
        ),
        StageDefinition(
            stage_id="leakage_audit",
            runner="module",
            module="src.eda.track_a.leakage_audit",
            config_path="configs/track_a.yaml",
            required_outputs=(
                "outputs/tables/track_a_s6_leakage_report.parquet",
                "outputs/logs/track_a_s6_leakage_audit.log",
            ),
        ),
        StageDefinition(
            stage_id="feature_availability",
            runner="module",
            module="src.eda.track_a.feature_availability",
            config_path="configs/track_a.yaml",
            required_outputs=(
                "outputs/tables/track_a_s7_feature_availability.parquet",
                "outputs/figures/track_a_s7_feature_coverage_bars.png",
            ),
        ),
        StageDefinition(
            stage_id="summary_report",
            runner="module",
            module="src.eda.track_a.summary_report",
            config_path="configs/track_a.yaml",
            required_outputs=("outputs/tables/track_a_s8_eda_summary.md",),
        ),
    ),
    APPROACH_TRACK_B: (
        StageDefinition(
            stage_id="usefulness_distribution",
            runner="module",
            module="src.eda.track_b.usefulness_distribution",
            config_path="configs/track_b.yaml",
            required_outputs=(
                "outputs/tables/track_b_s1_useful_vote_distribution.parquet",
                "outputs/tables/track_b_s1_bucket_summary.parquet",
                "outputs/tables/track_b_s1_category_zero_fraction.parquet",
                "outputs/tables/track_b_s1_age_distribution.parquet",
                "outputs/figures/track_b_s1_useful_histogram.png",
                "outputs/figures/track_b_s1_zero_fraction_by_category.png",
            ),
        ),
        StageDefinition(
            stage_id="age_confounding",
            runner="module",
            module="src.eda.track_b.age_confounding",
            config_path="configs/track_b.yaml",
            required_outputs=(
                "outputs/tables/track_b_s2_age_effect_summary.parquet",
                "outputs/figures/track_b_s2_useful_by_age_bucket.png",
                "outputs/figures/track_b_s2_textlen_vs_useful_within_age.png",
            ),
        ),
        StageDefinition(
            stage_id="ranking_group_analysis",
            runner="module",
            module="src.eda.track_b.ranking_group_analysis",
            config_path="configs/track_b.yaml",
            required_outputs=(
                "outputs/tables/track_b_s3_group_sizes_by_business_age.parquet",
                "outputs/tables/track_b_s3_group_sizes_by_category_age.parquet",
                "outputs/figures/track_b_s3_group_size_distribution.png",
            ),
        ),
        StageDefinition(
            stage_id="label_construction",
            runner="module",
            module="src.eda.track_b.label_construction",
            config_path="configs/track_b.yaml",
            required_outputs=(
                "outputs/tables/track_b_s4_label_candidates.parquet",
                "outputs/tables/track_b_s4_label_scheme_summary.parquet",
            ),
        ),
        StageDefinition(
            stage_id="feature_correlates",
            runner="module",
            module="src.eda.track_b.feature_correlates",
            config_path="configs/track_b.yaml",
            required_outputs=(
                "outputs/tables/track_b_s5_feature_correlates.parquet",
                "outputs/figures/track_b_s5_stars_vs_useful_within_age.png",
                "outputs/figures/track_b_s5_elite_vs_useful_within_age.png",
            ),
        ),
        StageDefinition(
            stage_id="training_feasibility",
            runner="module",
            module="src.eda.track_b.training_feasibility",
            config_path="configs/track_b.yaml",
            required_outputs=(
                "outputs/tables/track_b_s6_pairwise_stats.parquet",
                "outputs/tables/track_b_s6_listwise_stats.parquet",
            ),
        ),
        StageDefinition(
            stage_id="leakage_scope_check",
            runner="module",
            module="src.eda.track_b.leakage_scope_check",
            config_path="configs/track_b.yaml",
            required_outputs=(
                "outputs/tables/track_b_s7_leakage_scope_report.parquet",
                "outputs/logs/track_b_s7_leakage_scope_check.log",
            ),
        ),
        StageDefinition(
            stage_id="summary_report",
            runner="module",
            module="src.eda.track_b.summary_report",
            config_path="configs/track_b.yaml",
            required_outputs=("outputs/tables/track_b_s8_eda_summary.md",),
        ),
    ),
    APPROACH_TRACK_C: (
        StageDefinition(
            stage_id="geo_coverage",
            runner="module",
            module="src.eda.track_c.geo_coverage",
            config_path="configs/track_c.yaml",
            required_outputs=(
                "outputs/tables/track_c_s1_city_coverage.parquet",
                "outputs/tables/track_c_s1_state_coverage.parquet",
                "outputs/tables/track_c_s1_city_variant_diagnostic.parquet",
                "outputs/figures/track_c_s1_city_review_count_bar.png",
                "outputs/figures/track_c_s1_coverage_map.png",
            ),
        ),
        StageDefinition(
            stage_id="temporal_binning",
            runner="module",
            module="src.eda.track_c.temporal_binning",
            config_path="configs/track_c.yaml",
            required_outputs=(
                "outputs/tables/track_c_s2_review_volume_by_month.parquet",
                "outputs/tables/track_c_s2_review_volume_by_quarter.parquet",
                "outputs/figures/track_c_s2_volume_timeline.png",
            ),
        ),
        StageDefinition(
            stage_id="text_normalization",
            runner="module",
            module="src.eda.track_c.text_normalization",
            config_path="configs/track_c.yaml",
            required_outputs=(
                "outputs/tables/track_c_s3_text_stats.parquet",
                "outputs/tables/track_c_s3_language_detection.parquet",
            ),
        ),
        StageDefinition(
            stage_id="sentiment_baseline",
            runner="module",
            module="src.eda.track_c.sentiment_baseline",
            config_path="configs/track_c.yaml",
            required_outputs=(
                "outputs/tables/track_c_s4_sentiment_by_city_month.parquet",
                "outputs/figures/track_c_s4_sentiment_vs_stars.png",
                "outputs/figures/track_c_s4_sentiment_timeseries_top_cities.png",
            ),
        ),
        StageDefinition(
            stage_id="topic_prevalence",
            runner="module",
            module="src.eda.track_c.topic_prevalence",
            config_path="configs/track_c.yaml",
            required_outputs=(
                "outputs/tables/track_c_s5_keyword_trends.parquet",
                "outputs/tables/track_c_s5_tfidf_cluster_summary.parquet",
                "outputs/figures/track_c_s5_keyword_trend_lines.png",
            ),
        ),
        StageDefinition(
            stage_id="drift_detection",
            runner="module",
            module="src.eda.track_c.drift_detection",
            config_path="configs/track_c.yaml",
            required_outputs=(
                "outputs/tables/track_c_s6_sentiment_drift_by_city.parquet",
                "outputs/tables/track_c_s6_topic_drift_by_city.parquet",
                "outputs/figures/track_c_s6_drift_heatmap.png",
            ),
        ),
        StageDefinition(
            stage_id="event_candidates",
            runner="module",
            module="src.eda.track_c.event_candidates",
            config_path="configs/track_c.yaml",
            required_outputs=(
                "outputs/tables/track_c_s7_business_lifecycle.parquet",
                "outputs/tables/track_c_s7_event_candidates.parquet",
                "outputs/figures/track_c_s7_open_close_timeline.png",
            ),
        ),
        StageDefinition(
            stage_id="checkin_correlation",
            runner="module",
            module="src.eda.track_c.checkin_correlation",
            config_path="configs/track_c.yaml",
            required_outputs=(
                "outputs/tables/track_c_s8_checkin_volume_monthly.parquet",
                "outputs/tables/track_c_s8_checkin_sentiment_correlation.parquet",
                "outputs/figures/track_c_s8_checkin_vs_sentiment.png",
            ),
        ),
        StageDefinition(
            stage_id="summary_report",
            runner="module",
            module="src.eda.track_c.summary_report",
            config_path="configs/track_c.yaml",
            required_outputs=("outputs/tables/track_c_s9_eda_summary.md",),
        ),
    ),
    APPROACH_TRACK_D: (
        StageDefinition(
            stage_id="business_lifecycle",
            runner="module",
            module="src.eda.track_d.business_lifecycle",
            config_path="configs/track_d.yaml",
            required_outputs=(
                "outputs/tables/track_d_s1_business_lifecycle.parquet",
                "outputs/figures/track_d_s1_review_accrual_curves.png",
                "outputs/figures/track_d_s1_days_to_nth_review.png",
            ),
        ),
        StageDefinition(
            stage_id="business_cold_start",
            runner="module",
            module="src.eda.track_d.business_cold_start",
            config_path="configs/track_d.yaml",
            required_outputs=(
                "outputs/tables/track_d_s2_business_cold_start_cohort.parquet",
                "outputs/tables/track_d_s2_business_cohort_size_by_threshold.parquet",
                "outputs/figures/track_d_s2_business_cohort_sizes.png",
            ),
        ),
        StageDefinition(
            stage_id="business_early_signals",
            runner="module",
            module="src.eda.track_d.business_early_signals",
            config_path="configs/track_d.yaml",
            required_outputs=(
                "outputs/tables/track_d_s3_business_early_signals.parquet",
                "outputs/tables/track_d_s3_business_signal_summary.parquet",
            ),
        ),
        StageDefinition(
            stage_id="popularity_baseline",
            runner="module",
            module="src.eda.track_d.popularity_baseline",
            config_path="configs/track_d.yaml",
            required_outputs=(
                "outputs/tables/track_d_s4_popularity_baseline_asof.parquet",
                "outputs/figures/track_d_s4_popularity_concentration.png",
            ),
        ),
        StageDefinition(
            stage_id="user_cold_start",
            runner="module",
            module="src.eda.track_d.user_cold_start",
            config_path="configs/track_d.yaml",
            required_outputs=(
                "outputs/tables/track_d_s5_user_cold_start_cohort.parquet",
                "outputs/figures/track_d_s5_user_activity_ramp.png",
                "outputs/figures/track_d_s5_first_k_review_behavior.png",
            ),
        ),
        StageDefinition(
            stage_id="user_warmup_profile",
            runner="module",
            module="src.eda.track_d.user_warmup_profile",
            config_path="configs/track_d.yaml",
            required_outputs=(
                "outputs/tables/track_d_s6_user_warmup_profile.parquet",
                "outputs/tables/track_d_s6_user_feature_coverage.parquet",
            ),
        ),
        StageDefinition(
            stage_id="evaluation_cohorts",
            runner="module",
            module="src.eda.track_d.evaluation_cohorts",
            config_path="configs/track_d.yaml",
            required_outputs=(
                "outputs/tables/track_d_s7_eval_cohorts.parquet",
                "outputs/tables/track_d_s7_eval_cohort_summary.parquet",
                "outputs/tables/track_d_s7_eval_candidate_members.parquet",
            ),
        ),
        StageDefinition(
            stage_id="leakage_check",
            runner="module",
            module="src.eda.track_d.leakage_check",
            config_path="configs/track_d.yaml",
            required_outputs=(
                "outputs/tables/track_d_s8_leakage_report.parquet",
                "outputs/logs/track_d_s8_leakage_check.log",
            ),
        ),
        StageDefinition(
            stage_id="summary_report",
            runner="module",
            module="src.eda.track_d.summary_report",
            config_path="configs/track_d.yaml",
            required_outputs=("outputs/tables/track_d_s9_eda_summary.md",),
        ),
    ),
    APPROACH_TRACK_E: (
        StageDefinition(
            stage_id="subgroup_definition",
            runner="module",
            module="src.eda.track_e.subgroup_definition",
            config_path="configs/track_e.yaml",
            required_outputs=(
                "outputs/tables/track_e_s1_subgroup_definitions.parquet",
                "outputs/tables/track_e_s1_subgroup_summary.parquet",
                "outputs/tables/track_e_s1_price_tier_diagnostic.parquet",
            ),
        ),
        StageDefinition(
            stage_id="coverage_profile",
            runner="module",
            module="src.eda.track_e.coverage_profile",
            config_path="configs/track_e.yaml",
            required_outputs=(
                "outputs/tables/track_e_s2_coverage_by_subgroup.parquet",
                "outputs/figures/track_e_s2_coverage_by_city.png",
                "outputs/figures/track_e_s2_coverage_by_category.png",
                "outputs/figures/track_e_s2_coverage_by_price.png",
            ),
        ),
        StageDefinition(
            stage_id="star_disparity",
            runner="module",
            module="src.eda.track_e.star_disparity",
            config_path="configs/track_e.yaml",
            required_outputs=(
                "outputs/tables/track_e_s3_star_disparity.parquet",
                "outputs/tables/track_e_s3_ks_test_results.parquet",
                "outputs/figures/track_e_s3_star_dist_by_category.png",
                "outputs/figures/track_e_s3_star_dist_by_price.png",
                "outputs/figures/track_e_s3_star_dist_by_city.png",
            ),
        ),
        StageDefinition(
            stage_id="usefulness_disparity",
            runner="module",
            module="src.eda.track_e.usefulness_disparity",
            config_path="configs/track_e.yaml",
            required_outputs=(
                "outputs/tables/track_e_s4_usefulness_disparity.parquet",
                "outputs/figures/track_e_s4_useful_by_subgroup.png",
            ),
        ),
        StageDefinition(
            stage_id="imbalance_analysis",
            runner="module",
            module="src.eda.track_e.imbalance_analysis",
            config_path="configs/track_e.yaml",
            required_outputs=(
                "outputs/tables/track_e_s5_imbalance_report.parquet",
                "outputs/figures/track_e_s5_lorenz_curve.png",
                "outputs/figures/track_e_s5_gini_by_dimension.png",
            ),
        ),
        StageDefinition(
            stage_id="proxy_risk",
            runner="module",
            module="src.eda.track_e.proxy_risk",
            config_path="configs/track_e.yaml",
            required_outputs=(
                "outputs/tables/track_e_s6_proxy_correlations.parquet",
                "outputs/figures/track_e_s6_proxy_heatmap.png",
            ),
        ),
        StageDefinition(
            stage_id="fairness_baseline",
            runner="module",
            module="src.eda.track_e.fairness_baseline",
            config_path="configs/track_e.yaml",
            required_outputs=(
                "outputs/tables/track_e_s7_fairness_metrics.parquet",
            ),
        ),
        StageDefinition(
            stage_id="mitigation_candidates",
            runner="module",
            module="src.eda.track_e.mitigation_candidates",
            config_path="configs/track_e.yaml",
            required_outputs=(
                "outputs/tables/track_e_s8_mitigation_candidates.md",
            ),
        ),
        StageDefinition(
            stage_id="summary_report",
            runner="module",
            module="src.eda.track_e.summary_report",
            config_path="configs/track_e.yaml",
            required_outputs=(
                "outputs/tables/track_e_s9_eda_summary.md",
                "outputs/logs/track_e_s9_validity_scan.log",
            ),
        ),
    ),
    APPROACH_PHOTO_INTAKE: (
        StageDefinition(
            stage_id="photo_intake_runtime",
            runner="module",
            module="src.multimodal.photo_intake",
            config_path="configs/multimodal.yaml",
            required_outputs=(
                "outputs/multimodal/photo_intake/manifest.json",
                "outputs/multimodal/photo_intake/validation_report.json",
                "outputs/multimodal/photo_intake/photo_metadata.parquet",
                "outputs/multimodal/photo_intake/image_path_manifest.parquet",
            ),
        ),
    ),
}


def utc_now_iso() -> str:
    """Return the current UTC time in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def detect_runtime() -> str:
    """Return the current host runtime family."""
    if os.name == "nt":
        return RUNTIME_WINDOWS

    release = platform.uname().release.lower()
    if "microsoft" in release or os.environ.get("WSL_INTEROP"):
        return RUNTIME_WSL
    return RUNTIME_LINUX


def venv_dir_name_for_runtime(runtime: str) -> str:
    """Return the repo-local virtualenv directory name for a runtime."""
    mapping = {
        RUNTIME_WINDOWS: ".venv-win",
        RUNTIME_WSL: ".venv-wsl",
        RUNTIME_LINUX: ".venv-linux",
    }
    try:
        return mapping[runtime]
    except KeyError as exc:
        raise DispatcherError(f"Unsupported runtime '{runtime}'.") from exc


def resolve_venv_python(path: Path, runtime: str) -> Path | None:
    """Return the venv interpreter for the current runtime."""
    if runtime == RUNTIME_WINDOWS:
        candidates = (
            path / "Scripts" / "python.exe",
            path / "Scripts" / "python",
            path / "python.exe",
            path / "python",
        )
    else:
        candidates = (
            path / "bin" / "python",
            path / "bin" / "python3",
            path / "python",
        )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def assert_interpreter_matches_runtime(interpreter: Path, runtime: str) -> None:
    """Fail fast when the selected interpreter looks like the wrong runtime family."""
    interpreter_str = str(interpreter)
    normalized = interpreter_str.replace("\\", "/")
    looks_windows = (
        "\\" in interpreter_str
        or interpreter_str.lower().endswith(".exe")
        or (interpreter.drive != "")
    )
    looks_posix = normalized.startswith("/")

    if runtime == RUNTIME_WINDOWS and looks_posix:
        raise DispatcherError(
            "Detected Windows runtime with a POSIX-style interpreter path. "
            "Use the Windows launcher or a Windows virtualenv."
        )

    if runtime in {RUNTIME_WSL, RUNTIME_LINUX} and looks_windows:
        raise DispatcherError(
            "Detected POSIX runtime with a Windows-style interpreter path. "
            "Use the WSL/Linux launcher or a POSIX virtualenv."
        )

    if runtime in {RUNTIME_WSL, RUNTIME_LINUX} and not looks_posix:
        raise DispatcherError(
            "Detected POSIX runtime with a non-POSIX interpreter path. "
            "Use the matching POSIX virtualenv."
        )


def discover_repo_root() -> Path:
    """Find the repo root regardless of the current working directory."""
    candidates: list[Path] = []
    script_path = Path(__file__).resolve()
    candidates.extend([script_path.parent, script_path.parent.parent, Path.cwd().resolve()])

    seen: set[Path] = set()
    for base in candidates:
        for candidate in (base, *base.parents):
            if candidate in seen:
                continue
            seen.add(candidate)
            if is_repo_root(candidate):
                return candidate

    raise DispatcherError(
        "Could not locate the repo root. Expected requirements.txt, configs/base.yaml, and src/."
    )


def is_repo_root(path: Path) -> bool:
    """Return True when the path looks like the expected repo root."""
    for relative, kind in REPO_ROOT_MARKERS:
        candidate = path / relative
        if kind == "file" and not candidate.is_file():
            return False
        if kind == "dir" and not candidate.is_dir():
            return False
    return True


def ensure_tty(prompt_context: str) -> None:
    """Fail fast when a prompt would be impossible."""
    if not sys.stdin.isatty():
        raise DispatcherError(
            f"{prompt_context} requires an interactive terminal. Re-run with --yes or explicit flags."
        )


def prompt_input(message: str) -> str:
    """Read one line of input from stdin."""
    ensure_tty("Prompting")
    try:
        return input(message).strip()
    except EOFError as exc:
        raise DispatcherError("Input was closed before a selection was provided.") from exc


def confirm(message: str, auto_yes: bool) -> bool:
    """Return True when the user confirms."""
    if auto_yes:
        print(f"{message} yes (via --yes)")
        return True
    response = prompt_input(message).lower()
    return response in {"y", "yes"}


def choose_approach() -> str:
    """Interactive approach selector."""
    ensure_tty("Selecting an approach")
    mapping = {
        "1": APPROACH_SHARED,
        "2": APPROACH_TRACK_A,
        "3": APPROACH_TRACK_B,
        "4": APPROACH_TRACK_C,
        "5": APPROACH_TRACK_D,
        "6": APPROACH_TRACK_E,
        "7": APPROACH_PHOTO_INTAKE,
        APPROACH_SHARED: APPROACH_SHARED,
        APPROACH_TRACK_A: APPROACH_TRACK_A,
        APPROACH_TRACK_B: APPROACH_TRACK_B,
        APPROACH_TRACK_C: APPROACH_TRACK_C,
        APPROACH_TRACK_D: APPROACH_TRACK_D,
        APPROACH_TRACK_E: APPROACH_TRACK_E,
        APPROACH_PHOTO_INTAKE: APPROACH_PHOTO_INTAKE,
    }

    while True:
        print("Select a pipeline approach:")
        print("  1) shared")
        print("  2) track_a")
        print("  3) track_b")
        print("  4) track_c")
        print("  5) track_d")
        print("  6) track_e")
        print("  7) photo_intake")
        print("  q) quit")
        choice = prompt_input("Choice: ").lower()
        if choice in {"q", "quit", "exit"}:
            raise SystemExit(0)
        if choice in mapping:
            return mapping[choice]
        print("Invalid selection. Choose 1, 2, 3, 4, 5, 6, 7, or q.")


def load_state(state_path: Path) -> dict[str, Any]:
    """Load state.json if present, otherwise return an empty state structure."""
    if not state_path.is_file():
        return {"approaches": {}}

    try:
        with open(state_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except json.JSONDecodeError as exc:
        raise DispatcherError(f"State file is not valid JSON: {state_path}") from exc

    if not isinstance(payload, dict):
        raise DispatcherError(f"State file must contain a JSON object: {state_path}")

    payload.setdefault("approaches", {})
    return payload


def save_state(state_path: Path, state: dict[str, Any]) -> None:
    """Persist state.json atomically."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = utc_now_iso()

    temp_path = state_path.with_suffix(f"{state_path.suffix}.tmp")
    with open(temp_path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
    temp_path.replace(state_path)


def get_stage_state(state: dict[str, Any], approach: str, stage_id: str) -> dict[str, Any]:
    """Return the nested state record for one stage, creating containers as needed."""
    approaches = state.setdefault("approaches", {})
    approach_state = approaches.setdefault(approach, {})
    stages = approach_state.setdefault("stages", {})
    return stages.setdefault(stage_id, {})


def peek_stage_state(state: dict[str, Any], approach: str, stage_id: str) -> dict[str, Any]:
    """Return the nested state record for one stage without mutating state."""
    approaches = state.get("approaches", {})
    if not isinstance(approaches, dict):
        return {}
    approach_state = approaches.get(approach, {})
    if not isinstance(approach_state, dict):
        return {}
    stages = approach_state.get("stages", {})
    if not isinstance(stages, dict):
        return {}
    stage_state = stages.get(stage_id, {})
    return stage_state if isinstance(stage_state, dict) else {}


def stage_outputs_exist(repo_root: Path, stage: StageDefinition) -> bool:
    """Return True when all declared completion artifacts exist."""
    return all((repo_root / relative).is_file() for relative in stage.required_outputs)


def assess_pipeline(repo_root: Path, state: dict[str, Any], approach: str) -> PipelineAssessment:
    """Assess the current completion state for an approach."""
    stage_assessments: list[StageAssessment] = []
    for stage in PIPELINES[approach]:
        stage_state = peek_stage_state(state, approach, stage.stage_id)
        outputs_exist = stage_outputs_exist(repo_root, stage)
        state_status = stage_state.get("status")
        complete = outputs_exist and state_status not in {"failed", "running"}
        stage_assessments.append(
            StageAssessment(
                stage=stage,
                outputs_exist=outputs_exist,
                state_status=str(state_status) if state_status is not None else None,
                complete=complete,
            )
        )
    return PipelineAssessment(approach=approach, stages=tuple(stage_assessments))


def render_status_table(assessment: PipelineAssessment) -> None:
    """Print the required status table for partial pipelines."""
    if assessment.all_complete or not assessment.any_complete:
        return

    first_incomplete = assessment.first_incomplete_index
    assert first_incomplete is not None

    rows: list[tuple[str, str]] = []
    for index, stage in enumerate(assessment.stages):
        if index < first_incomplete:
            status = "complete"
        elif index == first_incomplete:
            status = "missing"
        else:
            status = "blocked"
        rows.append((stage.stage.stage_id, status))

    stage_width = max(len("stage"), *(len(stage_id) for stage_id, _ in rows))
    print(f"Status for {assessment.approach}:")
    print(f"{'stage'.ljust(stage_width)}  status")
    print(f"{'-' * stage_width}  ------")
    for stage_id, status in rows:
        print(f"{stage_id.ljust(stage_width)}  {status}")


def stage_index_for(approach: str, stage_id: str) -> int:
    """Return the ordinal index for a stage id in its approach."""
    for index, stage in enumerate(PIPELINES[approach]):
        if stage.stage_id == stage_id:
            return index
    valid = ", ".join(stage.stage_id for stage in PIPELINES[approach])
    raise DispatcherError(
        f"Unknown stage '{stage_id}' for {approach}. Valid stage ids: {valid}"
    )


def completed_stage_ids_from(
    assessment: PipelineAssessment,
    start_index: int,
) -> list[str]:
    """Return complete stages that would be rerun from the given start index."""
    return [
        stage.stage.stage_id
        for stage in assessment.stages[start_index:]
        if stage.complete
    ]


def prompt_completed_approach_action(
    approach: str,
    auto_yes: bool,
) -> RunDecision:
    """Handle the already-complete case with the exact required options."""
    if auto_yes:
        print(f"{approach} is already complete. Defaulting to 'skip' because --yes was supplied.")
        return RunDecision(should_run=False)

    print(f"{approach} is already complete. Choose one:")
    print("skip")
    print("rerun from stage")
    print("rerun full approach")
    selection = prompt_input("Selection: ").lower()

    if selection == "skip":
        return RunDecision(should_run=False)
    if selection == "rerun full approach":
        if confirm(
            f"Rerun all completed stages for {approach}? [y/N]: ",
            auto_yes=False,
        ):
            return RunDecision(should_run=True, start_index=0)
        return RunDecision(should_run=False)
    if selection == "rerun from stage":
        valid_ids = ", ".join(stage.stage_id for stage in PIPELINES[approach])
        stage_id = prompt_input(f"Stage id to rerun ({valid_ids}): ")
        stage_start = stage_index_for(approach, stage_id)
        if confirm(
            f"Rerun {approach} from '{stage_id}' and overwrite downstream stage outputs? [y/N]: ",
            auto_yes=False,
        ):
            return RunDecision(should_run=True, start_index=stage_start)
        return RunDecision(should_run=False)

    print("Unrecognized selection; defaulting to skip.")
    return RunDecision(should_run=False)


def resolve_run_decision(
    repo_root: Path,
    state: dict[str, Any],
    approach: str,
    from_stage: str | None,
    auto_yes: bool,
) -> RunDecision:
    """Resolve whether the approach should run and from which stage."""
    assessment = assess_pipeline(repo_root, state, approach)

    if not assessment.all_complete and assessment.any_complete:
        render_status_table(assessment)

    if assessment.all_complete and from_stage is None:
        return prompt_completed_approach_action(approach, auto_yes)

    if from_stage is not None:
        start_index = stage_index_for(approach, from_stage)
        first_incomplete = assessment.first_incomplete_index
        if first_incomplete is not None and start_index > first_incomplete:
            blocked_by = assessment.stages[first_incomplete].stage.stage_id
            raise DispatcherError(
                f"Cannot start from '{from_stage}' because earlier stage '{blocked_by}' is incomplete."
            )

        rerun_completed = completed_stage_ids_from(assessment, start_index)
        if rerun_completed:
            if not confirm(
                "Rerun completed stages from "
                f"'{from_stage}' onward ({', '.join(rerun_completed)})? [y/N]: ",
                auto_yes,
            ):
                return RunDecision(should_run=False)
        return RunDecision(should_run=True, start_index=start_index)

    if assessment.all_complete:
        return RunDecision(should_run=False)

    first_incomplete = assessment.first_incomplete_index
    if first_incomplete is None:
        return RunDecision(should_run=False)

    if assessment.any_complete:
        earliest_missing = assessment.stages[first_incomplete].stage.stage_id
        rerun_completed = completed_stage_ids_from(assessment, first_incomplete)
        prompt = f"Continue from earliest missing stage '{earliest_missing}'?"
        if rerun_completed:
            prompt += f" This will rerun completed downstream stages: {', '.join(rerun_completed)}."
        prompt += " [y/N]: "
        if not confirm(prompt, auto_yes):
            return RunDecision(should_run=False)

    return RunDecision(should_run=True, start_index=first_incomplete)


def resolve_active_interpreter(repo_root: Path) -> Path:
    """Validate the current interpreter and return it for stage execution."""
    active_python = Path(sys.executable)
    if not active_python.is_file():
        raise DispatcherError("Active Python interpreter could not be resolved.")

    runtime = detect_runtime()
    assert_interpreter_matches_runtime(active_python, runtime)

    missing_imports = check_required_imports(active_python, repo_root)
    if missing_imports:
        expected_venv = repo_root / venv_dir_name_for_runtime(runtime)
        raise DispatcherError(
            "Required packages are missing from the active interpreter: "
            + ", ".join(missing_imports)
            + ". Use scripts/run_pipeline.py or install requirements into "
            + f"the runtime-matched environment ({expected_venv})."
        )
    return active_python


def check_required_imports(venv_python: Path, repo_root: Path) -> list[str]:
    """Return the list of required imports that are missing from the virtualenv."""
    script = (
        "import importlib.util, json; "
        f"mods = {list(REQUIRED_IMPORTS)!r}; "
        "missing = [name for name in mods if importlib.util.find_spec(name) is None]; "
        "print(json.dumps(missing))"
    )
    result = subprocess.run(
        [str(venv_python), "-c", script],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise DispatcherError(
            "Could not verify imports inside .venv: " + (result.stderr.strip() or result.stdout.strip())
        )
    try:
        payload = json.loads(result.stdout.strip() or "[]")
    except json.JSONDecodeError as exc:
        raise DispatcherError("Import check returned invalid JSON.") from exc
    if not isinstance(payload, list):
        raise DispatcherError("Import check did not return a list of missing modules.")
    return [str(name) for name in payload]


def run_command(
    command: list[str],
    cwd: Path,
    check: bool,
) -> subprocess.CompletedProcess[str]:
    """Run a simple subprocess command, streaming its output to this terminal."""
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env.setdefault("MPLBACKEND", "Agg")
    env["PYTHONPATH"] = str(cwd) + os.pathsep + env.get("PYTHONPATH", "")

    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise DispatcherError(
            f"Command failed with exit code {result.returncode}: {' '.join(command)}"
        )
    return result


def update_stage_state(
    state: dict[str, Any],
    state_path: Path,
    approach: str,
    stage: StageDefinition,
    *,
    status: str,
    interpreter: Path,
    log_path: Path,
    started_at: str | None = None,
    finished_at: str | None = None,
    exit_code: int | None = None,
    outputs_verified: bool | None = None,
) -> None:
    """Update state.json for one stage."""
    state["repo_root"] = str(state_path.parent.parent.parent.parent.resolve())
    state["interpreter"] = str(interpreter)
    state["last_requested_approach"] = approach

    approach_state = state.setdefault("approaches", {}).setdefault(approach, {})
    approach_state["last_updated_at"] = utc_now_iso()

    stage_state = get_stage_state(state, approach, stage.stage_id)
    stage_state["stage_id"] = stage.stage_id
    stage_state["status"] = status
    stage_state["config"] = stage.config_path
    stage_state["runner"] = stage.runner
    stage_state["module"] = stage.module
    stage_state["interpreter"] = str(interpreter)
    stage_state["log_path"] = str(log_path)
    if started_at is not None:
        stage_state["started_at"] = started_at
    if finished_at is not None:
        stage_state["finished_at"] = finished_at
    if exit_code is not None:
        stage_state["exit_code"] = exit_code
    if outputs_verified is not None:
        stage_state["outputs_verified"] = outputs_verified
    if status == "completed":
        stage_state["last_success_at"] = finished_at
    if status == "failed":
        stage_state["last_failure_at"] = finished_at

    save_state(state_path, state)


def stage_log_path(repo_root: Path, approach: str, stage_id: str) -> Path:
    """Return the orchestrator log path for a stage."""
    return repo_root / ORCHESTRATOR_ROOT_RELATIVE / approach / f"{stage_id}.log"


def schema_success_marker(repo_root: Path) -> Path:
    """Return the schema_checks success marker path."""
    return repo_root / "outputs/logs/orchestrator/shared/schema_checks.ok.json"


def build_stage_command(repo_root: Path, interpreter: Path, stage: StageDefinition) -> list[str]:
    """Build the subprocess command for a stage."""
    config_path = repo_root / stage.config_path
    if stage.runner == "module":
        if stage.module is None:
            raise DispatcherError(f"Stage '{stage.stage_id}' is missing a module definition.")
        return [
            str(interpreter),
            "-m",
            stage.module,
            "--config",
            str(config_path),
        ]

    if stage.runner == "schema_checks":
        return [
            str(interpreter),
            "-c",
            SCHEMA_CHECKS_WRAPPER,
            str(repo_root),
            str(config_path),
        ]

    raise DispatcherError(f"Unknown runner '{stage.runner}' for stage '{stage.stage_id}'.")


def write_schema_success_marker(
    marker_path: Path,
    interpreter: Path,
    config_path: str,
) -> None:
    """Write the schema_checks success marker only after a successful run."""
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": "completed",
        "validated_at": utc_now_iso(),
        "interpreter": str(interpreter),
        "config": config_path,
    }
    with open(marker_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def stream_stage_output(
    command: list[str],
    cwd: Path,
    log_path: Path,
) -> int:
    """Run a stage, mirroring stdout/stderr to the console and the stage log."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env.setdefault("MPLBACKEND", "Agg")
    env["PYTHONPATH"] = str(cwd) + os.pathsep + env.get("PYTHONPATH", "")

    with open(log_path, "w", encoding="utf-8") as handle:
        handle.write(f"$ {' '.join(command)}\n\n")
        handle.flush()

        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        assert process.stdout is not None
        for line in process.stdout:
            print(line, end="")
            handle.write(line)
        process.stdout.close()
        return process.wait()


def verify_stage_outputs(repo_root: Path, stage: StageDefinition) -> bool:
    """Return True when all declared outputs exist after a stage run."""
    return stage_outputs_exist(repo_root, stage)


def _format_elapsed(seconds: float) -> str:
    """Format elapsed seconds as a human-friendly string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = seconds % 60
    if minutes < 60:
        return f"{minutes}m {secs:.0f}s"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m {secs:.0f}s"


def execute_pipeline(
    repo_root: Path,
    state: dict[str, Any],
    state_path: Path,
    approach: str,
    start_index: int,
    interpreter: Path,
) -> int:
    """Execute the selected pipeline from the requested stage onward."""
    import time as _time

    stages = PIPELINES[approach]
    if start_index < 0 or start_index >= len(stages):
        raise DispatcherError(f"Invalid start index for {approach}: {start_index}")

    stage_timings: list[tuple[str, float, str]] = []
    pipeline_t0 = _time.monotonic()

    for stage in stages[start_index:]:
        log_path = stage_log_path(repo_root, approach, stage.stage_id)
        started_at = utc_now_iso()
        update_stage_state(
            state,
            state_path,
            approach,
            stage,
            status="running",
            interpreter=interpreter,
            log_path=log_path,
            started_at=started_at,
            outputs_verified=False,
        )

        command = build_stage_command(repo_root, interpreter, stage)
        print(f"\n==> [{approach}] running stage: {stage.stage_id}")
        stage_t0 = _time.monotonic()
        exit_code = stream_stage_output(command, repo_root, log_path)
        stage_elapsed = _time.monotonic() - stage_t0

        if exit_code == 0 and stage.stage_id == "schema_checks":
            write_schema_success_marker(
                schema_success_marker(repo_root),
                interpreter,
                stage.config_path,
            )

        outputs_verified = exit_code == 0 and verify_stage_outputs(repo_root, stage)
        finished_at = utc_now_iso()
        status_label = "completed" if (exit_code == 0 and outputs_verified) else "failed"
        stage_timings.append((stage.stage_id, stage_elapsed, status_label))

        print(
            f"    [{approach}/{stage.stage_id}] {status_label} in "
            f"{_format_elapsed(stage_elapsed)}"
        )

        if exit_code != 0 or not outputs_verified:
            if exit_code == 0 and not outputs_verified:
                with open(log_path, "a", encoding="utf-8") as handle:
                    handle.write(
                        "\nDispatcher error: stage exited successfully but required outputs are missing.\n"
                    )
                print(
                    "Dispatcher error: stage exited successfully but required outputs are missing.",
                    file=sys.stderr,
                )
                exit_code = 1

            update_stage_state(
                state,
                state_path,
                approach,
                stage,
                status="failed",
                interpreter=interpreter,
                log_path=log_path,
                started_at=started_at,
                finished_at=finished_at,
                exit_code=exit_code,
                outputs_verified=False,
            )
            _print_timing_summary(approach, stage_timings, pipeline_t0, repo_root)
            return exit_code

        update_stage_state(
            state,
            state_path,
            approach,
            stage,
            status="completed",
            interpreter=interpreter,
            log_path=log_path,
            started_at=started_at,
            finished_at=finished_at,
            exit_code=0,
            outputs_verified=True,
        )

    _print_timing_summary(approach, stage_timings, pipeline_t0, repo_root)
    return 0


def _print_timing_summary(
    approach: str,
    timings: list[tuple[str, float, str]],
    pipeline_t0: float,
    repo_root: Path | None = None,
) -> None:
    """Print a ranked timing summary and disk usage after a pipeline run."""
    import time as _time

    if not timings:
        return

    total_elapsed = _time.monotonic() - pipeline_t0
    sorted_by_time = sorted(timings, key=lambda t: t[1], reverse=True)

    print(f"\n{'=' * 60}")
    print(f"  Timing summary for {approach}")
    print(f"  Total wall-clock: {_format_elapsed(total_elapsed)}")
    print(f"{'=' * 60}")
    print(f"  {'Stage':<30} {'Time':>10}  {'Status'}")
    print(f"  {'-' * 30} {'-' * 10}  {'-' * 9}")
    for stage_id, elapsed, status in sorted_by_time:
        pct = (elapsed / total_elapsed * 100) if total_elapsed > 0 else 0
        print(
            f"  {stage_id:<30} {_format_elapsed(elapsed):>10}  "
            f"{status}  ({pct:.0f}%)"
        )
    print(f"{'=' * 60}")

    if repo_root is not None:
        _print_disk_usage_summary(repo_root)


def _print_disk_usage_summary(repo_root: Path) -> None:
    """Print disk usage by track for figures, tables, and curated data."""
    from src.common.disk_usage import (
        compute_outputs_disk_usage,
        format_bytes,
        total_outputs_bytes,
    )

    usage = compute_outputs_disk_usage(repo_root)
    total = total_outputs_bytes(usage)
    if total == 0:
        return

    print(f"\n  {'Disk usage (outputs):':<30}")
    print(f"  {'-' * 50}")
    for approach, u in usage.items():
        if u.total_bytes == 0:
            continue
        parts = []
        if u.figures_bytes:
            parts.append(f"figures {format_bytes(u.figures_bytes)}")
        if u.tables_bytes:
            parts.append(f"tables {format_bytes(u.tables_bytes)}")
        if u.curated_bytes:
            parts.append(f"curated {format_bytes(u.curated_bytes)}")
        if u.logs_bytes:
            parts.append(f"logs {format_bytes(u.logs_bytes)}")
        label = approach.replace("_", " ").title()
        print(f"  {label:<12} {format_bytes(u.total_bytes):>10}  ({', '.join(parts)})")
    print(f"  {'-' * 50}")
    print(f"  {'Total':<12} {format_bytes(total):>10}")
    print(f"{'=' * 60}")


def maybe_run_shared_prerequisites(
    repo_root: Path,
    state: dict[str, Any],
    state_path: Path,
    selected_approach: str,
    auto_yes: bool,
    interpreter: Path | None,
) -> tuple[bool, int, Path | None]:
    """Run shared prerequisites before dependent approaches when needed."""
    if selected_approach in {APPROACH_SHARED, APPROACH_PHOTO_INTAKE}:
        return True, 0, interpreter

    assessment = assess_pipeline(repo_root, state, APPROACH_SHARED)
    if assessment.all_complete:
        return True, 0, interpreter

    first_incomplete = assessment.first_incomplete_index
    if first_incomplete is None:
        return True, 0, interpreter

    earliest_missing = assessment.stages[first_incomplete].stage.stage_id
    rerun_completed = completed_stage_ids_from(assessment, first_incomplete)
    prompt = (
        f"Shared prerequisites are incomplete for {selected_approach}. "
        f"Run shared first from '{earliest_missing}'?"
    )
    if rerun_completed:
        prompt += f" This will rerun completed downstream stages: {', '.join(rerun_completed)}."
    prompt += " [y/N]: "

    if not confirm(prompt, auto_yes):
        print("Shared prerequisites were declined; stopping.")
        return False, 0, interpreter

    if interpreter is None:
        interpreter = resolve_active_interpreter(repo_root)

    exit_code = execute_pipeline(
        repo_root=repo_root,
        state=state,
        state_path=state_path,
        approach=APPROACH_SHARED,
        start_index=first_incomplete,
        interpreter=interpreter,
    )
    return True, exit_code, interpreter


def ensure_track_d_split_artifact(repo_root: Path, selected_approach: str) -> None:
    """Fail early when Track D is requested without Track A Stage 5 splits."""
    if selected_approach != APPROACH_TRACK_D:
        return

    split_artifact = repo_root / "outputs/tables/track_a_s5_candidate_splits.parquet"
    if not split_artifact.is_file():
        raise DispatcherError(
            "Track D requires Track A Stage 5 split artifact "
            "(outputs/tables/track_a_s5_candidate_splits.parquet). "
            "Run Track A through Stage 5 before running Track D."
        )


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Execute a pipeline approach from the repo root using the current "
            "runtime-matched Python interpreter."
        ),
    )
    parser.add_argument(
        "--approach",
        choices=APPROACH_CHOICES,
        help="Pipeline approach to run.",
    )
    parser.add_argument(
        "--from-stage",
        help="Optional stage id to rerun from within the selected approach.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Answer yes to confirmation prompts. For already-complete approaches, this defaults to skip.",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    """CLI entry point."""
    args = parse_args(argv)
    repo_root = discover_repo_root()
    state_path = repo_root / STATE_RELATIVE_PATH
    state = load_state(state_path)
    if args.approach is None:
        raise DispatcherError(
            "An approach is required when calling pipeline_dispatcher.py directly. "
            "Use scripts/run_pipeline.py for the interactive launcher."
        )

    approach = args.approach

    interpreter: Path | None = resolve_active_interpreter(repo_root)
    should_continue, shared_exit_code, interpreter = maybe_run_shared_prerequisites(
        repo_root=repo_root,
        state=state,
        state_path=state_path,
        selected_approach=approach,
        auto_yes=args.yes,
        interpreter=interpreter,
    )
    if not should_continue:
        return 0
    if shared_exit_code != 0:
        return shared_exit_code
    if shared_exit_code == 0 and approach != APPROACH_SHARED:
        refreshed_state = load_state(state_path)
        state.clear()
        state.update(refreshed_state)

    ensure_track_d_split_artifact(repo_root, approach)

    decision = resolve_run_decision(
        repo_root=repo_root,
        state=state,
        approach=approach,
        from_stage=args.from_stage,
        auto_yes=args.yes,
    )
    if not decision.should_run or decision.start_index is None:
        print("No stages were run.")
        _print_disk_usage_summary(repo_root)
        return 0

    return execute_pipeline(
        repo_root=repo_root,
        state=state,
        state_path=state_path,
        approach=approach,
        start_index=decision.start_index,
        interpreter=interpreter,
    )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DispatcherError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
