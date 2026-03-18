"""Tests for the cross-platform launcher and runtime guards."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import pipeline_dispatcher as dispatcher
from scripts import run_pipeline


def test_detect_runtime_prefers_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    """Windows hosts should be classified before other heuristics."""
    monkeypatch.setattr(dispatcher.os, "name", "nt", raising=False)
    assert dispatcher.detect_runtime() == dispatcher.RUNTIME_WINDOWS


def test_detect_runtime_detects_wsl(monkeypatch: pytest.MonkeyPatch) -> None:
    """WSL hosts should be detected from the kernel release string."""
    monkeypatch.setattr(dispatcher.os, "name", "posix", raising=False)
    monkeypatch.setattr(
        dispatcher.platform,
        "uname",
        lambda: SimpleNamespace(release="5.15.167.4-microsoft-standard-WSL2"),
    )
    monkeypatch.delenv("WSL_INTEROP", raising=False)
    assert dispatcher.detect_runtime() == dispatcher.RUNTIME_WSL


def test_detect_runtime_defaults_to_linux(monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-WSL POSIX hosts should fall back to linux."""
    monkeypatch.setattr(dispatcher.os, "name", "posix", raising=False)
    monkeypatch.setattr(
        dispatcher.platform,
        "uname",
        lambda: SimpleNamespace(release="6.8.0-generic"),
    )
    monkeypatch.delenv("WSL_INTEROP", raising=False)
    assert dispatcher.detect_runtime() == dispatcher.RUNTIME_LINUX


def test_resolve_venv_python_uses_runtime_specific_layout(tmp_path: Path) -> None:
    """The runtime should only resolve the native venv path layout."""
    win_dir = tmp_path / ".venv-win" / "Scripts"
    win_dir.mkdir(parents=True)
    win_python = win_dir / "python.exe"
    win_python.write_text("", encoding="utf-8")

    linux_dir = tmp_path / ".venv-linux" / "bin"
    linux_dir.mkdir(parents=True)
    linux_python = linux_dir / "python"
    linux_python.write_text("", encoding="utf-8")

    assert (
        dispatcher.resolve_venv_python(tmp_path / ".venv-win", dispatcher.RUNTIME_WINDOWS)
        == win_python
    )
    assert (
        dispatcher.resolve_venv_python(tmp_path / ".venv-linux", dispatcher.RUNTIME_LINUX)
        == linux_python
    )


def test_assert_interpreter_matches_runtime_rejects_windows_path_on_posix() -> None:
    """WSL/Linux runs should reject Windows interpreters."""
    with pytest.raises(dispatcher.DispatcherError):
        dispatcher.assert_interpreter_matches_runtime(
            Path(r"C:\repo\.venv-win\Scripts\python.exe"),
            dispatcher.RUNTIME_WSL,
        )


def test_assert_interpreter_matches_runtime_rejects_posix_path_on_windows() -> None:
    """Windows runs should reject POSIX interpreters."""
    with pytest.raises(dispatcher.DispatcherError):
        dispatcher.assert_interpreter_matches_runtime(
            Path("/mnt/c/repo/.venv-wsl/bin/python"),
            dispatcher.RUNTIME_WINDOWS,
        )


def test_normalize_approach_accepts_aliases() -> None:
    """The launcher should preserve shorthand compatibility."""
    args = Namespace(approach=None, approach_alias="track-a")
    assert run_pipeline.normalize_approach(args) == dispatcher.APPROACH_TRACK_A


def test_build_dispatcher_command_preserves_approach_and_stage() -> None:
    """Launcher passthrough should preserve approach, stage, and yes flag."""
    repo_root = Path("/repo")
    interpreter = Path("/repo/.venv-wsl/bin/python")

    command = run_pipeline.build_dispatcher_command(
        repo_root=repo_root,
        interpreter=interpreter,
        approach=dispatcher.APPROACH_TRACK_B,
        from_stage="feature_correlates",
        auto_yes=True,
    )

    assert command == [
        str(interpreter),
        str(repo_root / "scripts" / "pipeline_dispatcher.py"),
        "--approach",
        dispatcher.APPROACH_TRACK_B,
        "--from-stage",
        "feature_correlates",
        "--yes",
    ]


def test_dispatcher_main_requires_explicit_approach() -> None:
    """The execution engine should direct interactive users to the launcher."""
    with pytest.raises(dispatcher.DispatcherError):
        dispatcher.main([])


def test_shell_wrapper_targets_python_launcher() -> None:
    """The Unix wrapper should delegate to the canonical Python launcher."""
    wrapper = (Path(__file__).resolve().parents[1] / "run_pipeline.sh").read_text(
        encoding="utf-8"
    )
    assert 'scripts/run_pipeline.py' in wrapper
    assert '"$@"' in wrapper


def test_powershell_wrapper_targets_python_launcher() -> None:
    """The Windows wrapper should delegate to the canonical Python launcher."""
    wrapper = (Path(__file__).resolve().parents[1] / "run_pipeline.ps1").read_text(
        encoding="utf-8"
    )
    assert "scripts\\run_pipeline.py" in wrapper
    assert "@args" in wrapper
