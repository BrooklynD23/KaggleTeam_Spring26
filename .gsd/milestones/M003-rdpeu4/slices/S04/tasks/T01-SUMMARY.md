---
id: T01
parent: S04
milestone: M003-rdpeu4
provides:
  - Canonical S04 comparator contract constants + validators for materiality-table schema, manifest status vocabulary, and strict boolean gate typing.
key_files:
  - src/modeling/common/comparator_contract.py
  - src/modeling/common/__init__.py
  - tests/test_m003_comparator_contract.py
  - .gsd/milestones/M003-rdpeu4/slices/S04/tasks/T01-PLAN.md
  - .gsd/milestones/M003-rdpeu4/slices/S04/S04-PLAN.md
key_decisions:
  - Enforced strict boolean gate typing by requiring pandas bool dtype and row-level boolean/null validation for comparator gate columns.
patterns_established:
  - Comparator contracts follow the same machine-readable diagnostics shape used in S01–S03 (`checks`, `missing_columns`, status validator payloads).
observability_surfaces:
  - validate_materiality_table_dataframe() and validate_comparator_manifest_status() structured diagnostics consumed by runtime/tests.
duration: 45m
verification_result: passed
completed_at: 2026-03-23T14:50:00-07:00
blocker_discovered: false
---

# T01: Define comparator contract and materiality schema validators

**Added canonical S04 comparator contract module with strict materiality schema/status/boolean validators and regression tests.**

## What Happened

I first fixed the pre-flight documentation gap by adding `## Observability Impact` to `T01-PLAN.md` so this task explicitly defines new diagnostics surfaces. I then followed TDD: created `tests/test_m003_comparator_contract.py` first (red on missing exports), implemented `src/modeling/common/comparator_contract.py` with schema constants, status vocabulary lock (`ready_for_closeout`, `blocked_upstream`), dataframe validation, and status validation, and finally exported all comparator helpers via `src/modeling/common/__init__.py`.

The dataframe validator now deterministically reports required-column drift, invalid boolean gate dtypes, malformed gate rows, and check-level pass/fail diagnostics. I marked T01 complete in `S04-PLAN.md`.

## Verification

- Task-level verification passed:
  - `pytest tests/test_m003_comparator_contract.py -q`
  - `pytest tests/test_m003_comparator_contract.py -k "missing_columns or invalid_status or boolean" -q`
- Observability impact was directly verified via a Python probe that asserts comparator validator outputs include expected diagnostics keys and invalid-status checks.
- Slice-level verification commands were run; expected failures remain because T02/T03 runtime/tests/artifacts are not implemented yet.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_comparator_contract.py -q` | 0 | ✅ pass | 5.58s |
| 2 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_comparator_contract.py -k "missing_columns or invalid_status or boolean" -q` | 0 | ✅ pass | 5.51s |
| 3 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_comparator_contract.py tests/test_m003_track_a_stronger_comparator.py tests/test_m003_comparator_handoff_contract.py -q` | 4 | ❌ fail (expected pre-T02/T03) | 1.94s |
| 4 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_a.stronger_comparator --config configs/track_a.yaml --intake-dir outputs/modeling/track_a/audit_intake --fairness-dir outputs/modeling/track_e/fairness_audit --candidate-metrics tests/fixtures/m003_candidate_metrics.csv --output-dir outputs/modeling/track_a/stronger_comparator` | 1 | ❌ fail (expected pre-T02 runtime) | 0.05s |
| 5 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY' ... comparator bundle assertions ... PY` | 1 | ❌ fail (expected missing comparator artifacts pre-T02) | 3.54s |
| 6 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_a_stronger_comparator.py -k "blocked_upstream or no_fairness_signal" -q` | 4 | ❌ fail (expected pre-T02 tests) | 1.92s |
| 7 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY' ... direct comparator observability probe ... PY` | 0 | ✅ pass | 3.56s |

## Diagnostics

- Contract metadata surface: `src.modeling.common.comparator_contract.comparator_contract_spec()`.
- Table diagnostics surface: `validate_materiality_table_dataframe(df)` returns `missing_columns`, `invalid_boolean_gate_dtypes`, `malformed_gate_flags`, and check-level statuses.
- Manifest diagnostics surface: `validate_comparator_manifest_status(status)` returns explicit invalid status payload with allowed vocabulary.
- Shared import surface for runtime/tests: `src.modeling.common` exports all comparator contract helpers.

## Deviations

- Applied an unplanned but required pre-flight fix: added `## Observability Impact` to `T01-PLAN.md` before implementation.

## Known Issues

- Full slice verification remains red until T02/T03 add comparator runtime, handoff tests, and generated comparator artifacts.

## Files Created/Modified

- `src/modeling/common/comparator_contract.py` — Added canonical comparator schema/status constants and validators.
- `src/modeling/common/__init__.py` — Exported comparator contract helpers/constants on shared modeling surface.
- `tests/test_m003_comparator_contract.py` — Added regression coverage for schema drift, status drift, and strict boolean gate typing.
- `.gsd/milestones/M003-rdpeu4/slices/S04/tasks/T01-PLAN.md` — Added `## Observability Impact` section per pre-flight requirement.
- `.gsd/milestones/M003-rdpeu4/slices/S04/S04-PLAN.md` — Marked T01 as complete (`[x]`).
