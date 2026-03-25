# S02 UAT — Model-aware fairness audit runtime on upstream predictions

This UAT script verifies the completed S02 fairness runtime and its downstream handoff contract.

## Preconditions

1. Run from repo root (`/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.gsd/worktrees/M003-rdpeu4`).
2. Use the project interpreter:
   - `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python`
3. S01 intake bundle exists at `outputs/modeling/track_a/audit_intake/` with:
   - `scored_intake.parquet`
   - `manifest.json` where `status == ready_for_fairness_audit`
   - `validation_report.json` where `status == pass`
4. No raw-text outputs are expected in fairness bundle artifacts.

---

## Test Case 1 — Contract + runtime + handoff regression suite

**Purpose:** prove schema/status contracts and downstream handoff checks stay aligned.

### Steps
1. Run:
   ```bash
   /mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest \
     tests/test_m003_fairness_audit_contract.py \
     tests/test_m003_track_e_fairness_audit.py \
     tests/test_m003_fairness_audit_handoff_contract.py -q
   ```

### Expected Outcomes
- Exit code is `0`.
- All tests pass.
- Coverage includes:
  - required column contract checks,
  - status vocabulary (`ready_for_mitigation`, `blocked_upstream`),
  - blocked-upstream failure behavior,
  - baseline/split continuity equality checks.

---

## Test Case 2 — Canonical fairness runtime replay

**Purpose:** prove one command regenerates the authoritative fairness bundle on real S01 intake predictions.

### Steps
1. Run:
   ```bash
   /mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.fairness_audit \
     --config configs/track_e.yaml \
     --intake-dir outputs/modeling/track_a/audit_intake \
     --output-dir outputs/modeling/track_e/fairness_audit
   ```

### Expected Outcomes
- Exit code is `0`.
- `outputs/modeling/track_e/fairness_audit/manifest.json` exists and has:
  - `status == "ready_for_mitigation"`
  - `phase == "write_bundle"`
  - `validation_status == "pass"`
- `outputs/modeling/track_e/fairness_audit/validation_report.json` exists and has:
  - `status == "pass"`
  - `phase == "write_bundle"`
  - populated `phases[]` timeline.

---

## Test Case 3 — Artifact contract + schema sanity check

**Purpose:** prove bundle file presence and required table columns for downstream S03/S04/S05 consumption.

### Steps
1. Run:
   ```bash
   /mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY'
   import json
   from pathlib import Path
   import pandas as pd

   root = Path('outputs/modeling/track_e/fairness_audit')
   required_files = {
       'subgroup_metrics.parquet',
       'disparity_summary.parquet',
       'manifest.json',
       'validation_report.json',
   }
   missing = [name for name in required_files if not (root / name).is_file()]
   assert not missing, missing

   manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
   validation = json.loads((root / 'validation_report.json').read_text(encoding='utf-8'))
   assert manifest['status'] == 'ready_for_mitigation', manifest['status']
   assert validation['status'] == 'pass', validation['status']

   subgroup = pd.read_parquet(root / 'subgroup_metrics.parquet')
   disparity = pd.read_parquet(root / 'disparity_summary.parquet')

   subgroup_required = {
       'subgroup_type', 'subgroup_value', 'support_count',
       'mean_y_true', 'mean_y_pred', 'mean_signed_error',
       'mae', 'rmse', 'within_1_star_rate',
   }
   disparity_required = {
       'subgroup_type', 'metric_name', 'reference_group', 'comparison_group',
       'reference_value', 'comparison_value', 'delta', 'exceeds_threshold',
   }
   assert subgroup_required.issubset(subgroup.columns), subgroup_required - set(subgroup.columns)
   assert disparity_required.issubset(disparity.columns), disparity_required - set(disparity.columns)

   forbidden = {
       'review_id', 'business_id', 'user_id', 'review_text', 'raw_text', 'text',
       'gender', 'race', 'income', 'ethnicity', 'nationality'
   }
   assert forbidden.isdisjoint(subgroup.columns), forbidden.intersection(subgroup.columns)
   assert forbidden.isdisjoint(disparity.columns), forbidden.intersection(disparity.columns)

   print('m003 s02 fairness bundle verified')
   PY
   ```

### Expected Outcomes
- Exit code is `0`.
- Script prints `m003 s02 fairness bundle verified`.
- Required columns exist even when row count is zero.
- No forbidden raw-text/demographic-inference columns appear.

---

## Test Case 4 — Blocked-upstream failure-path visibility

**Purpose:** prove fail-closed semantics and deterministic diagnostics for missing/bad upstream intake inputs.

### Steps
1. Run blocked-upstream regression subset:
   ```bash
   /mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest \
     tests/test_m003_track_e_fairness_audit.py -k blocked_upstream -q
   ```

### Expected Outcomes
- Exit code is `0`.
- Tests confirm runtime emits:
  - `manifest.status == "blocked_upstream"`
  - failure `phase` of `load_intake_manifest` or `validate_intake`
  - `missing_inputs` / missing-column diagnostics in `validation_report.json`.

---

## Edge Cases to Validate During Triage

1. **Empty but valid fairness tables**
   - If `subgroup_metrics.parquet` and `disparity_summary.parquet` have 0 rows but status is pass, inspect:
     - `manifest.row_counts.dropped_by_min_group_size`
   - This is expected when `subgroups.min_group_size` filters all candidate groups.

2. **Missing curated business parquet**
   - Runtime should still be able to complete by synthesizing business context from intake `business_id` values.
   - Do not assume missing `data/curated/business.parquet` implies blocked status.

3. **Baseline continuity drift**
   - `manifest.json` and `validation_report.json` must preserve exact S01 `split_context` and `baseline_anchor` payloads.
   - Any mismatch should fail `tests/test_m003_fairness_audit_handoff_contract.py`.

---

## Fast Triage Order (if any check fails)

1. `outputs/modeling/track_e/fairness_audit/manifest.json`
   - `status`, `phase`, `row_counts`, `threshold_checks`, `upstream_paths`
2. `outputs/modeling/track_e/fairness_audit/validation_report.json`
   - `status`, `phase`, `message`, `checks[]`, `phases[]`, `missing_inputs`
3. `outputs/modeling/track_a/audit_intake/{manifest.json,validation_report.json,scored_intake.parquet}`
4. Regression tests:
   - `tests/test_m003_track_e_fairness_audit.py`
   - `tests/test_m003_fairness_audit_handoff_contract.py`

---

## Handoff Ready Definition

S02 is handoff-ready when all four test cases pass and `outputs/modeling/track_e/fairness_audit/` contains the canonical bundle with `ready_for_mitigation` status and pass validation diagnostics, consumable without path/schema/status guesswork by S03/S04/S05.
