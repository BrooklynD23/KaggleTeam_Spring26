---
estimated_steps: 4
estimated_files: 3
skills_used:
  - tdd-workflow
  - verification-loop
  - test
---

# T01: Define comparator contract and materiality schema validators

**Slice:** S04 — Stronger/combined comparator with materiality gate
**Milestone:** M003-rdpeu4

## Description

Create the canonical S04 comparator output contract before runtime implementation so materiality/adoption outputs are schema-stable, status-safe, and diagnosable for both ready and blocked flows.

## Steps

1. Add `src/modeling/common/comparator_contract.py` with comparator schema/version constants, required `materiality_table` columns, and manifest status vocabulary (`ready_for_closeout`, `blocked_upstream`).
2. Implement dataframe validators that enforce required columns and strict boolean typing for gate fields (`material_improvement`, `runtime_within_budget`, `fairness_context_ready`, `fairness_signal_available`, `adopt_recommendation`).
3. Export comparator contract helpers from `src/modeling/common/__init__.py` for a single shared import surface used by runtime/tests.
4. Add `tests/test_m003_comparator_contract.py` pass/fail coverage for missing columns, invalid status values, and malformed gate booleans.

## Must-Haves

- [ ] Comparator contract constants and validators live in one shared module, not duplicated in runtime/tests.
- [ ] Manifest status validation explicitly locks `ready_for_closeout` and `blocked_upstream` vocabulary.
- [ ] Contract tests fail deterministically on schema/status/boolean drift.

## Verification

- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_comparator_contract.py -q`
- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_comparator_contract.py -k "missing_columns or invalid_status or boolean" -q`

## Inputs

- `src/modeling/common/audit_intake_contract.py` — S01 contract idioms for required-column and diagnostics payload structure.
- `src/modeling/common/fairness_audit_contract.py` — S02 contract pattern for status vocabulary + boolean field checks.
- `src/modeling/common/mitigation_contract.py` — S03 contract pattern for readiness-vs-blocked semantics and shared validator style.
- `.gsd/milestones/M003-rdpeu4/slices/S04/S04-RESEARCH.md` — S04-required materiality/fairness gating constraints.

## Expected Output

- `src/modeling/common/comparator_contract.py` — Canonical S04 comparator contract constants and validators.
- `src/modeling/common/__init__.py` — Export surface updates for comparator contract helpers.
- `tests/test_m003_comparator_contract.py` — Regression tests locking comparator schema/status invariants.

## Observability Impact

- New comparator-contract validators emit structured diagnostics payloads (`checks`, `missing_columns`, `malformed_gate_flags`, `invalid_status`) that runtime and tests can persist directly in `validation_report.json`.
- Future agents can inspect contract drift by calling the shared validators from `src.modeling.common` and reading deterministic fail reasons instead of inferring from downstream runtime crashes.
- Failure visibility improves for three concrete states: required materiality schema missing, manifest status outside allowed vocabulary, and non-boolean gate columns in `materiality_table`.
