---
estimated_steps: 4
estimated_files: 3
skills_used:
  - tdd-workflow
  - verification-loop
---

# T01: Codify the upstream scored-intake schema contract and validator tests

**Slice:** S01 — Upstream audit-intake contract on reproducible scored artifacts
**Milestone:** M003-rdpeu4

## Description

Define the canonical schema contract for M003 upstream scored intake and lock it with deterministic tests before building runtime ingestion. This creates the non-negotiable boundary S02/S03/S04 will rely on.

## Steps

1. Create a reusable intake-contract module that defines required columns, schema version, key uniqueness/nullability rules, and forbidden column families.
2. Implement a validator API that returns structured pass/fail diagnostics (not just exceptions) for missing fields, duplicate IDs, and forbidden fields.
3. Add pytest coverage for success and failure modes using synthetic DataFrames.
4. Expose the contract helper in package init files so T02 can import it directly.

## Must-Haves

- [ ] Required intake fields include IDs, split/as-of markers, truth/prediction values, model name, and subgroup join keys.
- [ ] Validator output is machine-readable and includes failure details needed for downstream diagnostics.
- [ ] Tests cover both passing and failing contract cases without relying on external runtime artifacts.

## Verification

- `python -m pytest tests/test_m003_audit_intake_contract.py`
- `python -m pytest tests/test_m003_audit_intake_contract.py -k "missing_or_duplicate"`

## Inputs

- `configs/track_a.yaml` — Track A leakage/split context used to align contract fields
- `.gsd/milestones/M003-rdpeu4/M003-rdpeu4-ROADMAP.md` — Slice boundary expectations for required intake fields
- `src/eda/track_e/fairness_baseline.py` — Existing fairness metric expectations that intake must satisfy

## Expected Output

- `src/modeling/common/audit_intake_contract.py` — Canonical schema + validator for upstream scored intake
- `src/modeling/common/__init__.py` — Export surface for intake contract helpers
- `tests/test_m003_audit_intake_contract.py` — Contract regression suite for schema and failure diagnostics

## Observability Impact

- **Signals changed:** validator returns machine-readable diagnostics (`status`, `checks`, `missing_columns`, `duplicate_key_rows`, `forbidden_columns`) that downstream runtime and tests can persist or surface directly.
- **How to inspect:** run `python -m pytest tests/test_m003_audit_intake_contract.py` and inspect assertion messages/returned payloads for explicit check-level pass/fail state rather than exception-only behavior.
- **Failure visibility:** missing required fields, duplicate key combinations, nullability violations, and forbidden-column-family detections become individually visible with named check identifiers and offending column details.
