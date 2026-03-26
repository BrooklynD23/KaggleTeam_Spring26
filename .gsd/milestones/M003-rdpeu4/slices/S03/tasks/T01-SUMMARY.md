---
id: T01
parent: S03
milestone: M003-rdpeu4
provides:
  - Canonical S03 mitigation contract module with required pre/post delta schema, status vocabulary, and deterministic validator diagnostics.
key_files:
  - src/modeling/common/mitigation_contract.py
  - src/modeling/common/__init__.py
  - tests/test_m003_mitigation_contract.py
  - .gsd/milestones/M003-rdpeu4/slices/S03/tasks/T01-PLAN.md
key_decisions:
  - Kept mitigation contract validation centralized in `src/modeling/common/mitigation_contract.py` and exported through `src.modeling.common` to prevent runtime/test schema drift.
patterns_established:
  - Contract validators emit structured `checks` plus row-level malformed-threshold diagnostics (`row_index`, `column`, `reason`) for fail-closed debugging.
observability_surfaces:
  - mitigation_contract_spec/validate_pre_post_delta_dataframe/validate_mitigation_manifest_status payloads with status, checks, missing_columns, malformed_threshold_flags, and invalid_status.
duration: 55m
verification_result: passed
completed_at: 2026-03-23T14:06:00-07:00
blocker_discovered: false
---

# T01: Define mitigation bundle contract with threshold-delta schema and blocked vocab

**Added a canonical mitigation contract module and regression tests that lock pre/post delta schema, blocked status vocabulary, and strict threshold-flag typing.**

## What Happened

Implemented `src/modeling/common/mitigation_contract.py` with S03 schema/version metadata, required `pre_post_delta` columns, mitigation manifest statuses (`ready_for_closeout`, `blocked_upstream`, `blocked_insufficient_signal`), and two validators:
- `validate_pre_post_delta_dataframe(...)` for required columns + strict boolean threshold flags.
- `validate_mitigation_manifest_status(...)` for explicit status-vocabulary enforcement.

Updated `src/modeling/common/__init__.py` to export mitigation contract constants/helpers from a single import surface for runtime/tests.

Added `tests/test_m003_mitigation_contract.py` (TDD-first) covering:
- Contract metadata + status vocabulary stability.
- Pass-path validation.
- Missing-column fail diagnostics.
- Malformed threshold booleans (`non_boolean`, `null_not_allowed`) with deterministic row/column payloads.
- Invalid and valid manifest status handling.

Per pre-flight requirement, patched `.gsd/milestones/M003-rdpeu4/slices/S03/tasks/T01-PLAN.md` to add `## Observability Impact`.

## Verification

Executed task-level verification commands and confirmed both pass. Also ran adjacent S01/S02 contract suites to ensure common export changes did not regress existing behavior.

Executed all slice-level verification commands for this intermediate task; as expected, integration checks that depend on T02/T03 runtime/tests currently fail due missing module/files.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_mitigation_contract.py -q` | 0 | ✅ pass | 5.40s |
| 2 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_mitigation_contract.py -k "missing_columns or invalid_status or threshold" -q` | 0 | ✅ pass | 5.40s |
| 3 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_fairness_audit_contract.py -q` | 0 | ✅ pass | 2.27s |
| 4 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_audit_intake_contract.py -q` | 0 | ✅ pass | 2.30s |
| 5 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_mitigation_contract.py tests/test_m003_track_e_mitigation_experiment.py tests/test_m003_mitigation_handoff_contract.py -q` | 4 | ❌ fail | 1.91s |
| 6 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.mitigation_experiment --config configs/track_e.yaml --intake-dir outputs/modeling/track_a/audit_intake --fairness-dir outputs/modeling/track_e/fairness_audit --output-dir outputs/modeling/track_e/mitigation_experiment` | 1 | ❌ fail | 0.06s |
| 7 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY' ... PY` (slice artifact assertion snippet) | 1 | ❌ fail | 3.44s |
| 8 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_e_mitigation_experiment.py -k "blocked_upstream or insufficient_signal" -q` | 4 | ❌ fail | 1.93s |

## Diagnostics

Future agents can inspect mitigation contract behavior directly via:
- `src.modeling.common.mitigation_contract.mitigation_contract_spec()`
- `src.modeling.common.mitigation_contract.validate_pre_post_delta_dataframe(df)`
- `src.modeling.common.mitigation_contract.validate_mitigation_manifest_status(status)`

Failure payloads are explicit and machine-readable:
- `missing_columns`
- `malformed_threshold_flags` with row/column/reason
- `invalid_status` + `allowed_statuses`
- check-level pass/fail under `checks`

## Deviations

None.

## Known Issues

- Slice-level integration/runtime checks are still failing because T02/T03 deliverables are not implemented yet (`src.modeling.track_e.mitigation_experiment` and related tests/artifacts are intentionally absent at T01 stage).

## Files Created/Modified

- `src/modeling/common/mitigation_contract.py` — Added canonical S03 mitigation schema constants and validators.
- `src/modeling/common/__init__.py` — Exported mitigation contract helpers/constants for single-surface imports.
- `tests/test_m003_mitigation_contract.py` — Added regression suite for schema/status/threshold contract behavior.
- `.gsd/milestones/M003-rdpeu4/slices/S03/tasks/T01-PLAN.md` — Added required `## Observability Impact` section.
- `.gsd/milestones/M003-rdpeu4/slices/S03/S03-PLAN.md` — Marked T01 as complete (`[x]`).
