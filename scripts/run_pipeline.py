#!/usr/bin/env python3
"""Cross-platform interactive launcher for the pipeline dispatcher."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import pipeline_dispatcher as dispatcher
from src.common.gpu_check import check_gpu_available, get_gpu_status


COLOR_ENABLED = sys.stdout.isatty()
RST = "\033[0m" if COLOR_ENABLED else ""
BOLD = "\033[1m" if COLOR_ENABLED else ""
DIM = "\033[2m" if COLOR_ENABLED else ""
RED = "\033[31m" if COLOR_ENABLED else ""
GRN = "\033[32m" if COLOR_ENABLED else ""
YLW = "\033[33m" if COLOR_ENABLED else ""
CYN = "\033[36m" if COLOR_ENABLED else ""
BWHT = "\033[1;97m" if COLOR_ENABLED else ""

APPROACH_ORDER = [
    dispatcher.APPROACH_SHARED,
    dispatcher.APPROACH_TRACK_A,
    dispatcher.APPROACH_TRACK_B,
    dispatcher.APPROACH_TRACK_C,
    dispatcher.APPROACH_TRACK_D,
    dispatcher.APPROACH_TRACK_E,
    dispatcher.APPROACH_PHOTO_INTAKE,
]

APPROACH_LABELS = {
    dispatcher.APPROACH_SHARED: "Shared",
    dispatcher.APPROACH_TRACK_A: "Track A",
    dispatcher.APPROACH_TRACK_B: "Track B",
    dispatcher.APPROACH_TRACK_C: "Track C",
    dispatcher.APPROACH_TRACK_D: "Track D",
    dispatcher.APPROACH_TRACK_E: "Track E",
    dispatcher.APPROACH_PHOTO_INTAKE: "Photo Intake",
}

APPROACH_DESCRIPTIONS = {
    dispatcher.APPROACH_SHARED: "Ingest + Curate",
    dispatcher.APPROACH_TRACK_A: "Future star prediction",
    dispatcher.APPROACH_TRACK_B: "Usefulness ranking",
    dispatcher.APPROACH_TRACK_C: "Sentiment and topic drift",
    dispatcher.APPROACH_TRACK_D: "Cold-start recommendation",
    dispatcher.APPROACH_TRACK_E: "Bias and disparity auditing",
    dispatcher.APPROACH_PHOTO_INTAKE: "Multimodal photo metadata intake",
}

APPROACH_ALIASES = {
    "shared": dispatcher.APPROACH_SHARED,
    "track_a": dispatcher.APPROACH_TRACK_A,
    "track-a": dispatcher.APPROACH_TRACK_A,
    "a": dispatcher.APPROACH_TRACK_A,
    "track_b": dispatcher.APPROACH_TRACK_B,
    "track-b": dispatcher.APPROACH_TRACK_B,
    "b": dispatcher.APPROACH_TRACK_B,
    "track_c": dispatcher.APPROACH_TRACK_C,
    "track-c": dispatcher.APPROACH_TRACK_C,
    "c": dispatcher.APPROACH_TRACK_C,
    "track_d": dispatcher.APPROACH_TRACK_D,
    "track-d": dispatcher.APPROACH_TRACK_D,
    "d": dispatcher.APPROACH_TRACK_D,
    "track_e": dispatcher.APPROACH_TRACK_E,
    "track-e": dispatcher.APPROACH_TRACK_E,
    "e": dispatcher.APPROACH_TRACK_E,
    "photo_intake": dispatcher.APPROACH_PHOTO_INTAKE,
    "photo-intake": dispatcher.APPROACH_PHOTO_INTAKE,
    "photo": dispatcher.APPROACH_PHOTO_INTAKE,
    "p": dispatcher.APPROACH_PHOTO_INTAKE,
}


class LauncherError(RuntimeError):
    """Raised when the launcher cannot safely continue."""


def supports_tty() -> bool:
    """Return True when the launcher can safely prompt interactively."""
    return sys.stdin.isatty() and sys.stdout.isatty()


def prompt_input(message: str) -> str:
    """Prompt for one line of text."""
    if not supports_tty():
        raise LauncherError("Interactive mode requires a TTY. Pass explicit arguments instead.")
    try:
        return input(message).strip()
    except EOFError as exc:
        raise LauncherError("Input closed before a selection was provided.") from exc


def confirm(message: str, auto_yes: bool) -> bool:
    """Return True when the user confirms."""
    if auto_yes:
        print(f"{message} yes (via --yes)")
        return True
    return prompt_input(message).lower() in {"y", "yes"}


def clear_screen() -> None:
    """Clear the terminal for the dashboard render."""
    if supports_tty():
        print("\033[2J\033[H", end="")


def discover_repo_root() -> Path:
    """Return the repo root from the known script location."""
    repo_root = REPO_ROOT.resolve()
    if not dispatcher.is_repo_root(repo_root):
        raise LauncherError(f"Could not locate repo root from launcher path: {repo_root}")
    return repo_root


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    """Parse launcher CLI arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Cross-platform launcher for the shared and per-track pipelines. "
            "This is the canonical entrypoint for interactive and scripted runs."
        ),
    )
    parser.add_argument(
        "approach_alias",
        nargs="?",
        help="Optional positional approach alias such as shared, track_a, or a.",
    )
    parser.add_argument(
        "--approach",
        choices=dispatcher.APPROACH_CHOICES,
        help="Pipeline approach to run. If omitted, an interactive dashboard is shown.",
    )
    parser.add_argument(
        "--from-stage",
        help="Optional stage id to run from within the selected approach.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Answer yes to confirmation prompts when running the dispatcher.",
    )
    return parser.parse_args(argv)


def normalize_approach(args: argparse.Namespace) -> str | None:
    """Resolve the requested approach from explicit or positional input."""
    if args.approach is not None:
        return args.approach
    if args.approach_alias is None:
        return None

    alias = args.approach_alias.lower()
    if alias in APPROACH_ALIASES:
        return APPROACH_ALIASES[alias]
    raise LauncherError(
        f"Unknown approach '{args.approach_alias}'. Use --help to see valid choices."
    )


def format_bar(completed: int, total: int, width: int = 16) -> str:
    """Return a compact unicode progress bar."""
    if total <= 0:
        return f"{DIM}{'░' * width}{RST}"

    filled = (completed * width) // total
    bar = ("█" * filled) + ("░" * (width - filled))
    if completed == total:
        color = GRN
    elif completed > 0:
        color = YLW
    else:
        color = DIM
    return f"{color}{bar}{RST}"


def build_assessments(
    repo_root: Path,
) -> tuple[dict[str, dispatcher.PipelineAssessment], dict[str, str], str | None]:
    """Return assessments, a coarse status label per approach, and the recommendation."""
    state = dispatcher.load_state(repo_root / dispatcher.STATE_RELATIVE_PATH)
    assessments = {
        approach: dispatcher.assess_pipeline(repo_root, state, approach)
        for approach in APPROACH_ORDER
    }

    statuses: dict[str, str] = {}
    shared_complete = assessments[dispatcher.APPROACH_SHARED].all_complete
    track_d_split_ready = (
        repo_root / "outputs/tables/track_a_s5_candidate_splits.parquet"
    ).is_file()

    for approach, assessment in assessments.items():
        if assessment.all_complete:
            statuses[approach] = "complete"
        elif assessment.any_complete:
            statuses[approach] = "in_progress"
        elif (
            approach
            not in {dispatcher.APPROACH_SHARED, dispatcher.APPROACH_PHOTO_INTAKE}
            and not shared_complete
        ):
            statuses[approach] = "blocked_shared"
        elif approach == dispatcher.APPROACH_TRACK_D and not track_d_split_ready:
            statuses[approach] = "blocked_track_a"
        else:
            statuses[approach] = "not_started"

    recommendation: str | None = None
    for approach in APPROACH_ORDER:
        if statuses[approach] == "complete":
            continue
        if (
            approach
            not in {dispatcher.APPROACH_SHARED, dispatcher.APPROACH_PHOTO_INTAKE}
            and not shared_complete
        ):
            recommendation = dispatcher.APPROACH_SHARED
            break
        if approach == dispatcher.APPROACH_TRACK_D and not track_d_split_ready:
            recommendation = dispatcher.APPROACH_TRACK_A
            break
        recommendation = approach
        break

    return assessments, statuses, recommendation


def status_message(
    approach: str,
    assessment: dispatcher.PipelineAssessment,
    status: str,
) -> str:
    """Return the secondary status line for one approach."""
    if status == "complete":
        return f"{GRN}All stages complete{RST}"
    if status == "in_progress":
        assert assessment.first_incomplete_index is not None
        stage_id = assessment.stages[assessment.first_incomplete_index].stage.stage_id
        return f"{YLW}Next: {stage_id}{RST}"
    if status == "blocked_shared":
        return f"{DIM}Blocked: run Shared first{RST}"
    if status == "blocked_track_a":
        return f"{DIM}Blocked: needs Track A split_selection output{RST}"
    return f"{DIM}Not started{RST}"


def render_dashboard(
    assessments: dict[str, dispatcher.PipelineAssessment],
    statuses: dict[str, str],
    recommendation: str | None,
    repo_root: Path,
) -> None:
    """Render the main overview screen."""
    clear_screen()
    print(f"{CYN}{'=' * 68}{RST}")
    print(f"{BWHT}KaggleTeam Spring 2026 - Pipeline Launcher{RST}")
    print(f"{CYN}{'=' * 68}{RST}")
    print()

    for index, approach in enumerate(APPROACH_ORDER, start=1):
        assessment = assessments[approach]
        label = APPROACH_LABELS[approach]
        desc = APPROACH_DESCRIPTIONS[approach]
        completed = sum(1 for stage in assessment.stages if stage.complete)
        total = len(assessment.stages)
        bar = format_bar(completed, total)
        print(
            f"{BOLD}{index}) {label:<8}{RST} {desc:<28} {bar} {completed}/{total}"
        )
        print(f"   {status_message(approach, assessment, statuses[approach])}")
        print()

    print(f"{CYN}{'-' * 68}{RST}")
    if recommendation is None:
        print(f"{YLW}Recommended:{RST} all tracked approaches are complete")
    else:
        recommendation_assessment = assessments[recommendation]
        if recommendation_assessment.all_complete:
            suffix = "already complete"
        elif recommendation_assessment.first_incomplete_index is None:
            suffix = "ready"
        else:
            suffix = (
                "resume from "
                + recommendation_assessment.stages[
                    recommendation_assessment.first_incomplete_index
                ].stage.stage_id
            )
        print(
            f"{YLW}Recommended:{RST} {APPROACH_LABELS[recommendation]} ({suffix})"
        )

    # Disk usage summary
    from src.common.disk_usage import (
        compute_outputs_disk_usage,
        format_bytes,
        total_outputs_bytes,
    )

    usage = compute_outputs_disk_usage(repo_root)
    total = total_outputs_bytes(usage)
    if total > 0:
        print(f"   {DIM}Outputs disk usage: {format_bytes(total)}{RST}")

    print("Choose 1-7, R for recommended, or Q to quit.")


def choose_dashboard_approach(
    assessments: dict[str, dispatcher.PipelineAssessment],
    statuses: dict[str, str],
    recommendation: str | None,
    repo_root: Path,
) -> str | None:
    """Return the chosen approach or None to exit."""
    while True:
        render_dashboard(assessments, statuses, recommendation, repo_root)
        choice = prompt_input("> ").lower()
        if choice in {"q", "quit", "exit"}:
            return None
        if choice == "r":
            return recommendation
        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(APPROACH_ORDER):
                return APPROACH_ORDER[index]
        print("Invalid selection. Choose 1-7, R, or Q.")


def stage_list(approach: str) -> list[str]:
    """Return stage ids in order for an approach."""
    return [stage.stage_id for stage in dispatcher.PIPELINES[approach]]


def choose_stage(approach: str) -> str | None:
    """Prompt for a stage to rerun from."""
    stages = stage_list(approach)
    print()
    print(f"{BOLD}{APPROACH_LABELS[approach]} stages{RST}")
    for index, stage_id in enumerate(stages, start=1):
        print(f"{index}) {stage_id}")
    print("B) back")

    while True:
        choice = prompt_input("Select stage: ").lower()
        if choice in {"b", "back"}:
            return None
        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(stages):
                return stages[index]
        print("Invalid stage selection.")


def choose_action(
    approach: str,
    assessment: dispatcher.PipelineAssessment,
    status: str,
) -> tuple[str, str | None, bool] | None:
    """Prompt for the action to take for a selected approach."""
    clear_screen()
    print(f"{BWHT}{APPROACH_LABELS[approach]} - {APPROACH_DESCRIPTIONS[approach]}{RST}")
    print(f"{CYN}{'-' * 68}{RST}")
    for stage in assessment.stages:
        icon = f"{GRN}OK{RST}" if stage.complete else f"{RED}--{RST}"
        present = len(stage.stage.required_outputs) if stage.complete else 0
        print(f"{icon} {stage.stage.stage_id} ({present}/{len(stage.stage.required_outputs)} outputs)")
    print()

    if status == "complete":
        print("1) Skip")
        print("2) Rerun from stage")
        print("3) Rerun full approach")
        print("B) Back")
        while True:
            choice = prompt_input("Action: ").lower()
            if choice in {"1", "s", "skip"}:
                return None
            if choice in {"2", "r"}:
                selected_stage = choose_stage(approach)
                if selected_stage is not None:
                    return approach, selected_stage, True
                clear_screen()
                return choose_action(approach, assessment, status)
            if choice in {"3", "f"}:
                return approach, stage_list(approach)[0], True
            if choice in {"b", "back"}:
                return None
            print("Invalid selection.")

    if status == "in_progress":
        first_incomplete = assessment.first_incomplete_index
        assert first_incomplete is not None
        first_stage = assessment.stages[first_incomplete].stage.stage_id
        print(f"1) Continue from earliest missing stage ({first_stage})")
        print("2) Rerun from stage")
        print("3) Rerun full approach")
        print("B) Back")
        while True:
            choice = prompt_input("Action: ").lower()
            if choice in {"1", "c", "continue"}:
                return approach, None, True
            if choice in {"2", "r"}:
                selected_stage = choose_stage(approach)
                if selected_stage is not None:
                    return approach, selected_stage, True
                clear_screen()
                return choose_action(approach, assessment, status)
            if choice in {"3", "f"}:
                return approach, stage_list(approach)[0], True
            if choice in {"b", "back"}:
                return None
            print("Invalid selection.")

    if status in {"blocked_shared", "blocked_track_a", "not_started"}:
        print(f"1) Run {APPROACH_LABELS[approach]}")
        print("B) Back")
        while True:
            choice = prompt_input("Action: ").lower()
            if choice in {"1", "r", "run"}:
                return approach, None, True
            if choice in {"b", "back"}:
                return None
            print("Invalid selection.")

    return None


def choose_interactive_command(
    repo_root: Path,
) -> tuple[str, str | None, bool] | None:
    """Drive the dashboard flow and return the chosen dispatcher request."""
    while True:
        assessments, statuses, recommendation = build_assessments(repo_root)
        approach = choose_dashboard_approach(
            assessments, statuses, recommendation, repo_root
        )
        if approach is None:
            return None
        action = choose_action(approach, assessments[approach], statuses[approach])
        if action is not None:
            return action


def ensure_gpu_if_desired(
    venv_python: Path,
    repo_root: Path,
    auto_yes: bool,
) -> bool:
    """Check GPU availability, optionally prompt to install, return True if GPU will be used."""
    if check_gpu_available(venv_python, repo_root):
        return True

    available, reason = get_gpu_status(venv_python, repo_root)
    if available:
        return True

    req_gpu = repo_root / "requirements-gpu.txt"
    if not req_gpu.is_file():
        return False

    message = (
        f"GPU acceleration not available ({reason or 'unknown'}). "
        "Install optional GPU packages for faster pipeline? [y/N]: "
    )
    if not confirm(message, auto_yes):
        return False

    print("Installing GPU packages (cudf-cu12, cudf-polars-cu12)...")
    result = subprocess.run(
        [str(venv_python), "-m", "pip", "install", "-r", str(req_gpu)],
        cwd=repo_root,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        print("GPU package install failed; continuing with CPU.", file=sys.stderr)
        return False

    return check_gpu_available(venv_python, repo_root)


def ensure_matching_virtualenv(repo_root: Path, auto_yes: bool) -> Path:
    """Return a runtime-matched interpreter with the required packages installed."""
    runtime = dispatcher.detect_runtime()
    venv_dir = repo_root / dispatcher.venv_dir_name_for_runtime(runtime)
    venv_python = dispatcher.resolve_venv_python(venv_dir, runtime)

    if venv_python is None:
        print(f"Creating runtime-matched virtual environment at {venv_dir}")
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_dir)],
            cwd=repo_root,
            check=True,
            text=True,
        )
        venv_python = dispatcher.resolve_venv_python(venv_dir, runtime)

    if venv_python is None:
        raise LauncherError(f"Could not locate virtualenv interpreter in {venv_dir}")

    dispatcher.assert_interpreter_matches_runtime(venv_python, runtime)

    pip_check = subprocess.run(
        [str(venv_python), "-m", "pip", "--version"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if pip_check.returncode != 0:
        subprocess.run(
            [str(venv_python), "-m", "ensurepip", "--upgrade"],
            cwd=repo_root,
            check=True,
            text=True,
        )

    missing_imports = dispatcher.check_required_imports(venv_python, repo_root)
    if missing_imports:
        message = (
            f"Missing packages in {venv_dir.name} ({', '.join(missing_imports)}). "
            "Install from requirements.txt? [y/N]: "
        )
        if not confirm(message, auto_yes):
            raise LauncherError(
                "Required packages are missing from the runtime-matched virtual environment."
            )
        subprocess.run(
            [str(venv_python), "-m", "pip", "install", "-r", "requirements.txt"],
            cwd=repo_root,
            check=True,
            text=True,
        )
        remaining = dispatcher.check_required_imports(venv_python, repo_root)
        if remaining:
            raise LauncherError(
                "Imports are still missing after install: " + ", ".join(remaining)
            )
    return venv_python


def build_dispatcher_command(
    repo_root: Path,
    interpreter: Path,
    approach: str,
    from_stage: str | None,
    auto_yes: bool,
) -> list[str]:
    """Return the dispatcher command for execution."""
    command = [
        str(interpreter),
        str(repo_root / "scripts" / "pipeline_dispatcher.py"),
        "--approach",
        approach,
    ]
    if from_stage:
        command.extend(["--from-stage", from_stage])
    if auto_yes:
        command.append("--yes")
    return command


def execute_dispatch(
    repo_root: Path,
    approach: str,
    from_stage: str | None,
    auto_yes: bool,
) -> int:
    """Execute the dispatcher with the runtime-matched interpreter."""
    interpreter = ensure_matching_virtualenv(repo_root, auto_yes)
    use_gpu = ensure_gpu_if_desired(interpreter, repo_root, auto_yes)
    command = build_dispatcher_command(repo_root, interpreter, approach, from_stage, auto_yes)

    env = os.environ.copy()
    if use_gpu:
        env["YELP_POLARS_ENGINE"] = "gpu"
        print(f"{GRN}Using GPU acceleration (cudf-polars).{RST}")

    return subprocess.run(command, cwd=repo_root, env=env, check=False).returncode


def main(argv: Iterable[str] | None = None) -> int:
    """Launcher entrypoint."""
    args = parse_args(argv)
    repo_root = discover_repo_root()
    approach = normalize_approach(args)

    if approach is None:
        selection = choose_interactive_command(repo_root)
        if selection is None:
            return 0
        approach, from_stage, auto_yes = selection
        return execute_dispatch(repo_root, approach, from_stage, auto_yes)

    return execute_dispatch(repo_root, approach, args.from_stage, args.yes)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (LauncherError, dispatcher.DispatcherError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
