"""Regression checks for the shared M002 modeling contract."""

from pathlib import Path


def test_modeling_package_scaffold_exists() -> None:
    """Shared modeling packages should exist before per-track implementation starts."""
    required_dirs = [
        Path("src/modeling/common"),
        Path("src/modeling/track_a"),
        Path("src/modeling/track_b"),
        Path("src/modeling/track_c"),
        Path("src/modeling/track_d"),
        Path("outputs/modeling/track_a"),
        Path("outputs/modeling/track_b"),
        Path("outputs/modeling/track_c"),
        Path("outputs/modeling/track_d"),
    ]
    missing = [path.as_posix() for path in required_dirs if not path.is_dir()]
    assert not missing, f"Missing modeling contract directories: {missing}"


def test_modeling_readme_preserves_artifact_contract() -> None:
    """The shared README should keep the per-track artifact bundle explicit."""
    readme = Path("src/modeling/README.md").read_text(encoding="utf-8")
    for marker in [
        "summary.md",
        "metrics.csv",
        "metrics.parquet",
        "config_snapshot.json",
        "Track D1 is required",
        "Track D2 is optional/stretch only",
        "Track A is the preferred default M003 fairness-audit target",
    ]:
        assert marker in readme, marker


def test_m002_docs_preserve_scope_lock_and_audit_target() -> None:
    """Milestone docs should keep the revised M002 scope and audit target stable."""
    text = (
        Path(".gsd/milestones/M002-c1uww6/M002-c1uww6-CONTEXT.md").read_text(
            encoding="utf-8"
        )
        + Path(".gsd/milestones/M002-c1uww6/M002-c1uww6-ROADMAP.md").read_text(
            encoding="utf-8"
        )
    )
    for marker in [
        "D1",
        "D2",
        "optional",
        "Track A preferred by default",
        "track_a_s5_candidate_splits.parquet",
    ]:
        assert marker in text, marker
