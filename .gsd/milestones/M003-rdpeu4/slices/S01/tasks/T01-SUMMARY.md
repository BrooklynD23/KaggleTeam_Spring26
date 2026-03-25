---
id: T01
parent: S01
milestone: M003-rdpeu4
provides:
  - Canonical M003 scored-intake schema contract with machine-readable validator diagnostics
  - Deterministic pytest regression coverage for pass/fail schema-contract behavior
key_files:
  - src/modeling/common/audit_intake_contract.py
  - src/modeling/common/__init__.py
  - tests/test_m003_audit_intake_contract.py
  - .gsd/milestones/M003-rdpeu4/slices/S01/tasks/T01-PLAN.md
  - .gsd/milestones/M003-rdpeu4/slices/S01/S01-PLAN.md
key_decisions:
  - D027 — Use review_id as primary key, business_id as subgroup join key, and centralized forbidden text/demographic column-family checks in the shared intake validator
patterns_established:
  - Contract helpers expose both static schema metadata (`intake_contract_spec`) and runtime validation diagnostics (`validate_audit_intake_dataframe`) with check-level statuses
observability_surfaces:
  - `validate_audit_intake_dataframe(...)` return payload (`status`, `checks`, `missing_columns`, `null_violations`, `duplicate_key_rows`, `forbidden_columns`, timestamp)
  - `tests/test_m003_audit_intake_contract.py` for failure-shape assertions on missing fields, duplicate IDs, nulls, and forbidden families
duration: 1h10m
verification_result: passed
completed_at: 2026-03-23T14:06:00-07:00
blocker_discovered: false
---

# T01: Codify the upstream scored-intake schema contract and validator tests

**Added the M003 scored-intake contract module and regression tests so downstream slices can consume a deterministic, machine-validated intake schema with structured failure diagnostics.**

## What Happened

I first applied the pre-flight plan fix by adding a missing `## Observability Impact` section to `T01-PLAN.md`.

Using TDD flow, I created `tests/test_m003_audit_intake_contract.py` before implementation, confirmed the initial red state (`ModuleNotFoundError: No module named 'src.modeling'`), then implemented `src/modeling/common/audit_intake_contract.py` and exports in `src/modeling/common/__init__.py`.

The contract now defines schema version, required columns, subgroup join keys, primary-key uniqueness/nullability checks, forbidden column-family detection, and a machine-readable validation payload with per-check status details. I also created `src/modeling/__init__.py` because `src/modeling/` did not yet exist in this worktree.

I recorded the contract-shape decision in `.gsd/DECISIONS.md` (D027) and added a worktree execution gotcha to `.gsd/KNOWLEDGE.md` (use `.venv-local/bin/python` because default `python3` lacks `pytest` here).

## Verification

I ran the task-level verification commands from T01 and confirmed they pass under the repo venv interpreter.

Per slice instructions, I also ran all S01 slice-level verification commands. As expected for an intermediate task, non-T01 checks fail because T02/T03 artifacts and modules are not implemented yet.

I additionally verified the new observability payload directly with a synthetic failing DataFrame and asserted presence/content of `checks`, `null_violations`, and `forbidden_columns` fields.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_audit_intake_contract.py` | 0 | ✅ pass | 6.388s |
| 2 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_audit_intake_contract.py -k "missing_or_duplicate"` | 0 | ✅ pass | 5.169s |
| 3 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_audit_intake_contract.py tests/test_m003_track_a_audit_intake.py tests/test_m003_intake_handoff_contract.py` | 4 | ❌ fail | 1.809s |
| 4 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_a.audit_intake --config configs/track_a.yaml --predictions outputs/modeling/track_a/predictions_test.parquet --metrics outputs/modeling/track_a/metrics.csv --output-dir outputs/modeling/track_a/audit_intake` | 1 | ❌ fail | 0.049s |
| 5 | `python snippet: verify outputs/modeling/track_a/audit_intake/{scored_intake.parquet,manifest.json,validation_report.json}` | 1 | ❌ fail | 4.417s |
| 6 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_a_audit_intake.py -k missing_predictions_emits_diagnostics` | 4 | ❌ fail | 1.831s |
| 7 | `python snippet: synthetic failing DataFrame asserts machine-readable validator diagnostics` | 0 | ✅ pass | 3.502s |

## Diagnostics

- Contract metadata surface: `src/modeling/common/audit_intake_contract.py::intake_contract_spec()`
- Runtime diagnostics surface: `src/modeling/common/audit_intake_contract.py::validate_audit_intake_dataframe()`
- Failure visibility includes explicit check names (`required_columns`, `subgroup_join_keys`, `required_non_null_values`, `unique_primary_key`, `forbidden_column_families`) and field-level details.
- Contract regression surface: `tests/test_m003_audit_intake_contract.py`

## Deviations

- Added `src/modeling/__init__.py` (not explicitly listed in expected outputs) because `src/modeling/` did not exist and package initialization needed an explicit root for new modeling modules.
- Applied required pre-flight fix to `T01-PLAN.md` by adding `## Observability Impact` before implementation.

## Known Issues

- Slice-level verification commands that depend on T02/T03 remain failing by design at this stage:
  - `tests/test_m003_track_a_audit_intake.py` and `tests/test_m003_intake_handoff_contract.py` do not exist yet.
  - `src.modeling.track_a.audit_intake` CLI is not implemented yet.
  - `outputs/modeling/track_a/audit_intake/*` bundle artifacts are not generated until T02.

## Files Created/Modified

- `.gsd/milestones/M003-rdpeu4/slices/S01/tasks/T01-PLAN.md` — Added missing `## Observability Impact` section (pre-flight requirement).
- `src/modeling/common/audit_intake_contract.py` — Added canonical schema contract constants, forbidden-family detection, metadata helper, and structured validator.
- `src/modeling/common/__init__.py` — Exported contract constants and helper APIs for downstream imports.
- `src/modeling/__init__.py` — Created new modeling package root for module discoverability.
- `tests/test_m003_audit_intake_contract.py` — Added deterministic T01 contract regression suite using synthetic DataFrames.
- `.gsd/DECISIONS.md` — Appended D027 via decision tool for intake key/join/forbidden-field policy.
- `.gsd/KNOWLEDGE.md` — Added venv interpreter gotcha for this worktree.
- `.gsd/milestones/M003-rdpeu4/slices/S01/S01-PLAN.md` — Marked T01 checkbox as complete.
