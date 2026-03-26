---
estimated_steps: 4
estimated_files: 3
skills_used:
  - tdd-workflow
  - verification-loop
  - test
---

# T01: Add fairness sufficiency diagnostics contract and regression coverage

**Slice:** S06 — Fairness-signal sufficiency replay on real upstream predictions
**Milestone:** M003-rdpeu4

## Description

Define the shared fairness-audit sufficiency diagnostics contract before runtime rewiring so S02 status semantics stay stable while downstream parsers can deterministically interpret primary/fallback/insufficient outcomes.

## Steps

1. Extend `src/modeling/common/fairness_audit_contract.py` with `signal_sufficiency` schema constants (required fields, allowed outcomes, reason vocabulary) and validator helpers that return machine-readable checks.
2. Keep existing fairness manifest status vocabulary unchanged (`ready_for_mitigation`, `blocked_upstream`) and wire new contract helpers into `fairness_audit_contract_spec()` output.
3. Export any new constants/helpers from `src/modeling/common/__init__.py` for use by runtime and tests.
4. Expand `tests/test_m003_fairness_audit_contract.py` to lock pass/fail coverage for valid sufficiency payloads, malformed outcomes, missing reasons, and invalid fallback metadata.

## Must-Haves

- [ ] Contract spec includes deterministic `signal_sufficiency` metadata expected by runtime/handoff consumers.
- [ ] Validator checks produce explicit, machine-readable failure details for malformed sufficiency payloads.
- [ ] Existing fairness status vocabulary remains unchanged to preserve S03/S04 compatibility.

## Verification

- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_fairness_audit_contract.py -q`
- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_fairness_audit_contract.py -k "sufficiency or manifest_status" -q`

## Observability Impact

- Signals added/changed: contract-level sufficiency diagnostics vocabulary and structured check payloads.
- How a future agent inspects this: run `tests/test_m003_fairness_audit_contract.py` and inspect validator return payloads in failing assertions.
- Failure state exposed: malformed sufficiency payloads fail with explicit reason fields rather than generic status mismatch.

## Inputs

- `src/modeling/common/fairness_audit_contract.py` — Existing fairness contract constants/spec/validators to extend.
- `src/modeling/common/__init__.py` — Shared export surface consumed by fairness runtime/tests.
- `tests/test_m003_fairness_audit_contract.py` — Current regression harness for fairness contract behavior.
- `.gsd/milestones/M003-rdpeu4/slices/S06/S06-RESEARCH.md` — Required sufficiency/fallback semantics and compatibility constraints.

## Expected Output

- `src/modeling/common/fairness_audit_contract.py` — New sufficiency diagnostics constants/spec fields/validators.
- `src/modeling/common/__init__.py` — Export updates for sufficiency contract helpers.
- `tests/test_m003_fairness_audit_contract.py` — Regression tests locking sufficiency payload semantics.
