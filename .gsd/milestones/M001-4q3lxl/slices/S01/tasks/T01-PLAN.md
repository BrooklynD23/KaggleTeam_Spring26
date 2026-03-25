---
estimated_steps: 4
estimated_files: 4
skills_used:
  - debug-like-expert
  - coding-standards
  - tdd-workflow
  - test
  - verification-loop
---

# T01: Expose the all-track EDA completion contract from the dispatcher

**Slice:** S01 — All-track EDA artifact census and gap closure
**Milestone:** M001-4q3lxl

## Description

Create one reusable, dispatcher-derived contract surface that tells downstream code which final summary stage belongs to each approach, which summary markdown proves completion, and which canonical launcher command should appear in the S01 checklist. This prevents the census layer from hand-maintaining a second manifest that can drift from `PIPELINES`.

## Steps

1. Add a small helper API in `scripts/pipeline_dispatcher.py` that exposes Tracks A–E final summary stages, required final summary outputs, and launcher-oriented ordering from existing `PIPELINES` / approach constants.
2. Ensure the helper preserves current constraints that matter to S01, especially Track D's dependency on `outputs/tables/track_a_s5_candidate_splits.parquet` and the canonical use of `python scripts/run_pipeline.py --approach ...`.
3. Add a new regression file covering the all-track summary contract and extend launcher coverage only where needed to keep the command checklist honest.
4. Run the focused pytest targets and adjust the helper surface until failures clearly identify contract drift.

## Must-Haves

- [ ] The new helper derives its answers from existing dispatcher data structures instead of a copied filename list.
- [ ] Tests fail if any track loses its terminal `summary_report` stage, expected final summary markdown path, or canonical launcher command.
- [ ] Track D's Track-A dependency remains visible to downstream reporting logic.

## Verification

- `python -m pytest tests/test_pipeline_dispatcher_all_tracks.py tests/test_run_pipeline_launcher.py`
- `python - <<'PY'
from scripts import pipeline_dispatcher as dispatcher
contract = dispatcher.get_eda_summary_contract()
assert set(contract) == {dispatcher.APPROACH_TRACK_A, dispatcher.APPROACH_TRACK_B, dispatcher.APPROACH_TRACK_C, dispatcher.APPROACH_TRACK_D, dispatcher.APPROACH_TRACK_E}
assert contract[dispatcher.APPROACH_TRACK_D]["blocked_by"] == ["outputs/tables/track_a_s5_candidate_splits.parquet"]
PY`

## Observability Impact

- New signal: `scripts.pipeline_dispatcher.get_eda_summary_contract()` exposes the ordered Track A–E terminal summary contract that downstream census/report code can inspect directly.
- How to inspect: import the helper in tests or a Python REPL and compare each approach's `final_stage_id`, `summary_markdown`, `required_outputs`, `launcher_command`, and `blocked_by` fields against `PIPELINES`.
- Failure visibility: contract drift now raises a `DispatcherError` when a track no longer ends in `summary_report` or no markdown completion artifact is declared, so downstream checklist/report code fails loudly instead of silently emitting a stale manifest.

## Inputs

- `scripts/pipeline_dispatcher.py` — current source of truth for approaches, stage order, and required outputs
- `scripts/run_pipeline.py` — canonical launcher surface the checklist must reference
- `tests/test_pipeline_dispatcher_tracks_cd.py` — existing dispatcher contract-testing style to extend
- `tests/test_run_pipeline_launcher.py` — existing launcher contract tests and command expectations

## Expected Output

- `scripts/pipeline_dispatcher.py` — reusable all-track EDA summary contract helper(s)
- `tests/test_pipeline_dispatcher_all_tracks.py` — new regression coverage for Tracks A–E terminal summary contract
- `tests/test_run_pipeline_launcher.py` — updated launcher assertions if checklist-facing behavior changes
