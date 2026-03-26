---
id: T01
parent: S05
milestone: M003-rdpeu4
provides:
  - Canonical S05 closeout contract constants and validators for stage-matrix schema, closeout status vocabulary, and compute-escalation decision vocabulary.
key_files:
  - src/modeling/common/closeout_contract.py
  - src/modeling/common/__init__.py
  - tests/test_m003_closeout_contract.py
key_decisions:
  - Enforced strict bool dtype + row-value validation for `is_hard_block`/`is_soft_block` and exposed machine-readable reason codes (`missing_columns`, `missing_stages`, `invalid_status`, `invalid_decision`).
patterns_established:
  - Contract module pattern aligned with S01–S04 (`*_contract_spec`, focused validators, deterministic `checks` payloads).
observability_surfaces:
  - `validate_stage_status_table_dataframe` and `validate_closeout_manifest_payload` return structured check-level diagnostics for direct inclusion in `validation_report.json`.
duration: 1h
verification_result: passed
completed_at: 2026-03-23
blocker_discovered: false
---

# T01: Define S05 closeout contract and escalation/status validators

**Added the S05 closeout contract module, wired shared exports, and shipped regression tests that lock schema/stage/status/decision drift with deterministic diagnostics.**

## What Happened

I followed TDD flow: first added `tests/test_m003_closeout_contract.py` to define pass/fail expectations for contract spec stability, stage-table schema coverage, strict boolean gate typing, and closeout manifest decision semantics.

After confirming red (import failure), I implemented `src/modeling/common/closeout_contract.py` with:
- canonical constants for schema version, required stage IDs, required stage table columns, status vocabulary, decision vocabulary, and required manifest fields;
- `closeout_contract_spec()` metadata surface;
- `validate_stage_status_table_dataframe()` enforcing required columns, complete stage coverage, and strict bool dtype/value validation for `is_hard_block`/`is_soft_block`;
- `validate_closeout_manifest_status()`, `validate_compute_escalation_decision()`, and `validate_closeout_manifest_payload()` with deterministic invalid/missing diagnostics.

Then I updated `src/modeling/common/__init__.py` to export all closeout contract helpers/constants from the canonical shared import surface for downstream runtime and handoff tests.

## Verification

Task-level verification passed for both required T01 test commands, and a direct observability assertion confirmed reason-code surfaces are available and stable.

Per slice instructions, I also ran all slice-level verification commands. Expected intermediate failures occurred for T02/T03-dependent checks because `tests/test_m003_milestone_closeout_gate.py`, `tests/test_m003_closeout_handoff_contract.py`, and `src.modeling.m003_closeout_gate` are not implemented yet in this task.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_closeout_contract.py -q` | 0 | ✅ pass | 2.37s |
| 2 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_closeout_contract.py -k "missing or invalid or decision or stage" -q` | 0 | ✅ pass | 2.37s |
| 3 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY' ... validate_stage_status_table_dataframe/validate_closeout_manifest_payload reason-code assertions ... PY` | 0 | ✅ pass | 3s |
| 4 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_closeout_contract.py tests/test_m003_milestone_closeout_gate.py tests/test_m003_closeout_handoff_contract.py -q` | 4 | ❌ fail | 2s |
| 5 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_audit_intake_contract.py tests/test_m003_track_a_audit_intake.py tests/test_m003_intake_handoff_contract.py tests/test_m003_fairness_audit_contract.py tests/test_m003_track_e_fairness_audit.py tests/test_m003_fairness_audit_handoff_contract.py tests/test_m003_mitigation_contract.py tests/test_m003_track_e_mitigation_experiment.py tests/test_m003_mitigation_handoff_contract.py tests/test_m003_comparator_contract.py tests/test_m003_track_a_stronger_comparator.py tests/test_m003_comparator_handoff_contract.py tests/test_m003_closeout_contract.py tests/test_m003_milestone_closeout_gate.py tests/test_m003_closeout_handoff_contract.py -q` | 4 | ❌ fail | 2s |
| 6 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.m003_closeout_gate --track-a-config configs/track_a.yaml --track-e-config configs/track_e.yaml --predictions outputs/modeling/track_a/predictions_test.parquet --metrics outputs/modeling/track_a/metrics.csv --candidate-metrics tests/fixtures/m003_candidate_metrics.csv --output-dir outputs/modeling/m003_closeout` | 1 | ❌ fail | 0s |
| 7 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY' ... closeout bundle artifact assertions ... PY` | 1 | ❌ fail | 4s |

## Diagnostics

Use these helpers for immediate contract drift triage:
- `validate_stage_status_table_dataframe(df)` → check-level details for `required_columns`, `required_stages`, `block_flag_fields` and top-level fields including `missing_columns`, `missing_stages`, `invalid_block_flag_dtypes`, `malformed_block_flags`.
- `validate_closeout_manifest_payload(payload)` → check-level details for `required_fields`, `manifest_status_vocabulary`, `compute_escalation_decision_vocabulary` and top-level `invalid_status`/`invalid_decision`.

## Deviations

None.

## Known Issues

- Slice-level verification commands that depend on T02/T03 artifacts currently fail by design at this intermediate point (missing runtime module/tests and closeout output bundle).

## Files Created/Modified

- `src/modeling/common/closeout_contract.py` — Added canonical S05 closeout contract constants plus stage-table and manifest validators.
- `src/modeling/common/__init__.py` — Exported closeout contract constants/helpers on the shared modeling contract import surface.
- `tests/test_m003_closeout_contract.py` — Added regression tests for pass/fail branches across schema, stage coverage, strict booleans, status vocab, and escalation decision vocab.
- `.gsd/milestones/M003-rdpeu4/slices/S05/S05-PLAN.md` — Marked T01 as complete (`[x]`).
