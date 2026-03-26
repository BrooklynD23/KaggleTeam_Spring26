---
estimated_steps: 5
estimated_files: 8
skills_used:
  - tdd-workflow
  - verification-loop
  - coding-standards
  - test
---

# T02: Implement Track E model-aware fairness runtime from S01 intake with diagnostics bundle outputs

**Slice:** S02 — Model-aware fairness audit runtime on upstream predictions
**Milestone:** M003-rdpeu4

## Description

Build the executable fairness-audit runtime that consumes S01 intake artifacts, computes model-aware subgroup fairness + accuracy context, and emits canonical success/failure diagnostics for downstream mitigation/comparator slices.

## Steps

1. Create `src/modeling/track_e/fairness_audit.py` CLI arguments (`--config`, `--intake-dir`, `--output-dir`) and `src/modeling/track_e/__init__.py` package wiring.
2. Implement upstream gating that requires S01 readiness: intake manifest status `ready_for_fairness_audit`, intake validation status `pass`, and schema validity via `validate_audit_intake_dataframe`.
3. Build subgroup join context by reusing Track E subgroup utilities and compute subgroup aggregate metrics (`support_count`, `mean_y_true`, `mean_y_pred`, `mean_signed_error`, `mae`, `rmse`, `within_1_star_rate`) with minimum-group filtering.
4. Compute disparity summary rows against deterministic reference groups, include signed deltas and `exceeds_threshold` flags, and carry baseline/split context into manifest metadata.
5. Write canonical bundle artifacts (`subgroup_metrics.parquet`, `disparity_summary.parquet`, `manifest.json`, `validation_report.json`) for both success (`ready_for_mitigation`) and blocked-upstream failures.

## Must-Haves

- [ ] Runtime fails closed on missing/non-ready intake and emits `blocked_upstream` diagnostics with phase-local reason and missing-input details.
- [ ] Success bundle is aggregate-only, includes fairness + accuracy context columns, and preserves no-text/no-demographic guardrails.
- [ ] Manifest and validation JSON include enough context (phase timeline, row counts, baseline anchor echoes, upstream paths) for S03/S04/S05 triage.

## Verification

- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_e_fairness_audit.py -q`
- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.fairness_audit --config configs/track_e.yaml --intake-dir outputs/modeling/track_a/audit_intake --output-dir outputs/modeling/track_e/fairness_audit`
- `test -f outputs/modeling/track_e/fairness_audit/subgroup_metrics.parquet && test -f outputs/modeling/track_e/fairness_audit/disparity_summary.parquet && test -f outputs/modeling/track_e/fairness_audit/manifest.json && test -f outputs/modeling/track_e/fairness_audit/validation_report.json`

## Observability Impact

- Signals added/changed: `manifest.json` + `validation_report.json` gain explicit phase timeline, status, blocking reason, row counts, and threshold-check surfaces for fairness runtime.
- How a future agent inspects this: rerun `python -m src.modeling.track_e.fairness_audit ...`, then inspect `outputs/modeling/track_e/fairness_audit/manifest.json` and `validation_report.json`.
- Failure state exposed: non-ready intake contract, schema drift, subgroup join failures, and write failures are localized by named phase and reason.

## Inputs

- `src/modeling/common/fairness_audit_contract.py` — S02 output contract and validators from T01.
- `src/modeling/common/audit_intake_contract.py` — S01 intake validation helper for upstream gating.
- `src/eda/track_e/subgroup_definition.py` — Reusable subgroup derivation logic for business-level mapping.
- `src/eda/track_e/common.py` — Aggregate-safe write helpers and min-group enforcement utilities.
- `configs/track_e.yaml` — Fairness thresholds and subgroup settings.
- `outputs/modeling/track_a/audit_intake/scored_intake.parquet` — Canonical S01 predictions/truth intake.
- `outputs/modeling/track_a/audit_intake/manifest.json` — Upstream readiness and baseline-anchor context.
- `outputs/modeling/track_a/audit_intake/validation_report.json` — Upstream validation status gate.

## Expected Output

- `src/modeling/track_e/fairness_audit.py` — S02 fairness audit CLI/runtime implementation.
- `src/modeling/track_e/__init__.py` — Package export surface for Track E modeling runtime.
- `tests/test_m003_track_e_fairness_audit.py` — Runtime integration and blocked-upstream regression tests.
- `outputs/modeling/track_e/fairness_audit/subgroup_metrics.parquet` — Aggregate subgroup fairness + accuracy context metrics.
- `outputs/modeling/track_e/fairness_audit/disparity_summary.parquet` — Reference/comparison disparities with threshold flags.
- `outputs/modeling/track_e/fairness_audit/manifest.json` — Status/readiness metadata for S03/S04/S05 consumption.
- `outputs/modeling/track_e/fairness_audit/validation_report.json` — Structured check-level diagnostics and phase timeline.
