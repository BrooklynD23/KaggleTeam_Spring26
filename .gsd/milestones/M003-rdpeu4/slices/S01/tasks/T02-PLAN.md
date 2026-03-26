---
estimated_steps: 5
estimated_files: 5
skills_used:
  - coding-standards
  - tdd-workflow
  - verification-loop
---

# T02: Implement Track A audit-intake builder CLI and canonical bundle outputs

**Slice:** S01 — Upstream audit-intake contract on reproducible scored artifacts
**Milestone:** M003-rdpeu4

## Description

Build the executable Track A intake command that transforms upstream scored predictions into a validated, downstream-ready bundle with stable schema and baseline anchor metadata.

## Steps

1. Implement `src.modeling.track_a.audit_intake` CLI arguments for config path, predictions path, metrics path, and output directory.
2. Load upstream predictions plus required join context (IDs, split/as-of markers) and normalize columns into the T01 contract shape.
3. Validate the normalized table with the contract helper and produce structured diagnostics for both pass and fail outcomes.
4. Write canonical bundle artifacts (`scored_intake.parquet`, `manifest.json`, `validation_report.json`) to the configured output directory.
5. Add integration tests for happy path and missing/malformed upstream input paths.

## Must-Haves

- [ ] CLI reruns deterministically and emits one canonical intake bundle path for downstream slices.
- [ ] Bundle includes both scored rows and machine-readable metadata (status, schema version, row counts, baseline anchor fields).
- [ ] Missing-input and malformed-schema failures produce explicit diagnostics rather than silent fallback behavior.

## Verification

- `python -m pytest tests/test_m003_track_a_audit_intake.py`
- `python -m src.modeling.track_a.audit_intake --config configs/track_a.yaml --predictions outputs/modeling/track_a/predictions_test.parquet --metrics outputs/modeling/track_a/metrics.csv --output-dir outputs/modeling/track_a/audit_intake`
- `test -f outputs/modeling/track_a/audit_intake/scored_intake.parquet && test -f outputs/modeling/track_a/audit_intake/manifest.json && test -f outputs/modeling/track_a/audit_intake/validation_report.json`

## Observability Impact

- Signals added/changed: `outputs/modeling/track_a/audit_intake/manifest.json` and `outputs/modeling/track_a/audit_intake/validation_report.json` expose status, phase, and schema diagnostics.
- How a future agent inspects this: rerun `python -m src.modeling.track_a.audit_intake ...` and inspect JSON diagnostics plus `scored_intake.parquet` column set.
- Failure state exposed: missing upstream artifact paths, schema violations, and key null/duplicate counts become explicit machine-readable failure records.

## Inputs

- `src/modeling/common/audit_intake_contract.py` — Contract validator and required schema from T01
- `configs/track_a.yaml` — Split/leakage context for Track A intake
- `outputs/modeling/track_a/predictions_test.parquet` — Upstream scored predictions from Track A baseline
- `outputs/modeling/track_a/metrics.csv` — Baseline metric/runtime anchors for downstream comparator context
- `data/curated/review_fact.parquet` — Join surface for required IDs and as-of context

## Expected Output

- `src/modeling/track_a/audit_intake.py` — Track A intake CLI implementation
- `src/modeling/track_a/__init__.py` — Package export for intake command
- `tests/test_m003_track_a_audit_intake.py` — Integration + failure-path regression tests
- `outputs/modeling/track_a/audit_intake/scored_intake.parquet` — Canonical scored intake rows for fairness audit
- `outputs/modeling/track_a/audit_intake/manifest.json` — Intake manifest with baseline anchors and readiness status
- `outputs/modeling/track_a/audit_intake/validation_report.json` — Structured validation pass/fail diagnostics
