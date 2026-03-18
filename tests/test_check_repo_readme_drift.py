"""Tests for the repository README drift checker."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module() -> object:
    script_path = Path(__file__).resolve().parent.parent / "scripts" / "check_repo_readme_drift.py"
    spec = importlib.util.spec_from_file_location("check_repo_readme_drift", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_detect_drift_reports_changed_file_and_sections(tmp_path: Path) -> None:
    module = _load_module()

    project_root = tmp_path / "repo"
    project_root.mkdir()
    (project_root / "README.md").write_text("# Repo\n", encoding="utf-8")
    (project_root / "requirements.txt").write_text("pandas\n", encoding="utf-8")

    module.PROJECT_ROOT = project_root
    module.README_FILE = project_root / "README.md"
    module.STATE_FILE = project_root / ".readme_state.json"
    module.DEPENDENCY_MAP = {
        "requirements.txt": ["Repository Status", "How to Run"],
    }

    module.update_state()
    (project_root / "requirements.txt").write_text("pandas\npolars\n", encoding="utf-8")

    result = module.detect_drift()

    assert result.changed_sources == ["requirements.txt"]
    assert result.new_sources == []
    assert result.missing_sources == []
    assert result.affected_sections == ["How to Run", "Repository Status"]


def test_detect_drift_reports_new_file_from_glob_pattern(tmp_path: Path) -> None:
    module = _load_module()

    project_root = tmp_path / "repo"
    project_root.mkdir()
    (project_root / "README.md").write_text("# Repo\n", encoding="utf-8")
    (project_root / "src" / "eda" / "track_c").mkdir(parents=True)

    module.PROJECT_ROOT = project_root
    module.README_FILE = project_root / "README.md"
    module.STATE_FILE = project_root / ".readme_state.json"
    module.DEPENDENCY_MAP = {
        "src/eda/track_c/*.py": ["Repository Status", "Track Index"],
    }

    module.update_state()
    (project_root / "src" / "eda" / "track_c" / "geo_coverage.py").write_text(
        "print('ok')\n",
        encoding="utf-8",
    )

    result = module.detect_drift()

    assert result.changed_sources == []
    assert result.new_sources == ["src/eda/track_c/geo_coverage.py"]
    assert result.missing_sources == []
    assert result.affected_sections == ["Repository Status", "Track Index"]


def test_detect_drift_reports_changed_directory_state(tmp_path: Path) -> None:
    module = _load_module()

    project_root = tmp_path / "repo"
    project_root.mkdir()
    (project_root / "README.md").write_text("# Repo\n", encoding="utf-8")
    (project_root / "src" / "eda" / "track_a").mkdir(parents=True)

    module.PROJECT_ROOT = project_root
    module.README_FILE = project_root / "README.md"
    module.STATE_FILE = project_root / ".readme_state.json"
    module.DEPENDENCY_MAP = {
        "src/eda": ["Repository Status", "Track Folder Check"],
    }

    module.update_state()
    (project_root / "src" / "eda" / "track_c").mkdir()

    result = module.detect_drift()

    assert result.changed_sources == ["src/eda"]
    assert result.new_sources == []
    assert result.missing_sources == []
    assert result.affected_sections == ["Repository Status", "Track Folder Check"]


def test_directory_tracking_ignores_local_tooling_dirs(tmp_path: Path) -> None:
    module = _load_module()

    project_root = tmp_path / "repo"
    project_root.mkdir()
    (project_root / "README.md").write_text("# Repo\n", encoding="utf-8")

    module.PROJECT_ROOT = project_root
    module.README_FILE = project_root / "README.md"
    module.STATE_FILE = project_root / ".readme_state.json"
    module.DEPENDENCY_MAP = {
        ".": ["Project Structure"],
    }

    module.update_state()
    (project_root / ".venv").mkdir()

    result = module.detect_drift()

    assert result.changed_sources == []
    assert result.new_sources == []
    assert result.missing_sources == []
    assert result.affected_sections == []