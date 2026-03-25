---
estimated_steps: 5
estimated_files: 8
skills_used:
  - tdd-workflow
  - verification-loop
  - test
---

# T02: Implement stronger comparator runtime with fairness-aware materiality gate

**Slice:** S04 — Stronger/combined comparator with materiality gate
**Milestone:** M003-rdpeu4

## Description

Implement `src.modeling.track_a.stronger_comparator` to consume S01/S02 bundles plus candidate metrics, compute materiality/runtime/fairness gate outcomes, and publish canonical ready/blocked comparator artifacts.

## Steps

1. Create `src/modeling/track_a/stronger_comparator.py` CLI (`--config`, `--intake-dir`, `--fairness-dir`, `--candidate-metrics`, `--output-dir`) and wire Track A exports in `src/modeling/track_a/__init__.py`.
2. Add config-driven comparator thresholds in `configs/track_a.yaml` (metric target, minimum gain, runtime multiplier cap) with runtime defaults for backward compatibility.
3. Gate upstream readiness by validating S01 intake status/schema, S02 fairness status/schema, and candidate metrics schema; emit deterministic `blocked_upstream` artifacts when gates fail.
4. Compute `materiality_table.parquet` fields (baseline vs candidate metric/runtime, gain/delta, fairness booleans, `adopt_recommendation`, `decision_reason`) and ensure no-fairness-signal produces ready/do-not-adopt output rather than blocked status.
5. Add `tests/test_m003_track_a_stronger_comparator.py` ready/blocked branch coverage and create `tests/fixtures/m003_candidate_metrics.csv` for canonical replay input.

## Must-Haves

- [ ] Runtime always writes deterministic bundle files (`materiality_table.parquet`, `manifest.json`, `validation_report.json`) on both ready and blocked branches.
- [ ] Adoption decision is explicitly gated by metric materiality, runtime budget, fairness readiness, and fairness signal availability.
- [ ] No-fairness-signal branch remains `ready_for_closeout` with `adopt_recommendation=false` and machine-readable decision reason.

## Verification

- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_a_stronger_comparator.py -q`
- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_a.stronger_comparator --config configs/track_a.yaml --intake-dir outputs/modeling/track_a/audit_intake --fairness-dir outputs/modeling/track_e/fairness_audit --candidate-metrics tests/fixtures/m003_candidate_metrics.csv --output-dir outputs/modeling/track_a/stronger_comparator`
- `test -f outputs/modeling/track_a/stronger_comparator/materiality_table.parquet && test -f outputs/modeling/track_a/stronger_comparator/manifest.json && test -f outputs/modeling/track_a/stronger_comparator/validation_report.json`

## Observability Impact

- Signals added/changed: S04 manifest/validation payloads expose phase progression, failed checks, threshold values, fairness-context flags, and adoption decision rationale.
- How a future agent inspects this: rerun `python -m src.modeling.track_a.stronger_comparator ...` then inspect `outputs/modeling/track_a/stronger_comparator/{materiality_table.parquet,manifest.json,validation_report.json}`.
- Failure state exposed: blocked runs localize missing inputs/schema mismatches to `load_upstream` or `validate_upstream`; ready runs preserve fairness-signal gating state in decision fields.

## Inputs

- `src/modeling/common/comparator_contract.py` — Comparator schema/status validators from T01.
- `src/modeling/track_a/audit_intake.py` — S01 bundle loading + phase diagnostics conventions to mirror.
- `src/modeling/track_e/fairness_audit.py` — S02 fairness status and threshold-check payload shape for adoption gating context.
- `outputs/modeling/track_a/audit_intake/manifest.json` — Baseline anchor and split continuity source.
- `outputs/modeling/track_a/audit_intake/validation_report.json` — Intake validation pass/fail gate source.
- `outputs/modeling/track_e/fairness_audit/manifest.json` — Fairness readiness + row-count/threshold context.
- `outputs/modeling/track_e/fairness_audit/disparity_summary.parquet` — Fairness signal availability and threshold exceedance context.
- `configs/track_a.yaml` — Comparator threshold configuration source.

## Expected Output

- `src/modeling/track_a/stronger_comparator.py` — S04 comparator runtime CLI and bundle writer.
- `src/modeling/track_a/__init__.py` — Track A export surface including comparator runtime proxies.
- `configs/track_a.yaml` — Comparator threshold settings for materiality/runtime gates.
- `tests/test_m003_track_a_stronger_comparator.py` — Integration tests for ready/do-not-adopt and blocked branches.
- `tests/fixtures/m003_candidate_metrics.csv` — Canonical candidate metrics input fixture for runtime replay.
- `outputs/modeling/track_a/stronger_comparator/materiality_table.parquet` — Authoritative S04 materiality decision table.
- `outputs/modeling/track_a/stronger_comparator/manifest.json` — S04 readiness/blocked status + continuity metadata.
- `outputs/modeling/track_a/stronger_comparator/validation_report.json` — Check-level and phase-level diagnostics.
