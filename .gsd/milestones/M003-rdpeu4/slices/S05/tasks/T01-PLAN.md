---
estimated_steps: 4
estimated_files: 3
skills_used:
  - tdd-workflow
  - verification-loop
  - test
---

# T01: Define S05 closeout contract and escalation/status validators

**Slice:** S05 — Integrated closeout gate with conditional compute-escalation decision
**Milestone:** M003-rdpeu4

## Description

Create the shared S05 closeout contract before runtime implementation so stage-matrix schema, closeout status vocabulary, and escalation-decision semantics are deterministic across runtime, tests, and handoff docs.

## Steps

1. Add `src/modeling/common/closeout_contract.py` with closeout schema/version constants, required stage IDs (`s01_intake`, `s02_fairness`, `s03_mitigation`, `s04_comparator`), required `stage_status_table` columns, closeout status vocabulary, and escalation-decision vocabulary.
2. Implement validators for stage table and manifest payloads, including strict boolean checks for `is_hard_block` / `is_soft_block` and deterministic diagnostics for missing columns, missing stages, invalid status values, or invalid escalation decisions.
3. Export new closeout contract helpers from `src/modeling/common/__init__.py` so T02 runtime and T03 handoff tests share one canonical import surface.
4. Add `tests/test_m003_closeout_contract.py` with pass/fail coverage for valid contract payloads and invalid schema/status/decision branches.

## Must-Haves

- [ ] Closeout status vocabulary and escalation decision vocabulary are centralized in one shared contract module.
- [ ] Validators enforce complete stage coverage and strict `bool` typing for hard/soft block flags.
- [ ] Contract tests fail deterministically on schema/status/decision drift.

## Verification

- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_closeout_contract.py -q`
- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_closeout_contract.py -k "missing or invalid or decision or stage" -q`

## Observability Impact

- Signals added/changed: contract validators return structured check-level diagnostics (`missing_columns`, `missing_stages`, `invalid_status`, `invalid_decision`) suitable for direct inclusion in `validation_report.json`.
- How a future agent inspects this: run `tests/test_m003_closeout_contract.py` or call shared validators from `src.modeling.common` to identify exact contract drift source.
- Failure state exposed: invalid closeout manifests/stage tables fail with machine-readable reason codes instead of ambiguous runtime exceptions.

## Inputs

- `src/modeling/common/audit_intake_contract.py` — S01 contract pattern for schema constants and deterministic diagnostics.
- `src/modeling/common/fairness_audit_contract.py` — S02 status-vocabulary and validator style reference.
- `src/modeling/common/mitigation_contract.py` — S03 blocked semantics and strict-threshold boolean validation pattern.
- `src/modeling/common/comparator_contract.py` — S04 materiality contract style and manifest validator conventions.
- `.gsd/milestones/M003-rdpeu4/slices/S05/S05-RESEARCH.md` — Required S05 status/decision semantics and trigger guidance.

## Expected Output

- `src/modeling/common/closeout_contract.py` — Canonical closeout schema constants, status/decision vocab, and validators.
- `src/modeling/common/__init__.py` — Shared export surface updates for closeout contract helpers.
- `tests/test_m003_closeout_contract.py` — Regression tests locking closeout contract invariants.
