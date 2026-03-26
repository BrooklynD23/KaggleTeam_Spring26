---
id: T01
parent: S01
milestone: M001-4q3lxl
provides:
  - Dispatcher-derived Track A–E terminal summary contract for downstream completeness reporting
  - Regression coverage for canonical launcher command order and Track D blocker visibility
key_files:
  - scripts/pipeline_dispatcher.py
  - scripts/run_pipeline.py
  - tests/test_pipeline_dispatcher_all_tracks.py
  - tests/test_run_pipeline_launcher.py
key_decisions:
  - Use `get_eda_summary_contract()` as the single checklist/reporting surface derived from `PIPELINES`, with Track D's blocker centralized in `TRACK_D_SPLIT_DEPENDENCY`.
patterns_established:
  - Derive downstream reporting contracts from terminal dispatcher stages instead of maintaining a parallel manifest.
observability_surfaces:
  - `scripts.pipeline_dispatcher.get_eda_summary_contract()`
  - `tests/test_pipeline_dispatcher_all_tracks.py`
  - `tests/test_run_pipeline_launcher.py`
duration: 25m
verification_result: passed
completed_at: 2026-03-21T21:49:00-07:00
blocker_discovered: false
---

# T01: Expose the all-track EDA completion contract from the dispatcher

**Added a dispatcher-derived Track A–E summary contract plus regression checks for launcher order and Track D blockers.**

## What Happened

I first fixed the pre-flight observability gaps by adding an inspectable failure-state verification step to `S01-PLAN.md` and an `## Observability Impact` section to `T01-PLAN.md`.

I then added `get_eda_summary_contract()` to `scripts/pipeline_dispatcher.py`. The helper derives the Track A–E checklist contract directly from `PIPELINES` and shared approach constants, validates that each EDA track still ends in `summary_report`, extracts the markdown artifact that proves completion, emits the canonical `python scripts/run_pipeline.py --approach ...` launcher command, and exposes Track D's dependency through the centralized `TRACK_D_SPLIT_DEPENDENCY` constant.

To keep downstream checklist/report logic honest, I updated `scripts/run_pipeline.py` to reuse the same Track D blocker constant and added regression coverage in a new `tests/test_pipeline_dispatcher_all_tracks.py` file plus a launcher-order alignment assertion in `tests/test_run_pipeline_launcher.py`.

## Verification

I ran the focused pytest targets for the new dispatcher contract and launcher coverage, then ran the task-plan inline contract assertion to confirm the helper exposes exactly Tracks A–E and preserves Track D's `blocked_by` dependency.

Because this stripped worktree had no ready `python` shim, `pip`, or `pytest`, I created a temporary repo-local `.venv-local` only for verification, ran the checks there, and removed it afterward so the task diff stayed focused on source changes.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `./.venv-local/bin/python -m pytest tests/test_pipeline_dispatcher_all_tracks.py tests/test_run_pipeline_launcher.py` | 0 | ✅ pass | 0.29s |
| 2 | `./.venv-local/bin/python - <<'PY' ... PY` | 0 | ✅ pass | 0.05s |

## Diagnostics

Inspect `scripts.pipeline_dispatcher.get_eda_summary_contract()` to see the ordered Track A–E terminal summary contract that downstream S01 code should consume. The helper now fails loudly with `DispatcherError` if a track loses its terminal `summary_report` stage or stops declaring a markdown completion artifact. Track D's dependency is inspectable both through `TRACK_D_SPLIT_DEPENDENCY` and the helper's `blocked_by` field.

## Deviations

None.

## Known Issues

None in scope. The host shell still lacks a default `python` shim and bundled `pytest`, so future verification in this stripped worktree may need the project runtime-matched venv or a temporary local venv again.

## Files Created/Modified

- `scripts/pipeline_dispatcher.py` — added the dispatcher-derived EDA summary contract helper, canonical launcher command helper, and centralized Track D split dependency constant.
- `scripts/run_pipeline.py` — reused the centralized Track D blocker constant so launcher status logic matches the dispatcher contract.
- `tests/test_pipeline_dispatcher_all_tracks.py` — added regression coverage for Track A–E terminal summary stages, markdown outputs, launcher commands, and failure-on-drift behavior.
- `tests/test_run_pipeline_launcher.py` — added launcher-order alignment coverage against the dispatcher summary contract.
- `.gsd/milestones/M001-4q3lxl/slices/S01/S01-PLAN.md` — added a failure-path verification step for inspectable missing-input diagnostics.
- `.gsd/milestones/M001-4q3lxl/slices/S01/tasks/T01-PLAN.md` — added the missing observability impact section for the new contract surface.
- `.gsd/DECISIONS.md` — recorded the dispatcher-as-source-of-truth decision for the all-track EDA completion checklist.
