# S02: Model-aware fairness audit runtime on upstream predictions

**Goal:** Convert the S01 scored-intake bundle into a deterministic, model-aware fairness audit runtime that reports subgroup fairness disparities with paired accuracy context on real upstream predictions.
**Demo:** Running one fairness-audit command from the S01 intake bundle produces `outputs/modeling/track_e/fairness_audit/` with `subgroup_metrics.parquet`, `disparity_summary.parquet`, `manifest.json`, and `validation_report.json`, where status/diagnostics are machine-readable and downstream mitigation work can consume the bundle without ad hoc repair.

## Must-Haves

- Deliver the first executable closure for **R009** by computing per-subgroup fairness metrics from real S01 predictions (not Track E data-only proxies), including support counts and paired accuracy context.
- Enforce fail-closed upstream gating against S01 readiness (`manifest.status == ready_for_fairness_audit`, `validation.status == pass`, and intake schema validity), emitting deterministic `blocked_upstream` diagnostics on failure.
- Produce a canonical fairness bundle contract (`subgroup_metrics`, `disparity_summary`, manifest, validation report) with threshold flags and baseline-anchor continuity fields so S03 and S04 can consume one stable surface.
- Add handoff tests/UAT docs that make S02 consumption and triage explicit, advancing **R012** continuity and preserving S04 fairness-context support for **R010** materiality decisions.

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_fairness_audit_contract.py tests/test_m003_track_e_fairness_audit.py tests/test_m003_fairness_audit_handoff_contract.py -q`
- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.fairness_audit --config configs/track_e.yaml --intake-dir outputs/modeling/track_a/audit_intake --output-dir outputs/modeling/track_e/fairness_audit`
- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY'
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
print('m003 s02 fairness bundle verified')
PY`
- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_e_fairness_audit.py -k blocked_upstream -q`

## Observability / Diagnostics

- Runtime signals: `outputs/modeling/track_e/fairness_audit/manifest.json` and `validation_report.json` expose status, phase timeline, row counts, threshold checks, and upstream path echoes.
- Inspection surfaces: fairness CLI entrypoint, bundle JSON/parquet outputs, and failure-path assertions in `tests/test_m003_track_e_fairness_audit.py`.
- Failure visibility: explicit `blocked_upstream` status with phase-local reason (`load_intake_manifest`, `validate_intake`, `join_subgroups`, `write_bundle`) and missing-input details.
- Redaction constraints: aggregate-only outputs; no raw text and no demographic-inference columns in written artifacts.

## Integration Closure

- Upstream surfaces consumed: `outputs/modeling/track_a/audit_intake/scored_intake.parquet`, `outputs/modeling/track_a/audit_intake/manifest.json`, `outputs/modeling/track_a/audit_intake/validation_report.json`, `data/curated/business.parquet`, `data/curated/review_fact.parquet`, `configs/track_e.yaml`.
- New wiring introduced in this slice: `src/modeling/common/fairness_audit_contract.py`, `src/modeling/track_e/fairness_audit.py`, Track E modeling package exports, and S02 contract/handoff regression tests.
- What remains before the milestone is truly usable end-to-end: S03 must apply one mitigation lever with authoritative pre/post deltas; S04 must complete stronger-model materiality gating; S05 must run integrated closeout/escalation decision.

## Tasks

- [x] **T01: Define the S02 fairness-audit bundle contract and lock failure semantics in tests** `est:45m`
  - Why: S02 needs a strict output contract before runtime code so fairness artifacts are machine-consumable and drift is caught early.
  - Files: `src/modeling/common/fairness_audit_contract.py`, `src/modeling/common/__init__.py`, `tests/test_m003_fairness_audit_contract.py`
  - Do: Add a fairness-audit contract helper that specifies required subgroup/disparity columns, status vocabulary (`ready_for_mitigation` / `blocked_upstream`), and validation payload structure; write contract tests for happy path and schema/status failure cases.
  - Verify: `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_fairness_audit_contract.py -q`
  - Done when: contract tests pass and the helper returns deterministic diagnostics for missing columns, invalid status, and threshold-flag shape drift.
- [x] **T02: Implement Track E model-aware fairness runtime from S01 intake with diagnostics bundle outputs** `est:1h 30m`
  - Why: R009 requires executable model-aware fairness outputs on real predictions, not descriptive EDA tables.
  - Files: `src/modeling/track_e/fairness_audit.py`, `src/modeling/track_e/__init__.py`, `tests/test_m003_track_e_fairness_audit.py`, `outputs/modeling/track_e/fairness_audit/manifest.json`, `outputs/modeling/track_e/fairness_audit/validation_report.json`
  - Do: Implement the CLI that gates on S01 manifest/validation/schema readiness, builds subgroup mappings (via Track E subgroup utilities), computes subgroup fairness + accuracy metrics and disparity deltas with threshold flags, and writes canonical bundle files while preserving fail-closed blocked diagnostics.
  - Verify: `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_e_fairness_audit.py -q && /mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.fairness_audit --config configs/track_e.yaml --intake-dir outputs/modeling/track_a/audit_intake --output-dir outputs/modeling/track_e/fairness_audit`
  - Done when: success runs emit `ready_for_mitigation` bundle artifacts and failure-path tests prove missing/non-ready intake yields `blocked_upstream` JSON diagnostics with phase-local reasons.
- [x] **T03: Lock S02 downstream handoff contract and UAT replay surfaces** `est:45m`
  - Why: S03/S04/S05 should consume one authoritative fairness bundle without rediscovering paths, statuses, or required columns.
  - Files: `tests/test_m003_fairness_audit_handoff_contract.py`, `src/modeling/README.md`, `.gsd/milestones/M003-rdpeu4/slices/S02/S02-UAT.md`
  - Do: Add handoff regression checks for required manifest keys, baseline-anchor continuity, and required subgroup/disparity columns; update modeling README with canonical S02 command/output layout; write S02 UAT replay/triage instructions.
  - Verify: `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_fairness_audit_contract.py tests/test_m003_track_e_fairness_audit.py tests/test_m003_fairness_audit_handoff_contract.py -q && rg -n "fairness_audit|ready_for_mitigation|disparity_summary.parquet" src/modeling/README.md .gsd/milestones/M003-rdpeu4/slices/S02/S02-UAT.md`
  - Done when: contract tests and docs point to one canonical fairness bundle and a fresh agent can rerun/triage S02 using only documented paths and commands.

## Files Likely Touched

- `src/modeling/common/fairness_audit_contract.py`
- `src/modeling/common/__init__.py`
- `src/modeling/track_e/fairness_audit.py`
- `src/modeling/track_e/__init__.py`
- `src/modeling/README.md`
- `tests/test_m003_fairness_audit_contract.py`
- `tests/test_m003_track_e_fairness_audit.py`
- `tests/test_m003_fairness_audit_handoff_contract.py`
- `.gsd/milestones/M003-rdpeu4/slices/S02/S02-UAT.md`
- `outputs/modeling/track_e/fairness_audit/subgroup_metrics.parquet`
- `outputs/modeling/track_e/fairness_audit/disparity_summary.parquet`
- `outputs/modeling/track_e/fairness_audit/manifest.json`
- `outputs/modeling/track_e/fairness_audit/validation_report.json`
