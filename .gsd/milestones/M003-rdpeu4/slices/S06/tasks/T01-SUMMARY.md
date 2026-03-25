---
id: T01
parent: S06
milestone: M003-rdpeu4
provides:
  - Fairness contract-level `signal_sufficiency` schema metadata and machine-readable validation checks for primary/fallback/insufficient outcomes.
key_files:
  - src/modeling/common/fairness_audit_contract.py
  - src/modeling/common/__init__.py
  - tests/test_m003_fairness_audit_contract.py
key_decisions:
  - Kept fairness manifest status vocabulary unchanged (`ready_for_mitigation`, `blocked_upstream`) and modeled sufficiency semantics as an additive diagnostics contract.
patterns_established:
  - Payload validators return deterministic `checks` entries plus normalized `missing_*`/`invalid_*`/`malformed_*` fields for downstream parsers.
observability_surfaces:
  - `validate_signal_sufficiency_payload(...)` return payload and sufficiency-focused assertions in `tests/test_m003_fairness_audit_contract.py`.
duration: ~1h
verification_result: passed
completed_at: 2026-03-23
blocker_discovered: false
---

# T01: Add fairness sufficiency diagnostics contract and regression coverage

**Added explicit fairness `signal_sufficiency` contract constants + validator diagnostics, and locked them with regression tests while preserving existing manifest status vocabulary.**

## What Happened

I extended `src/modeling/common/fairness_audit_contract.py` with a new sufficiency contract surface: required fields, allowed outcomes, reason vocabulary, fallback metadata requirements, and a new `validate_signal_sufficiency_payload` helper that emits machine-readable check results.

I kept manifest status values unchanged and wired the new sufficiency metadata into `fairness_audit_contract_spec()` so runtime/handoff code can discover the contract deterministically.

I exported all new constants and validator helpers through `src/modeling/common/__init__.py`, then expanded `tests/test_m003_fairness_audit_contract.py` with pass/fail coverage for valid sufficiency payloads, malformed outcomes, missing reasons for `insufficient`, and invalid fallback metadata.

During implementation, one bug surfaced (`_to_jsonable` handling of list values); I fixed it by making list/dict serialization explicit before `pd.isna(...)` checks.

## Verification

Task-level verification commands passed:
- `pytest tests/test_m003_fairness_audit_contract.py -q`
- `pytest tests/test_m003_fairness_audit_contract.py -k "sufficiency or manifest_status" -q`

Slice-level checks were also run for visibility at this intermediate task stage:
- Full three-test-suite pytest passed.
- Fairness and mitigation runtimes executed successfully.
- The two S06 sufficiency smoke assertions failed as expected because T02 runtime wiring is not implemented yet (`signal_sufficiency` not emitted in fairness artifacts; mitigation still reports `no_disparity_rows`).

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_fairness_audit_contract.py -q` | 0 | ✅ pass | 5.62s |
| 2 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_fairness_audit_contract.py -k "sufficiency or manifest_status" -q` | 0 | ✅ pass | 5.94s |
| 3 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_fairness_audit_contract.py tests/test_m003_track_e_fairness_audit.py tests/test_m003_fairness_audit_handoff_contract.py -q` | 0 | ✅ pass | 7.93s |
| 4 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.fairness_audit --config configs/track_e.yaml --intake-dir outputs/modeling/track_a/audit_intake --output-dir outputs/modeling/track_e/fairness_audit` | 0 | ✅ pass | 5.78s |
| 5 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY' ... fairness sufficiency contract assertions ... PY` | 1 | ❌ fail | 0.06s |
| 6 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.mitigation_experiment --config configs/track_e.yaml --intake-dir outputs/modeling/track_a/audit_intake --fairness-dir outputs/modeling/track_e/fairness_audit --output-dir outputs/modeling/track_e/mitigation_experiment` | 0 | ✅ pass | 5.88s |
| 7 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY' ... mitigation readiness smoke assertions ... PY` | 1 | ❌ fail | 0.06s |

## Diagnostics

Use `validate_signal_sufficiency_payload(...)` and inspect:
- top-level `status`
- `checks` entries (`required_fields`, `outcome_vocabulary`, `reasons_vocabulary`, `insufficient_reason_requirement`, `fallback_metadata`)
- `missing_fields`, `invalid_outcome`, `invalid_reasons`, `missing_fallback_fields`, `malformed_fallback_fields`

These are now the canonical machine-readable failure surfaces for malformed sufficiency payloads.

## Deviations

None.

## Known Issues

- Canonical fairness runtime output still does not include `signal_sufficiency`; this is expected to be addressed in T02.
- Slice-level smoke assertions that depend on sufficiency runtime behavior are currently failing until T02 wiring is complete.

## Files Created/Modified

- `src/modeling/common/fairness_audit_contract.py` — added sufficiency schema constants, spec metadata fields, and `validate_signal_sufficiency_payload` with structured check output.
- `src/modeling/common/__init__.py` — exported new sufficiency constants and validator helper.
- `tests/test_m003_fairness_audit_contract.py` — added sufficiency contract regression tests for pass/fail branches.
- `.gsd/milestones/M003-rdpeu4/slices/S06/S06-PLAN.md` — marked T01 complete (`[x]`).
