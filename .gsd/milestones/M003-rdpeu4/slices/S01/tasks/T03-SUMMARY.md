---
id: T03
parent: S01
milestone: M003-rdpeu4
provides:
  - Downstream handoff regression coverage that locks Track A intake readiness status, manifest anchors, and minimum scored-intake columns for S02/S03/S04
  - Canonical modeling intake documentation with one authoritative `audit_intake` command, required inputs, and bundle layout
  - Replayable S01 UAT runbook that executes slice verification commands in milestone-local context
key_files:
  - tests/test_m003_intake_handoff_contract.py
  - src/modeling/README.md
  - .gsd/milestones/M003-rdpeu4/slices/S01/S01-UAT.md
  - .gsd/milestones/M003-rdpeu4/slices/S01/tasks/T03-PLAN.md
  - .gsd/milestones/M003-rdpeu4/slices/S01/S01-PLAN.md
key_decisions:
  - Enforced a single downstream intake handoff surface (`outputs/modeling/track_a/audit_intake/`) via both regression assertions and operator-facing docs/runbook guidance
patterns_established:
  - Handoff tests validate readiness (`ready_for_fairness_audit`), manifest anchor presence (`split_context`, `baseline_anchor`), and minimum downstream schema before fairness/mitigation/comparator slices execute
observability_surfaces:
  - tests/test_m003_intake_handoff_contract.py
  - outputs/modeling/track_a/audit_intake/manifest.json
  - outputs/modeling/track_a/audit_intake/validation_report.json
  - src/modeling/README.md
  - .gsd/milestones/M003-rdpeu4/slices/S01/S01-UAT.md
duration: 45m
verification_result: passed
completed_at: 2026-03-23T14:56:30-07:00
blocker_discovered: false
---

# T03: Lock downstream handoff wiring with intake contract regression and runbook updates

**Added a downstream handoff regression test plus canonical intake/UAT docs so S02/S03/S04 consume one validated Track A audit_intake bundle without schema/path guesswork.**

## What Happened

I first applied the required pre-flight fix by adding `## Observability Impact` to `.gsd/milestones/M003-rdpeu4/slices/S01/tasks/T03-PLAN.md`.

Then I implemented the planned deliverables:

1. Created `tests/test_m003_intake_handoff_contract.py` with regression coverage that builds a real intake bundle in a temp workspace and asserts:
   - required manifest fields are present,
   - readiness status is `ready_for_fairness_audit`,
   - baseline/split anchor surfaces are present for downstream wiring,
   - scored intake contains the required downstream columns and no forbidden text/demographic columns.
2. Created `src/modeling/README.md` to document the canonical `python -m src.modeling.track_a.audit_intake ...` command, required inputs, and authoritative bundle layout (`scored_intake.parquet`, `manifest.json`, `validation_report.json`).
3. Created `.gsd/milestones/M003-rdpeu4/slices/S01/S01-UAT.md` as a replayable runbook with concrete commands and expected pass indicators.
4. Marked T03 complete in `.gsd/milestones/M003-rdpeu4/slices/S01/S01-PLAN.md`.

## Verification

I ran the full S01 slice verification commands plus the T03 documentation grep check and an explicit observability-signal assertion against generated JSON artifacts.

All checks passed.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_audit_intake_contract.py tests/test_m003_track_a_audit_intake.py tests/test_m003_intake_handoff_contract.py` | 0 | ✅ pass | 8s |
| 2 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_a.audit_intake --config configs/track_a.yaml --predictions outputs/modeling/track_a/predictions_test.parquet --metrics outputs/modeling/track_a/metrics.csv --output-dir outputs/modeling/track_a/audit_intake` | 0 | ✅ pass | 4s |
| 3 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY' ... assert manifest['status'] == 'ready_for_fairness_audit'; assert validation['status'] == 'pass' ... PY` | 0 | ✅ pass | 3s |
| 4 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_a_audit_intake.py -k missing_predictions_emits_diagnostics` | 0 | ✅ pass | 7s |
| 5 | `rg -n "audit_intake|ready_for_fairness_audit|scored_intake.parquet|validation_report.json" src/modeling/README.md .gsd/milestones/M003-rdpeu4/slices/S01/S01-UAT.md` | 0 | ✅ pass | 0s |
| 6 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY' ... assert row/null-count and required phases exist in validation/manifest JSON ... PY` | 0 | ✅ pass | 0s |

## Diagnostics

- Regression drift alarm: `tests/test_m003_intake_handoff_contract.py`
- Runtime handoff state: `outputs/modeling/track_a/audit_intake/manifest.json`
- Runtime validation state: `outputs/modeling/track_a/audit_intake/validation_report.json`
- Operator entrypoint/runbook: `src/modeling/README.md` and `.gsd/milestones/M003-rdpeu4/slices/S01/S01-UAT.md`

## Deviations

- The default `python` interpreter in this environment does not include `pytest`, so verification commands were run with the project interpreter at `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python` while preserving the exact command semantics.
- `src/modeling/README.md` did not exist in this worktree, so it was created as a new authoritative modeling handoff doc.

## Known Issues

- None.

## Files Created/Modified

- `tests/test_m003_intake_handoff_contract.py` — Added downstream handoff regression test for manifest readiness/anchors and minimum scored-intake schema.
- `src/modeling/README.md` — Added canonical Track A intake command, input contract, and output bundle layout for downstream slices.
- `.gsd/milestones/M003-rdpeu4/slices/S01/S01-UAT.md` — Added milestone-local S01 replay runbook and expected outcomes.
- `.gsd/milestones/M003-rdpeu4/slices/S01/tasks/T03-PLAN.md` — Added required `## Observability Impact` section.
- `.gsd/milestones/M003-rdpeu4/slices/S01/S01-PLAN.md` — Marked T03 checkbox complete.
