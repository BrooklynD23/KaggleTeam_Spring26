# S03: One mitigation lever with pre/post fairness-accuracy deltas

**Goal:** Execute one bounded mitigation lever on real upstream predictions and publish an authoritative pre/post fairness-vs-accuracy delta bundle that is machine-readable, fail-closed, and consumable by S05 without reconstruction.
**Demo:** Running one command (`python -m src.modeling.track_e.mitigation_experiment ...`) writes `outputs/modeling/track_e/mitigation_experiment/` with `pre_post_delta.parquet`, `manifest.json`, and `validation_report.json`, where success emits explicit pre/post fairness+accuracy deltas with threshold outcomes and failure emits deterministic blocked diagnostics.

## Must-Haves

- Close the remaining **R009** mitigation gap by implementing one executable lever (group-wise residual correction fit on non-test splits, then evaluated on test) and writing signed pre/post fairness + accuracy deltas in one canonical table.
- Prevent mitigation-theater by enforcing explicit insufficient-signal gating: when S02 has no usable subgroup/disparity comparisons, emit machine-readable blocked status/reason instead of silently reporting vacuous deltas.
- Preserve **R012** continuity and **R010** support by carrying exact `split_context` and `baseline_anchor` continuity from S02 into S03 outputs and locking required threshold/pass-fail fields in handoff regression tests and docs.

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_mitigation_contract.py tests/test_m003_track_e_mitigation_experiment.py tests/test_m003_mitigation_handoff_contract.py -q`
- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.mitigation_experiment --config configs/track_e.yaml --intake-dir outputs/modeling/track_a/audit_intake --fairness-dir outputs/modeling/track_e/fairness_audit --output-dir outputs/modeling/track_e/mitigation_experiment`
- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY'
import json
from pathlib import Path
import pandas as pd

root = Path('outputs/modeling/track_e/mitigation_experiment')
required_files = {'pre_post_delta.parquet', 'manifest.json', 'validation_report.json'}
missing = [name for name in required_files if not (root / name).is_file()]
assert not missing, missing

manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
validation = json.loads((root / 'validation_report.json').read_text(encoding='utf-8'))
delta = pd.read_parquet(root / 'pre_post_delta.parquet')

allowed_status = {'ready_for_closeout', 'blocked_upstream', 'blocked_insufficient_signal'}
assert manifest['status'] in allowed_status, manifest['status']

if manifest['status'] == 'ready_for_closeout':
    assert validation['status'] == 'pass', validation['status']
    required_cols = {
        'subgroup_type', 'metric_name', 'reference_group', 'comparison_group',
        'baseline_value', 'mitigated_value', 'delta_value',
        'baseline_exceeds_threshold', 'mitigated_exceeds_threshold',
        'baseline_rmse', 'mitigated_rmse', 'delta_rmse',
        'baseline_mae', 'mitigated_mae', 'delta_mae',
        'baseline_within_1_star_rate', 'mitigated_within_1_star_rate', 'delta_within_1_star_rate'
    }
    assert required_cols.issubset(delta.columns), required_cols - set(delta.columns)
else:
    assert validation['status'] == 'fail', validation['status']
    assert validation['phase'] in {'validate_upstream', 'evaluate_signal', 'write_bundle'}, validation['phase']

forbidden = {'review_id', 'business_id', 'user_id', 'review_text', 'raw_text', 'text', 'gender', 'race', 'income', 'ethnicity', 'nationality'}
assert forbidden.isdisjoint(delta.columns), forbidden.intersection(delta.columns)
print('m003 s03 mitigation bundle verified')
PY`
- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_e_mitigation_experiment.py -k "blocked_upstream or insufficient_signal" -q`

## Observability / Diagnostics

- Runtime signals: `manifest.json` and `validation_report.json` expose status, phase timeline, gating checks, mitigation lever metadata, threshold outcomes, and pre/post accuracy deltas.
- Inspection surfaces: `python -m src.modeling.track_e.mitigation_experiment ...`, `outputs/modeling/track_e/mitigation_experiment/{manifest.json,validation_report.json,pre_post_delta.parquet}`, and mitigation regression tests.
- Failure visibility: explicit blocked statuses with phase-local reason (`load_upstream`, `validate_upstream`, `evaluate_signal`, `apply_mitigation`, `write_bundle`) plus `missing_inputs` and insufficient-signal diagnostics.
- Redaction constraints: aggregate-only outputs; no raw review text and no demographic-inference columns in mitigation artifacts.

## Integration Closure

- Upstream surfaces consumed: `outputs/modeling/track_a/audit_intake/{scored_intake.parquet,manifest.json,validation_report.json}`, `outputs/modeling/track_e/fairness_audit/{subgroup_metrics.parquet,disparity_summary.parquet,manifest.json,validation_report.json}`, and `configs/track_e.yaml`.
- New wiring introduced in this slice: `src/modeling/common/mitigation_contract.py`, `src/modeling/track_e/mitigation_experiment.py`, Track E/common export updates, S03 contract/runtime/handoff tests, and S03 UAT + modeling README command contract.
- What remains before the milestone is truly usable end-to-end: S04 must close stronger/combined materiality gating, and S05 must run integrated closeout rerun + compute-escalation decision with S03 artifacts included.

## Tasks

- [x] **T01: Define mitigation bundle contract with threshold-delta schema and blocked vocab** `est:45m`
  - Why: S03 needs one strict output contract first so mitigation outputs are machine-consumable and cannot drift into narrative-only claims.
  - Files: `src/modeling/common/mitigation_contract.py`, `src/modeling/common/__init__.py`, `tests/test_m003_mitigation_contract.py`
  - Do: Add canonical schema constants for `pre_post_delta.parquet`, status vocabulary (`ready_for_closeout`, `blocked_upstream`, `blocked_insufficient_signal`), and validation helpers for delta columns plus boolean threshold fields.
  - Verify: `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_mitigation_contract.py -q`
  - Done when: contract tests pass and validators return deterministic diagnostics for missing columns, invalid status values, and malformed threshold booleans.
- [x] **T02: Implement mitigation runtime with residual-correction lever and fail-closed diagnostics** `est:1h 40m`
  - Why: R009 closure requires executable mitigation on real predictions with measurable pre/post fairness-vs-accuracy tradeoffs, not recommendation prose.
  - Files: `src/modeling/track_e/mitigation_experiment.py`, `src/modeling/track_e/__init__.py`, `tests/test_m003_track_e_mitigation_experiment.py`, `outputs/modeling/track_e/mitigation_experiment/pre_post_delta.parquet`, `outputs/modeling/track_e/mitigation_experiment/manifest.json`, `outputs/modeling/track_e/mitigation_experiment/validation_report.json`
  - Do: Build CLI gates on S01+S02 readiness, fit group-wise residual correction on non-test rows, apply/clamp mitigated predictions on test rows, compute baseline vs mitigated disparity + accuracy deltas, and write success/blocked bundles with phase-local diagnostics.
  - Verify: `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_e_mitigation_experiment.py -q && /mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.mitigation_experiment --config configs/track_e.yaml --intake-dir outputs/modeling/track_a/audit_intake --fairness-dir outputs/modeling/track_e/fairness_audit --output-dir outputs/modeling/track_e/mitigation_experiment`
  - Done when: success-path tests prove non-vacuous pre/post deltas on synthetic fixtures, and blocked-path tests prove deterministic `blocked_upstream` / `blocked_insufficient_signal` semantics.
- [x] **T03: Lock S03 handoff continuity and replay docs for S05 consumption** `est:50m`
  - Why: S05 and M004 handoff need one authoritative mitigation artifact contract with continuity guarantees and replayable triage instructions.
  - Files: `tests/test_m003_mitigation_handoff_contract.py`, `src/modeling/README.md`, `.gsd/milestones/M003-rdpeu4/slices/S03/S03-UAT.md`
  - Do: Add continuity regression checks for exact `split_context`/`baseline_anchor` propagation S02→S03 and required delta/threshold fields; document canonical S03 command/status semantics; author UAT replay + triage flow.
  - Verify: `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_mitigation_contract.py tests/test_m003_track_e_mitigation_experiment.py tests/test_m003_mitigation_handoff_contract.py -q && rg -n "mitigation_experiment|ready_for_closeout|blocked_insufficient_signal|pre_post_delta.parquet" src/modeling/README.md .gsd/milestones/M003-rdpeu4/slices/S03/S03-UAT.md`
  - Done when: handoff tests enforce continuity/contract invariants and docs let a fresh agent rerun and triage S03 without ad hoc path/schema discovery.

## Files Likely Touched

- `src/modeling/common/mitigation_contract.py`
- `src/modeling/common/__init__.py`
- `src/modeling/track_e/mitigation_experiment.py`
- `src/modeling/track_e/__init__.py`
- `src/modeling/README.md`
- `tests/test_m003_mitigation_contract.py`
- `tests/test_m003_track_e_mitigation_experiment.py`
- `tests/test_m003_mitigation_handoff_contract.py`
- `.gsd/milestones/M003-rdpeu4/slices/S03/S03-UAT.md`
- `outputs/modeling/track_e/mitigation_experiment/pre_post_delta.parquet`
- `outputs/modeling/track_e/mitigation_experiment/manifest.json`
- `outputs/modeling/track_e/mitigation_experiment/validation_report.json`
