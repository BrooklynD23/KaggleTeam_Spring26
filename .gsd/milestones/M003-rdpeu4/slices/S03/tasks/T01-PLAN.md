---
estimated_steps: 4
estimated_files: 3
skills_used:
  - tdd-workflow
  - verification-loop
  - test
---

# T01: Define mitigation bundle contract with threshold-delta schema and blocked vocab

**Slice:** S03 — One mitigation lever with pre/post fairness-accuracy deltas
**Milestone:** M003-rdpeu4

## Description

Create the canonical S03 mitigation output contract before runtime implementation so pre/post tradeoff evidence is schema-stable, status-safe, and diagnosable in both success and blocked flows.

## Steps

1. Add `src/modeling/common/mitigation_contract.py` with schema constants for `pre_post_delta.parquet`, contract metadata, and status vocabulary (`ready_for_closeout`, `blocked_upstream`, `blocked_insufficient_signal`).
2. Implement dataframe validators that enforce required delta/threshold columns and strict boolean threshold flag fields.
3. Export mitigation contract helpers in `src/modeling/common/__init__.py` for single-surface imports by runtime/tests.
4. Add `tests/test_m003_mitigation_contract.py` pass/fail coverage for required columns, status validation, and malformed threshold booleans.

## Must-Haves

- [ ] Mitigation contract constants and validators live in one shared module, not duplicated in runtime/tests.
- [ ] Status vocabulary explicitly distinguishes upstream failures from insufficient subgroup-signal failures.
- [ ] Contract tests fail deterministically on schema/status drift and threshold-flag type violations.

## Verification

- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_mitigation_contract.py -q`
- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_mitigation_contract.py -k "missing_columns or invalid_status or threshold" -q`

## Inputs

- `src/modeling/common/fairness_audit_contract.py` — S02 contract style and validator payload shape to mirror.
- `src/modeling/common/audit_intake_contract.py` — Existing S01 contract idioms for required columns and fail diagnostics.
- `.gsd/milestones/M003-rdpeu4/slices/S03/S03-RESEARCH.md` — S03-required status semantics and insufficient-signal risk constraints.

## Expected Output

- `src/modeling/common/mitigation_contract.py` — Canonical S03 mitigation contract constants and validators.
- `src/modeling/common/__init__.py` — Export surface updates for mitigation contract helpers.
- `tests/test_m003_mitigation_contract.py` — Regression tests locking mitigation schema/status invariants.

## Observability Impact

- New diagnostics surface: mitigation-contract validators return structured payloads (`status`, `checks`, `missing_columns`, `malformed_threshold_flags`, `invalid_status`) so schema/status drift is machine-inspectable by runtime and tests.
- Inspection path for future agents: import and call `src.modeling.common.mitigation_contract` helpers directly (or via `src.modeling.common`) to validate `pre_post_delta.parquet` and manifest status semantics without duplicating logic.
- Failure states now explicit: blocked vocabulary mismatch (`ready_for_closeout` vs blocked statuses), missing required delta columns, and non-boolean threshold flags become deterministic fail results with row-level reasons instead of silent downstream breakage.
