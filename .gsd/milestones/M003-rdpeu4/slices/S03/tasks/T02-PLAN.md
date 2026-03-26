---
estimated_steps: 5
estimated_files: 6
skills_used:
  - tdd-workflow
  - verification-loop
  - test
---

# T02: Implement mitigation runtime with residual-correction lever and fail-closed diagnostics

**Slice:** S03 — One mitigation lever with pre/post fairness-accuracy deltas
**Milestone:** M003-rdpeu4

## Description

Implement `src.modeling.track_e.mitigation_experiment` to consume S01/S02 artifacts, execute one bounded mitigation lever, compute pre/post fairness+accuracy deltas, and write canonical success/blocked bundles.

## Steps

1. Create `src/modeling/track_e/mitigation_experiment.py` CLI (`--config`, `--intake-dir`, `--fairness-dir`, `--output-dir`) and wire package exports in `src/modeling/track_e/__init__.py`.
2. Gate upstream readiness by validating S01 intake bundle and S02 fairness bundle statuses/contracts; emit `blocked_upstream` artifacts when these checks fail.
3. Implement the mitigation lever: fit group-wise residual correction on non-test rows, apply subgroup shifts to test predictions, and clamp mitigated predictions to valid star range.
4. Compute baseline vs mitigated subgroup disparities plus overall accuracy metrics (`rmse`, `mae`, `within_1_star_rate`) and write `pre_post_delta.parquet` with explicit threshold/pass-fail fields.
5. Add `tests/test_m003_track_e_mitigation_experiment.py` for ready-path behavior plus blocked-upstream and blocked-insufficient-signal branches.

## Must-Haves

- [ ] Runtime writes deterministic bundle files on both success and blocked flows.
- [ ] Pre/post delta output includes both fairness disparity deltas and paired accuracy deltas in one authoritative table.
- [ ] Insufficient subgroup signal is fail-closed and explicit (`blocked_insufficient_signal`) instead of silent empty-success claims.

## Verification

- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_e_mitigation_experiment.py -q`
- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.mitigation_experiment --config configs/track_e.yaml --intake-dir outputs/modeling/track_a/audit_intake --fairness-dir outputs/modeling/track_e/fairness_audit --output-dir outputs/modeling/track_e/mitigation_experiment`
- `test -f outputs/modeling/track_e/mitigation_experiment/pre_post_delta.parquet && test -f outputs/modeling/track_e/mitigation_experiment/manifest.json && test -f outputs/modeling/track_e/mitigation_experiment/validation_report.json`

## Observability Impact

- Signals added/changed: S03 manifest/validation payloads expose mitigation status, phase progression, lever metadata, row counts, and threshold/accuracy delta checks.
- How a future agent inspects this: rerun `python -m src.modeling.track_e.mitigation_experiment ...` then inspect `outputs/modeling/track_e/mitigation_experiment/{manifest.json,validation_report.json,pre_post_delta.parquet}`.
- Failure state exposed: blocked runs identify `validate_upstream` or `evaluate_signal` failures with structured reasons and missing-input/signal diagnostics.

## Inputs

- `src/modeling/common/mitigation_contract.py` — Mitigation schema/status validators from T01.
- `src/modeling/track_e/fairness_audit.py` — S02 fairness metric/disparity computation patterns and diagnostics shape.
- `outputs/modeling/track_a/audit_intake/scored_intake.parquet` — Canonical scored predictions/truth intake.
- `outputs/modeling/track_a/audit_intake/manifest.json` — Baseline/split anchor context from S01.
- `outputs/modeling/track_e/fairness_audit/subgroup_metrics.parquet` — S02 subgroup support posture for signal gating.
- `outputs/modeling/track_e/fairness_audit/disparity_summary.parquet` — S02 baseline disparity posture for mitigation targeting.
- `outputs/modeling/track_e/fairness_audit/manifest.json` — S02 readiness gate (`ready_for_mitigation`) and continuity context.
- `configs/track_e.yaml` — Fairness thresholds, min group sizes, and subgroup settings.

## Expected Output

- `src/modeling/track_e/mitigation_experiment.py` — S03 mitigation runtime CLI and bundle writer.
- `src/modeling/track_e/__init__.py` — Track E package exports including mitigation runtime.
- `tests/test_m003_track_e_mitigation_experiment.py` — Integration tests for ready and blocked branches.
- `outputs/modeling/track_e/mitigation_experiment/pre_post_delta.parquet` — Authoritative pre/post fairness-accuracy delta artifact.
- `outputs/modeling/track_e/mitigation_experiment/manifest.json` — S03 readiness/blocked status + continuity metadata.
- `outputs/modeling/track_e/mitigation_experiment/validation_report.json` — Check-level and phase-level diagnostics.
