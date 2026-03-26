---
estimated_steps: 4
estimated_files: 4
skills_used:
  - test
  - verification-loop
---

# T03: Add shared modeling-contract verification

**Slice:** S01 — Repo-state reconciliation and shared modeling contract
**Milestone:** M002-c1uww6

## Description

Add a focused regression test that keeps the M002 shared contract honest. This task prevents future milestone drift by mechanically checking the modeling scaffold, scope lock, and audit-target language before Track A–D implementation starts.

## Steps

1. Add a test file for the M002 modeling contract.
2. Assert the shared modeling directories exist.
3. Assert the milestone docs preserve D1-required / D2-optional scope and Track A as the preferred audit target.
4. Run the test and fix any contract mismatches.

## Must-Haves

- [ ] The repo has a dedicated regression test for the shared M002 modeling contract.
- [ ] The test fails if modeling directories disappear or milestone scope language drifts.

## Verification

- `python -m pytest tests/test_m002_modeling_contract.py`
- `python - <<'PY'
from pathlib import Path
assert Path('tests/test_m002_modeling_contract.py').exists()
print('M002 modeling contract test exists')
PY`

## Inputs

- `.gsd/milestones/M002-c1uww6/M002-c1uww6-CONTEXT.md` — milestone scope source of truth for the regression test
- `.gsd/milestones/M002-c1uww6/M002-c1uww6-ROADMAP.md` — milestone slice/source contract for the regression test
- `src/modeling/README.md` — artifact contract source of truth for the regression test
- `src/modeling/` — directory scaffold the regression test must enforce

## Expected Output

- `tests/test_m002_modeling_contract.py` — regression test covering shared modeling directories and milestone contract markers

## Observability Impact

- **Signals added/strengthened:** `python -m pytest tests/test_m002_modeling_contract.py` now serves as the inspectable status surface for shared modeling scaffold drift, milestone scope-lock language drift, and README artifact-contract drift.
- **How future agents inspect it:** Read `tests/test_m002_modeling_contract.py` for the enforced contract markers, then run the pytest target to get exact missing-path or missing-marker failures.
- **Failure state now visible:** missing `src/modeling/*` / `outputs/modeling/*` directories, missing D1-required / D2-optional / Track A preferred milestone markers, or missing shared artifact-contract language in `src/modeling/README.md` fail with concrete assertion messages instead of silent milestone drift.
