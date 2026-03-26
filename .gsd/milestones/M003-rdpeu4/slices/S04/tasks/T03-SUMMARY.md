---
id: T03
parent: S04
milestone: M003-rdpeu4
provides:
  - S04 handoff continuity regression coverage plus canonical replay documentation for ready and blocked comparator outcomes.
key_files:
  - tests/test_m003_comparator_handoff_contract.py
  - src/modeling/README.md
  - .gsd/milestones/M003-rdpeu4/slices/S04/S04-UAT.md
  - .gsd/milestones/M003-rdpeu4/slices/S04/tasks/T03-PLAN.md
  - .gsd/milestones/M003-rdpeu4/slices/S04/S04-PLAN.md
key_decisions:
  - Locked S04 continuity by asserting comparator `manifest.json` preserves exact `split_context` and `baseline_anchor` from S02 fairness manifest in both ready and blocked branches.
  - Documented one canonical S04 CLI replay path (`outputs/modeling/track_a/stronger_comparator`) and explicit interpretation of `ready_for_closeout` vs `blocked_upstream` plus `adopt_recommendation` semantics.
patterns_established:
  - Follow existing M003 handoff-contract test style: synthesize minimal upstream bundles in `tmp_path`, run runtime CLI, then assert manifest schema/status, continuity anchors, table schema, and redaction constraints.
observability_surfaces:
  - `outputs/modeling/track_a/stronger_comparator/{materiality_table.parquet,manifest.json,validation_report.json}`
  - `tests/test_m003_comparator_handoff_contract.py` (ready + blocked continuity/contract diagnostics)
  - `.gsd/milestones/M003-rdpeu4/slices/S04/S04-UAT.md` replay and triage commands
duration: 55m
verification_result: passed
completed_at: 2026-03-23T17:23:36-07:00
blocker_discovered: false
---

# T03: Lock S04 handoff continuity and canonical replay docs for S05

**Added S04 comparator handoff contract tests and canonical README/UAT replay docs that lock continuity, status semantics, and ready/blocked triage paths.**

## What Happened

Implemented `tests/test_m003_comparator_handoff_contract.py` with three regression checks: (1) required manifest keys + status vocabulary + fairness-anchor continuity, (2) required `materiality_table` schema + strict boolean gate dtypes + redaction, and (3) blocked-upstream branch continuity + contract-valid empty table shape.

Extended `src/modeling/README.md` with one canonical S04 `stronger_comparator` command, required inputs, canonical output layout, and explicit downstream interpretation of `ready_for_closeout`/`blocked_upstream` and `adopt_recommendation`.

Authored `.gsd/milestones/M003-rdpeu4/slices/S04/S04-UAT.md` with executable ready and blocked replay flows, concrete assertion snippets, and triage checklist anchored to `manifest.json`/`validation_report.json`.

Applied the required pre-flight correction by adding `## Observability Impact` to `T03-PLAN.md`, and marked T03 complete in `S04-PLAN.md`.

## Verification

Ran the full S04 comparator verification stack (tests + runtime + artifact assertions + targeted blocked/no-fairness branch tests) and executed the docs keyword contract grep. All checks passed.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_comparator_contract.py tests/test_m003_track_a_stronger_comparator.py tests/test_m003_comparator_handoff_contract.py -q` | 0 | ✅ pass | 6.16s |
| 2 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_a.stronger_comparator --config configs/track_a.yaml --intake-dir outputs/modeling/track_a/audit_intake --fairness-dir outputs/modeling/track_e/fairness_audit --candidate-metrics tests/fixtures/m003_candidate_metrics.csv --output-dir outputs/modeling/track_a/stronger_comparator` | 0 | ✅ pass | 3.78s |
| 3 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY' ... comparator bundle assertions ... PY` | 0 | ✅ pass | 3.68s |
| 4 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_a_stronger_comparator.py -k "blocked_upstream or no_fairness_signal" -q` | 0 | ✅ pass | 5.76s |
| 5 | `rg -n "stronger_comparator|materiality_table.parquet|ready_for_closeout|blocked_upstream|adopt_recommendation" src/modeling/README.md .gsd/milestones/M003-rdpeu4/slices/S04/S04-UAT.md` | 0 | ✅ pass | 0.00s |

## Diagnostics

Primary inspection surface remains `outputs/modeling/track_a/stronger_comparator/`:
- `manifest.json` for status vocabulary, continuity anchors, decision payload, and upstream paths.
- `validation_report.json` for phase-local failures (`load_upstream`, `validate_upstream`, etc.), check-level diagnostics, and missing inputs.
- `materiality_table.parquet` for machine-readable gate outcomes and `adopt_recommendation`.

For deterministic replay/triage, run the commands in `.gsd/milestones/M003-rdpeu4/slices/S04/S04-UAT.md`.

## Deviations

- Added `## Observability Impact` to `.gsd/milestones/M003-rdpeu4/slices/S04/tasks/T03-PLAN.md` before implementation, per pre-flight requirement.

## Known Issues

- none

## Files Created/Modified

- `tests/test_m003_comparator_handoff_contract.py` — New S04 handoff regression tests for continuity anchors, status vocabulary, schema/redaction constraints, and blocked branch behavior.
- `src/modeling/README.md` — Added canonical S04 comparator command, inputs, output contract, and status/adoption interpretation guidance.
- `.gsd/milestones/M003-rdpeu4/slices/S04/S04-UAT.md` — Added executable ready/blocked replay and triage checklist.
- `.gsd/milestones/M003-rdpeu4/slices/S04/tasks/T03-PLAN.md` — Added Observability Impact section required by pre-flight gate.
- `.gsd/milestones/M003-rdpeu4/slices/S04/S04-PLAN.md` — Marked T03 as complete (`[x]`).
