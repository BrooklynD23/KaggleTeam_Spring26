---
id: T02
parent: S01
milestone: M003-rdpeu4
provides:
  - Executable `src.modeling.track_a.audit_intake` CLI that builds a validated scored-intake bundle with canonical parquet + manifest + validation diagnostics
  - Integration/failure-path regression tests covering happy path, missing predictions diagnostics, and malformed prediction schema validation failure
key_files:
  - src/modeling/track_a/audit_intake.py
  - src/modeling/track_a/__init__.py
  - tests/test_m003_track_a_audit_intake.py
  - .gsd/milestones/M003-rdpeu4/slices/S01/S01-PLAN.md
key_decisions:
  - Reused D026/D027 contract and bundle-path decisions; no new architectural decision was required in T02
patterns_established:
  - The intake builder always emits machine-readable `manifest.json` and `validation_report.json` on both success and failure with explicit phase/status surfaces
  - Canonical scored output is normalized to the contract columns and written deterministically sorted by `review_id`
observability_surfaces:
  - outputs/modeling/track_a/audit_intake/validation_report.json
  - outputs/modeling/track_a/audit_intake/manifest.json
  - outputs/modeling/track_a/audit_intake_missing_case/{validation_report.json,manifest.json}
  - python -m src.modeling.track_a.audit_intake --config ... --predictions ... --metrics ... --output-dir ...
duration: 40m
verification_result: passed
completed_at: 2026-03-23T14:48:30-07:00
blocker_discovered: false
---

# T02: Implement Track A audit-intake builder CLI and canonical bundle outputs

**Added a production Track A audit-intake CLI plus regression coverage so upstream scored predictions are reproducibly normalized, contract-validated, and emitted as canonical intake artifacts with explicit failure diagnostics.**

## What Happened

Following TDD, I first created `tests/test_m003_track_a_audit_intake.py` and confirmed the red state (`ModuleNotFoundError: No module named 'src.modeling.track_a'`).

I then implemented `src/modeling/track_a/audit_intake.py` with a real CLI (`--config`, `--predictions`, `--metrics`, `--output-dir`) and runtime pipeline that:

- loads Track A config, predictions parquet, metrics CSV, and curated `review_fact.parquet`
- loads split context via `load_candidate_splits(...)` (artifact-first with config fallback)
- joins IDs/context by `review_id`, normalizes to contract fields, and derives split/as-of markers when needed
- validates with `validate_audit_intake_dataframe(...)`
- writes canonical outputs to the requested bundle directory:
  - `scored_intake.parquet`
  - `manifest.json`
  - `validation_report.json`

I implemented explicit phase/status diagnostics (`load_predictions`, `load_metrics`, `load_review_fact`, `join_keys`, `validate_schema`, `write_bundle`) and ensured failures still emit JSON diagnostics with upstream path echoing, missing-input lists, and timestamps.

I also added `src/modeling/track_a/__init__.py` package exports using lazy proxy functions (`run`, `main`) to avoid import-time runtime warnings when executing `python -m src.modeling.track_a.audit_intake`.

Finally, I marked T02 done in `.gsd/milestones/M003-rdpeu4/slices/S01/S01-PLAN.md`.

## Verification

I ran all T02 verification commands and confirmed they pass with generated canonical artifacts.

I also ran the slice-level verification commands. As expected on this intermediate task, the full three-file pytest gate partially fails because `tests/test_m003_intake_handoff_contract.py` belongs to T03 and is not implemented yet; all T02-relevant slice checks pass.

For Observability Impact, I directly verified:

- success-path diagnostics (`manifest.json` + `validation_report.json`) include status/phase and row/null diagnostics
- failure-path diagnostics include explicit `phase=load_predictions`, missing-input reporting, and blocked manifest status

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_a_audit_intake.py` | 0 | ✅ pass | 7.081s |
| 2 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_a.audit_intake --config configs/track_a.yaml --predictions outputs/modeling/track_a/predictions_test.parquet --metrics outputs/modeling/track_a/metrics.csv --output-dir outputs/modeling/track_a/audit_intake` | 0 | ✅ pass | 4.110s |
| 3 | `test -f outputs/modeling/track_a/audit_intake/scored_intake.parquet && test -f outputs/modeling/track_a/audit_intake/manifest.json && test -f outputs/modeling/track_a/audit_intake/validation_report.json` | 0 | ✅ pass | 0.035s |
| 4 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_audit_intake_contract.py tests/test_m003_track_a_audit_intake.py tests/test_m003_intake_handoff_contract.py` | 4 | ❌ fail | 1.856s |
| 5 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_a.audit_intake --config configs/track_a.yaml --predictions outputs/modeling/track_a/predictions_test.parquet --metrics outputs/modeling/track_a/metrics.csv --output-dir outputs/modeling/track_a/audit_intake` | 0 | ✅ pass | 3.985s |
| 6 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY' ... assert manifest['status']=='ready_for_fairness_audit'; assert validation['status']=='pass' ... PY` | 0 | ✅ pass | 3.634s |
| 7 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_a_audit_intake.py -k missing_predictions_emits_diagnostics` | 0 | ✅ pass | 5.897s |
| 8 | `failure-surface check: run CLI with missing predictions path and assert diagnostics JSON contains phase=load_predictions + missing_inputs + blocked_upstream status` | 0 | ✅ pass | 3.930s |

## Diagnostics

- Success surface: `outputs/modeling/track_a/audit_intake/validation_report.json` includes contract checks, `phase`, `status`, `row_count`, `null_violations`, per-phase timeline, and upstream paths.
- Success surface: `outputs/modeling/track_a/audit_intake/manifest.json` includes canonical readiness status (`ready_for_fairness_audit`), schema version, split context, baseline anchor metadata, and bundle file map.
- Failure surface: `outputs/modeling/track_a/audit_intake_missing_case/validation_report.json` and `manifest.json` expose `phase=load_predictions`, missing-input list, and `blocked_upstream` status.
- Test surface: `tests/test_m003_track_a_audit_intake.py` asserts happy-path output contract and failure-path diagnostics.

## Deviations

- The task plan listed `src/modeling/common/audit_intake_contract.py` as likely touched, but no contract changes were required; T02 consumed T01 contract APIs as-is.
- To run the required runtime verification command in this stripped worktree, I materialized minimal local upstream fixture artifacts under ignored paths (`data/curated/` and `outputs/modeling/track_a/`).

## Known Issues

- Slice-level full pytest command still fails on this intermediate task because `tests/test_m003_intake_handoff_contract.py` is not present until T03.

## Files Created/Modified

- `src/modeling/track_a/audit_intake.py` — Added Track A audit-intake CLI, normalization/join logic, contract validation wiring, and canonical manifest/validation outputs for pass/fail flows.
- `src/modeling/track_a/__init__.py` — Added lazy `run`/`main` exports for package-level CLI/runtime access without `-m` import warnings.
- `tests/test_m003_track_a_audit_intake.py` — Added T02 integration and failure-path regression tests.
- `.gsd/milestones/M003-rdpeu4/slices/S01/S01-PLAN.md` — Marked T02 task checkbox complete.
- `outputs/modeling/track_a/audit_intake/scored_intake.parquet` — Generated canonical scored intake rows for runtime verification.
- `outputs/modeling/track_a/audit_intake/manifest.json` — Generated readiness + baseline anchor metadata surface.
- `outputs/modeling/track_a/audit_intake/validation_report.json` — Generated schema/phase diagnostics surface.
