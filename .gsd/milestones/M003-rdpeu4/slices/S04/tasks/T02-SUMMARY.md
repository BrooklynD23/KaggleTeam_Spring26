---
id: T02
parent: S04
milestone: M003-rdpeu4
provides:
  - Canonical S04 stronger comparator runtime + CLI that consumes S01/S02 bundles and candidate metrics, then emits deterministic ready/blocked materiality bundles with adoption gating diagnostics.
key_files:
  - src/modeling/track_a/stronger_comparator.py
  - src/modeling/track_a/__init__.py
  - configs/track_a.yaml
  - tests/test_m003_track_a_stronger_comparator.py
  - tests/fixtures/m003_candidate_metrics.csv
  - outputs/modeling/track_a/stronger_comparator/materiality_table.parquet
  - outputs/modeling/track_a/stronger_comparator/manifest.json
  - outputs/modeling/track_a/stronger_comparator/validation_report.json
  - .gsd/milestones/M003-rdpeu4/slices/S04/S04-PLAN.md
  - .gsd/KNOWLEDGE.md
key_decisions:
  - D036: S04 comparator returns exit code 0 after writing blocked_upstream artifacts; readiness is conveyed via manifest/validation statuses.
patterns_established:
  - Follow S03-style deterministic blocked bundles (empty contract-valid parquet + machine-readable manifest/validation diagnostics) while keeping no-fairness-signal as ready/do-not-adopt.
observability_surfaces:
  - outputs/modeling/track_a/stronger_comparator/{materiality_table.parquet,manifest.json,validation_report.json} with phase/check/threshold/decision payloads.
duration: 1h 55m
verification_result: passed
completed_at: 2026-03-23T16:59:30-07:00
blocker_discovered: false
---

# T02: Implement stronger comparator runtime with fairness-aware materiality gate

**Implemented Track A stronger comparator runtime, fairness-aware adoption gating, and deterministic ready/blocked S04 bundle outputs with regression coverage.**

## What Happened

I followed TDD for this task: first added `tests/test_m003_track_a_stronger_comparator.py` and `tests/fixtures/m003_candidate_metrics.csv`, confirmed the expected red state (`ModuleNotFoundError` for the not-yet-created runtime), then implemented `src/modeling/track_a/stronger_comparator.py` and iterated to green.

Implementation shipped:
- New CLI/runtime: `python -m src.modeling.track_a.stronger_comparator --config --intake-dir --fairness-dir --candidate-metrics --output-dir`.
- Upstream readiness gates for S01 intake status/schema, S02 fairness status/schema, baseline anchor availability, comparator config validity, and candidate-metrics schema/metric/runtime extraction.
- Materiality/runtime/fairness gate computation with required S04 fields:
  - baseline vs candidate metric/runtime
  - `metric_gain`, `runtime_delta_seconds`, threshold echoes
  - boolean gates (`material_improvement`, `runtime_within_budget`, `fairness_context_ready`, `fairness_signal_available`)
  - `adopt_recommendation` and machine-readable `decision_reason`
- Deterministic bundle writing on both branches:
  - `ready_for_closeout` with pass validation
  - `blocked_upstream` with fail validation and empty-but-contract-valid `materiality_table.parquet`
- Required no-fairness-signal behavior: remains `ready_for_closeout` with `adopt_recommendation=false` and `decision_reason=do_not_adopt_no_fairness_signal`.
- Track A export wiring extended in `src/modeling/track_a/__init__.py` (`run_stronger_comparator`, `main_stronger_comparator`).
- Config thresholds added to `configs/track_a.yaml` under `modeling.stronger_comparator`.

I also recorded the operability decision (D036) and appended a knowledge-log entry documenting comparator exit/status semantics and no-fairness-signal behavior.

## Verification

Verified via task-level and slice-level commands:
- New T02 regression suite passes (ready/adopt, ready/no-fairness-signal/do-not-adopt, blocked_upstream).
- Runtime command produces canonical bundle files and satisfies schema/type/redaction checks.
- Blocked/no-fairness targeted pytest subset passes.
- Full S04 slice pytest command is still partially red due missing T03-owned `tests/test_m003_comparator_handoff_contract.py` (expected for intermediate task state).

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_a_stronger_comparator.py -q` (pre-implementation red check) | 2 | ❌ fail (expected TDD red: missing runtime module) | 6.30s |
| 2 | `/usr/bin/time -f 'DURATION:%e' /mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_comparator_contract.py tests/test_m003_track_a_stronger_comparator.py tests/test_m003_comparator_handoff_contract.py -q` | 4 | ❌ fail (expected pre-T03: handoff test file not yet present) | 1.93s |
| 3 | `/usr/bin/time -f 'DURATION:%e' /mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_a_stronger_comparator.py -q` | 0 | ✅ pass | 5.88s |
| 4 | `/usr/bin/time -f 'DURATION:%e' /mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_a.stronger_comparator --config configs/track_a.yaml --intake-dir outputs/modeling/track_a/audit_intake --fairness-dir outputs/modeling/track_e/fairness_audit --candidate-metrics tests/fixtures/m003_candidate_metrics.csv --output-dir outputs/modeling/track_a/stronger_comparator` | 0 | ✅ pass | 3.85s |
| 5 | `/usr/bin/time -f 'DURATION:%e' test -f outputs/modeling/track_a/stronger_comparator/materiality_table.parquet && test -f outputs/modeling/track_a/stronger_comparator/manifest.json && test -f outputs/modeling/track_a/stronger_comparator/validation_report.json` | 0 | ✅ pass | 0.01s |
| 6 | `/usr/bin/time -f 'DURATION:%e' /mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY' ... m003 s04 comparator bundle assertions ... PY` | 0 | ✅ pass | 3.83s |
| 7 | `/usr/bin/time -f 'DURATION:%e' /mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_a_stronger_comparator.py -k "blocked_upstream or no_fairness_signal" -q` | 0 | ✅ pass | 5.86s |
| 8 | `/usr/bin/time -f 'DURATION:%e' /mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_comparator_contract.py tests/test_m003_track_a_stronger_comparator.py -q` | 0 | ✅ pass | 5.97s |

## Diagnostics

- Primary inspection path: `outputs/modeling/track_a/stronger_comparator/`.
- `manifest.json` now surfaces status, phase, thresholds, decision snapshot, continuity fields (`split_context`, `baseline_anchor`), and upstream paths.
- `validation_report.json` now surfaces phase timeline (`load_config`, `load_upstream`, `validate_upstream`, `evaluate_materiality`, `write_bundle`), check-level failures, and output artifacts.
- `materiality_table.parquet` enforces canonical schema + strict bool gate dtypes via shared comparator contract validator.

## Deviations

- Added one explicit project-level decision entry (D036) and one knowledge-log entry because exit/status semantics for blocked comparator runs are non-obvious and relevant for downstream automation.

## Known Issues

- Full slice verification command still fails at this task boundary because `tests/test_m003_comparator_handoff_contract.py` is a T03 deliverable and is not present yet.

## Files Created/Modified

- `src/modeling/track_a/stronger_comparator.py` — Added S04 comparator runtime CLI, upstream gates, materiality/fairness decision logic, and deterministic bundle emission.
- `src/modeling/track_a/__init__.py` — Added stronger-comparator proxy exports (`run_stronger_comparator`, `main_stronger_comparator`).
- `configs/track_a.yaml` — Added comparator threshold configuration (`metric_name`, `metric_direction`, `min_metric_gain`, `max_runtime_multiplier`).
- `tests/test_m003_track_a_stronger_comparator.py` — Added regression coverage for ready/adopt, ready/no-fairness-signal/do-not-adopt, and blocked_upstream branches.
- `tests/fixtures/m003_candidate_metrics.csv` — Added canonical candidate metrics replay fixture.
- `outputs/modeling/track_a/stronger_comparator/materiality_table.parquet` — Generated canonical comparator materiality table artifact.
- `outputs/modeling/track_a/stronger_comparator/manifest.json` — Generated comparator readiness/decision manifest.
- `outputs/modeling/track_a/stronger_comparator/validation_report.json` — Generated comparator validation/diagnostic payload.
- `.gsd/milestones/M003-rdpeu4/slices/S04/S04-PLAN.md` — Marked T02 as complete (`[x]`).
- `.gsd/DECISIONS.md` — Appended D036 documenting blocked-branch exit/status semantics for S04 comparator automation.
- `.gsd/KNOWLEDGE.md` — Added S04 comparator status/exit/no-fairness-signal operational gotcha entry.
