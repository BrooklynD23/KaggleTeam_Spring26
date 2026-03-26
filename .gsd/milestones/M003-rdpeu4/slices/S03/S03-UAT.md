# S03 UAT — One mitigation lever with pre/post fairness-accuracy deltas

This UAT script validates the S03 mitigation slice exactly as implemented: canonical runtime command, contract/handoff tests, deterministic blocked behavior, and machine-readable artifact triage for S05.

## Preconditions

1. Run from repo root: `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.gsd/worktrees/M003-rdpeu4`
2. Use interpreter: `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python`
3. Upstream artifacts exist:
   - `outputs/modeling/track_a/audit_intake/{scored_intake.parquet,manifest.json,validation_report.json}`
   - `outputs/modeling/track_e/fairness_audit/{subgroup_metrics.parquet,disparity_summary.parquet,manifest.json,validation_report.json}`
4. Target output path: `outputs/modeling/track_e/mitigation_experiment/`

---

## Test Case 1 — Contract + runtime + handoff regression gate

**Purpose:** verify schema/status vocab, mitigation behavior, and S02→S03 continuity locks in one pass.

### Steps
1. Run:
   ```bash
   /mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest \
     tests/test_m003_mitigation_contract.py \
     tests/test_m003_track_e_mitigation_experiment.py \
     tests/test_m003_mitigation_handoff_contract.py -q
   ```

### Expected Outcomes
- Exit code `0`
- All tests pass
- Coverage confirms:
  - allowed statuses: `ready_for_closeout`, `blocked_upstream`, `blocked_insufficient_signal`
  - required `pre_post_delta.parquet` schema
  - exact `split_context` + `baseline_anchor` continuity from fairness bundle to mitigation bundle
  - aggregate-safe/redaction constraints

---

## Test Case 2 — Canonical mitigation runtime replay

**Purpose:** prove one command regenerates the authoritative S03 bundle.

### Steps
1. Run:
   ```bash
   /mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.mitigation_experiment \
     --config configs/track_e.yaml \
     --intake-dir outputs/modeling/track_a/audit_intake \
     --fairness-dir outputs/modeling/track_e/fairness_audit \
     --output-dir outputs/modeling/track_e/mitigation_experiment
   ```

### Expected Outcomes
- Exit code `0`
- Files exist:
  - `outputs/modeling/track_e/mitigation_experiment/pre_post_delta.parquet`
  - `outputs/modeling/track_e/mitigation_experiment/manifest.json`
  - `outputs/modeling/track_e/mitigation_experiment/validation_report.json`
- `manifest.status` is one of:
  - `ready_for_closeout`
  - `blocked_upstream`
  - `blocked_insufficient_signal`
- `validation_report.phases[]` includes `load_upstream`, `validate_upstream`, and `write_bundle`

---

## Test Case 3 — Bundle contract assertion (ready/blocked branches)

**Purpose:** verify machine-readable schema guarantees and fail-closed blocked semantics.

### Steps
1. Run:
   ```bash
   /mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY'
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

   forbidden = {
       'review_id', 'business_id', 'user_id', 'review_text', 'raw_text', 'text',
       'gender', 'race', 'income', 'ethnicity', 'nationality'
   }
   assert forbidden.isdisjoint(delta.columns), forbidden.intersection(delta.columns)

   print('m003 s03 mitigation bundle verified')
   PY
   ```

### Expected Outcomes
- Exit code `0`
- Console prints: `m003 s03 mitigation bundle verified`
- Ready branch enforces full required pre/post columns
- Blocked branch enforces deterministic fail status + phase semantics

---

## Test Case 4 — Blocked-branch regression subset

**Purpose:** preserve deterministic blocked outcomes and avoid pytest selector drift.

### Steps
1. Run:
   ```bash
   /mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest \
     tests/test_m003_track_e_mitigation_experiment.py -k "blocked_upstream or insufficient_signal" -q
   ```

### Expected Outcomes
- Exit code `0`
- Two blocked tests pass (`blocked_upstream`, `blocked_insufficient_signal`)
- Selector still matches (no code-5 “deselected all” false failures)

---

## Edge Case A — Missing upstream intake path should block (not crash)

**Purpose:** verify fail-closed `blocked_upstream` bundle writing with exit code `0`.

### Steps
1. Run with an intentionally missing intake dir:
   ```bash
   /mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.mitigation_experiment \
     --config configs/track_e.yaml \
     --intake-dir outputs/modeling/track_a/does_not_exist \
     --fairness-dir outputs/modeling/track_e/fairness_audit \
     --output-dir outputs/modeling/track_e/mitigation_experiment_blocked_upstream
   ```
2. Inspect status quickly:
   ```bash
   /mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY'
   import json
   from pathlib import Path
   root = Path('outputs/modeling/track_e/mitigation_experiment_blocked_upstream')
   manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
   validation = json.loads((root / 'validation_report.json').read_text(encoding='utf-8'))
   assert manifest['status'] == 'blocked_upstream'
   assert validation['status'] == 'fail'
   assert 'intake_manifest' in manifest.get('missing_inputs', [])
   print('blocked_upstream semantics verified')
   PY
   ```

### Expected Outcomes
- Runtime command exits `0`
- Bundle files are still written
- `manifest.status == blocked_upstream`
- Validation reflects failure phase for missing upstream inputs

---

## Edge Case B — Ready-path delta generation remains enforced in tests

**Purpose:** ensure non-vacuous pre/post delta path remains covered even if real-data replay blocks.

### Steps
1. Run only the ready-path unit test:
   ```bash
   /mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest \
     tests/test_m003_track_e_mitigation_experiment.py -k "builds_ready_bundle" -q
   ```

### Expected Outcomes
- Exit code `0`
- Test asserts non-empty deltas, required columns, and mitigation-improves-metric expectations on controlled fixture data

---

## Triage Order (if any case fails)

1. `outputs/modeling/track_e/mitigation_experiment/manifest.json`
   - `status`, `phase`, `missing_inputs`, `insufficient_signal.reasons`, `baseline_anchor`, `split_context`
2. `outputs/modeling/track_e/mitigation_experiment/validation_report.json`
   - `status`, `phase`, `checks[]`, `phases[]`
3. Upstream manifests:
   - `outputs/modeling/track_a/audit_intake/manifest.json`
   - `outputs/modeling/track_e/fairness_audit/manifest.json`
4. Regression suites:
   - `tests/test_m003_track_e_mitigation_experiment.py`
   - `tests/test_m003_mitigation_handoff_contract.py`

---

## S03 Handoff-Ready Definition

S03 is handoff-ready when Test Cases 1–4 pass, edge-case checks behave as expected, and `outputs/modeling/track_e/mitigation_experiment/` contains canonical machine-readable artifacts with explicit status semantics consumable by S05 without reconstructing schema/path rules.
