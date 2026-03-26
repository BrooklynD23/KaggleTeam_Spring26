---
id: S04
parent: M003-rdpeu4
milestone: M003-rdpeu4
provides:
  - Executable Track A stronger/combined comparator runtime (`python -m src.modeling.track_a.stronger_comparator`) that consumes S01 intake + S02 fairness artifacts and emits canonical materiality decision bundles.
  - Shared comparator contract validators for schema/status/strict-boolean gates with deterministic diagnostics payloads.
  - Handoff continuity and replay surfaces (tests + docs + UAT) that lock `baseline_anchor`/`split_context` and canonical status semantics for S05 closeout.
requires:
  - slice: M003-rdpeu4/S01
    provides: Canonical upstream scored intake with baseline anchor + split context.
  - slice: M003-rdpeu4/S02
    provides: Canonical fairness bundle and disparity context used in comparator adoption gating.
affects:
  - M003-rdpeu4/S05
  - M004-fjc2zy
key_files:
  - src/modeling/common/comparator_contract.py
  - src/modeling/common/__init__.py
  - src/modeling/track_a/stronger_comparator.py
  - src/modeling/track_a/__init__.py
  - configs/track_a.yaml
  - src/modeling/README.md
  - tests/test_m003_comparator_contract.py
  - tests/test_m003_track_a_stronger_comparator.py
  - tests/test_m003_comparator_handoff_contract.py
  - tests/fixtures/m003_candidate_metrics.csv
  - .gsd/milestones/M003-rdpeu4/slices/S04/S04-UAT.md
  - outputs/modeling/track_a/stronger_comparator/materiality_table.parquet
  - outputs/modeling/track_a/stronger_comparator/manifest.json
  - outputs/modeling/track_a/stronger_comparator/validation_report.json
key_decisions:
  - D035: S04 comparator runtime is the canonical stronger-model gate with statuses `ready_for_closeout`/`blocked_upstream` and do-not-adopt encoded through `adopt_recommendation=false` + `decision_reason`.
  - D036: Comparator CLI returns exit code 0 after writing blocked bundles; automation must read manifest/validation statuses.
  - D037: Comparator handoff must preserve exact `baseline_anchor`/`split_context` continuity in both ready and blocked outcomes.
patterns_established:
  - Contract-first delivery pattern: shared contract validators → runtime gate logic → handoff continuity tests.
  - Deterministic blocked-bundle semantics: even blocked runs emit contract-valid artifacts for downstream triage.
  - Fairness-aware adoption gate: metric/runtime gains alone cannot auto-adopt when fairness signal is unavailable.
observability_surfaces:
  - outputs/modeling/track_a/stronger_comparator/manifest.json
  - outputs/modeling/track_a/stronger_comparator/validation_report.json
  - outputs/modeling/track_a/stronger_comparator/materiality_table.parquet
  - tests/test_m003_track_a_stronger_comparator.py
  - tests/test_m003_comparator_handoff_contract.py
  - src/modeling/README.md
  - .gsd/milestones/M003-rdpeu4/slices/S04/S04-UAT.md
duration: 3h35m
verification_result: passed
completed_at: 2026-03-23
---

# S04: Stronger/combined comparator with materiality gate

**S04 closed successfully.** The slice now provides a canonical stronger-model comparator that is machine-readable, fairness-aware, and handoff-safe for S05/M004 consumers.

## What Happened

S04 integrated all three planned tasks into one deterministic comparator surface:

1. **T01 contract layer**
   - Added `src/modeling/common/comparator_contract.py` and exports in `src/modeling/common/__init__.py`.
   - Locked required materiality schema, strict bool gate typing, and allowed status vocabulary.
   - Added deterministic diagnostics for missing columns, malformed boolean gates, and status drift.

2. **T02 runtime layer**
   - Implemented `python -m src.modeling.track_a.stronger_comparator`.
   - Runtime now gates intake/fairness/candidate inputs, computes metric and runtime deltas, and evaluates fairness context before producing `adopt_recommendation`.
   - Writes canonical artifacts on both branches:
     - `ready_for_closeout` (+ pass validation)
     - `blocked_upstream` (+ fail validation + empty-but-contract-valid table)
   - Config thresholds now live in `configs/track_a.yaml` (`metric_name`, `metric_direction`, `min_metric_gain`, `max_runtime_multiplier`).

3. **T03 handoff closure**
   - Added `tests/test_m003_comparator_handoff_contract.py` for continuity/schema/redaction regressions.
   - Updated `src/modeling/README.md` with canonical command, status semantics, and output contract.
   - Authored concrete S04 replay/triage script in `.gsd/milestones/M003-rdpeu4/slices/S04/S04-UAT.md`.

As closer, I reran all slice-plan verification commands, confirmed observability surfaces from live artifacts, updated requirement evidence (R010/R012), recorded missing decision D037, added one useful comparator continuity gotcha to `.gsd/KNOWLEDGE.md`, refreshed `.gsd/PROJECT.md`, and marked S04 complete in the roadmap.

## Verification

All slice-plan verification checks passed in this worktree:

| # | Command | Result |
|---|---|---|
| 1 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_comparator_contract.py tests/test_m003_track_a_stronger_comparator.py tests/test_m003_comparator_handoff_contract.py -q` | ✅ 13 passed |
| 2 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_a.stronger_comparator --config configs/track_a.yaml --intake-dir outputs/modeling/track_a/audit_intake --fairness-dir outputs/modeling/track_e/fairness_audit --candidate-metrics tests/fixtures/m003_candidate_metrics.csv --output-dir outputs/modeling/track_a/stronger_comparator` | ✅ exit 0; bundle regenerated |
| 3 | Slice-plan artifact assertion snippet (`materiality_table.parquet` + `manifest.json` + `validation_report.json` schema/status/redaction checks) | ✅ prints `m003 s04 comparator bundle verified` |
| 4 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_a_stronger_comparator.py -k "blocked_upstream or no_fairness_signal" -q` | ✅ 2 passed, 1 deselected |

## Observability / Diagnostics Confirmed

Declared S04 observability surfaces are live and machine-readable:

- `outputs/modeling/track_a/stronger_comparator/manifest.json`
  - `status: ready_for_closeout`
  - decision snapshot including `material_improvement`, `runtime_within_budget`, `fairness_signal_available`, `adopt_recommendation`, `decision_reason`
  - continuity payloads: `baseline_anchor`, `split_context`
- `outputs/modeling/track_a/stronger_comparator/validation_report.json`
  - phase timeline (`load_config`, `load_upstream`, `validate_upstream`, `evaluate_materiality`, `write_bundle`)
  - check-level diagnostics and missing input visibility
- `outputs/modeling/track_a/stronger_comparator/materiality_table.parquet`
  - required schema + strict bool dtypes for all gate columns

Current replay state is intentionally **ready but do-not-adopt**:
- `metric_gain = 0.05` and `runtime_multiplier = 1.12` both pass threshold gates
- fairness disparity context has zero rows in this worktree replay
- `fairness_signal_available = false`, so `adopt_recommendation = false` with `decision_reason = do_not_adopt_no_fairness_signal`

## Requirements Advanced

- **R010 (active):** advanced to partially validated with passing comparator contract/runtime/handoff checks and canonical materiality bundle outputs.
- **R012 (active):** continuity support advanced with comparator continuity tests and canonical replay/triage docs for downstream trust-story assembly.

## Requirements Validated

- none (full milestone-level closure still depends on S05 integrated rerun + escalation disposition).

## Known Limitations

- In the current replay, fairness signal is absent (zero disparity rows), so recommendation is deterministic do-not-adopt despite metric/runtime improvement.
- S04 does not make compute escalation decisions (`local_sufficient` vs `overflow_required`); that remains S05 scope.

## Follow-ups for Next Slices

1. **S05:** run integrated closeout rerun across S01/S02/S03/S04 and publish final escalation decision artifact.
2. **S05 automation:** treat comparator statuses from `manifest.json`/`validation_report.json` as truth; do not key off process exit code alone.
3. **M004 consumers:** use `outputs/modeling/track_a/stronger_comparator/` as authoritative stronger-model adoption evidence surface.

## Files Created/Modified

- `src/modeling/common/comparator_contract.py`
- `src/modeling/common/__init__.py`
- `src/modeling/track_a/stronger_comparator.py`
- `src/modeling/track_a/__init__.py`
- `configs/track_a.yaml`
- `src/modeling/README.md`
- `tests/test_m003_comparator_contract.py`
- `tests/test_m003_track_a_stronger_comparator.py`
- `tests/test_m003_comparator_handoff_contract.py`
- `tests/fixtures/m003_candidate_metrics.csv`
- `.gsd/milestones/M003-rdpeu4/slices/S04/S04-UAT.md`
- `.gsd/milestones/M003-rdpeu4/slices/S04/S04-SUMMARY.md`
- `outputs/modeling/track_a/stronger_comparator/materiality_table.parquet`
- `outputs/modeling/track_a/stronger_comparator/manifest.json`
- `outputs/modeling/track_a/stronger_comparator/validation_report.json`
- `.gsd/REQUIREMENTS.md`
- `.gsd/DECISIONS.md` (D037)
- `.gsd/KNOWLEDGE.md`
- `.gsd/PROJECT.md`
- `.gsd/milestones/M003-rdpeu4/M003-rdpeu4-ROADMAP.md`

## Forward Intelligence

### What the next slice should know
S04 locks one canonical comparator command/path and status vocabulary. Downstream reruns should consume bundle status and decision payloads directly rather than inferring readiness from logs or exit codes.

### What is most fragile
- Continuity payload drift (`baseline_anchor`, `split_context`) between upstream artifacts and comparator outputs.
- Any change that upcasts gate booleans away from strict bool dtype.

### Authoritative triage surfaces
- `outputs/modeling/track_a/stronger_comparator/manifest.json`
- `outputs/modeling/track_a/stronger_comparator/validation_report.json`
- `tests/test_m003_track_a_stronger_comparator.py`
- `tests/test_m003_comparator_handoff_contract.py`
