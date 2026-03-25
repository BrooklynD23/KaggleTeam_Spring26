# S01: Upstream audit-intake contract on reproducible scored artifacts

**Goal:** Establish a reproducible Track A upstream scored-intake contract that downstream fairness, mitigation, and comparator slices can consume without ad hoc schema repair.
**Demo:** Running one Track A intake command regenerates a validated bundle (`scored_intake.parquet` + manifest/validation artifacts) with required IDs, split/as-of markers, truth/prediction fields, and subgroup join keys.

## Must-Haves

- Ship a machine-validated intake schema and validator for upstream scored artifacts, including required IDs, `split_name`, `as_of_date`, `y_true`, `y_pred`, `model_name`, and subgroup join keys.
- Provide a reproducible Track A intake builder command that emits a canonical bundle under `outputs/modeling/track_a/audit_intake/` and fails loudly when upstream scored artifacts are missing or malformed.
- Persist baseline metric/runtime anchor metadata in the intake bundle so stronger-model materiality comparisons have a stable baseline reference (supports roadmap continuity for R010).
- Produce handoff-ready contract docs/tests that make S02/S03/S04 consumption explicit and deterministic (supports roadmap continuity for R009 and R012).

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `python -m pytest tests/test_m003_audit_intake_contract.py tests/test_m003_track_a_audit_intake.py tests/test_m003_intake_handoff_contract.py`
- `python -m src.modeling.track_a.audit_intake --config configs/track_a.yaml --predictions outputs/modeling/track_a/predictions_test.parquet --metrics outputs/modeling/track_a/metrics.csv --output-dir outputs/modeling/track_a/audit_intake`
- `python - <<'PY'
import json
from pathlib import Path
import pandas as pd
root = Path('outputs/modeling/track_a/audit_intake')
scored = pd.read_parquet(root / 'scored_intake.parquet')
required = {'review_id','business_id','user_id','split_name','as_of_date','y_true','y_pred','model_name'}
missing = required - set(scored.columns)
assert not missing, missing
manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
validation = json.loads((root / 'validation_report.json').read_text(encoding='utf-8'))
assert manifest['status'] == 'ready_for_fairness_audit'
assert validation['status'] == 'pass'
print('m003 s01 intake bundle verified')
PY`
- `python -m pytest tests/test_m003_track_a_audit_intake.py -k missing_predictions_emits_diagnostics`

## Observability / Diagnostics

- Runtime signals: `outputs/modeling/track_a/audit_intake/validation_report.json`, `outputs/modeling/track_a/audit_intake/manifest.json`, and intake row-count/null-count fields embedded in those JSON surfaces.
- Inspection surfaces: `python -m src.modeling.track_a.audit_intake ...`, the generated intake bundle directory, and `tests/test_m003_track_a_audit_intake.py` failure-path assertions.
- Failure visibility: explicit phase/status values (`load_predictions`, `join_keys`, `validate_schema`, `write_bundle`), missing-field lists, upstream path echoing, and timestamps in diagnostics JSON.
- Redaction constraints: no raw review text columns or demographic-inference fields may appear in intake artifacts; diagnostics may report column names/counts only.

## Integration Closure

- Upstream surfaces consumed: `outputs/modeling/track_a/predictions_test.parquet`, `outputs/modeling/track_a/metrics.csv`, `data/curated/review_fact.parquet`, `outputs/tables/track_a_s5_candidate_splits.parquet`, `configs/track_a.yaml`.
- New wiring introduced in this slice: `src/modeling/common/audit_intake_contract.py`, `src/modeling/track_a/audit_intake.py`, and M003 intake contract tests/docs.
- What remains before the milestone is truly usable end-to-end: S02 must compute model-aware fairness metrics from this intake; S03 must run mitigation pre/post deltas; S04/S05 must consume baseline anchors for materiality and closeout gating.

## Tasks

- [x] **T01: Codify the upstream scored-intake schema contract and validator tests** `est:45m`
  - Why: S01 cannot be trusted unless the required intake fields and failure behavior are mechanically enforced before runtime wiring.
  - Files: `src/modeling/common/audit_intake_contract.py`, `tests/test_m003_audit_intake_contract.py`, `src/modeling/common/__init__.py`
  - Do: Define the canonical intake column contract, schema-version metadata, and validator output shape (pass/fail, missing columns, null/duplicate checks, forbidden-column checks); add focused pytest coverage for valid input, missing required fields, duplicate keys, and banned text/demographic columns.
  - Verify: `python -m pytest tests/test_m003_audit_intake_contract.py`
  - Done when: validator behavior is deterministic and all contract regressions fail with explicit machine-readable diagnostics.
- [x] **T02: Implement Track A audit-intake builder CLI and canonical bundle outputs** `est:1h 15m`
  - Why: Downstream fairness/mitigation slices need a reproducible command that turns upstream predictions into a ready-to-consume intake artifact bundle.
  - Files: `src/modeling/track_a/audit_intake.py`, `src/modeling/track_a/__init__.py`, `src/modeling/common/audit_intake_contract.py`, `tests/test_m003_track_a_audit_intake.py`, `outputs/modeling/track_a/audit_intake/`
  - Do: Build a Track A intake entrypoint that loads predictions and baseline metrics, joins required IDs/split/as-of context from curated or split artifacts, validates with the new contract, writes `scored_intake.parquet` plus `manifest.json`/`validation_report.json`, and emits structured failure diagnostics when upstream inputs are absent or malformed.
  - Verify: `python -m pytest tests/test_m003_track_a_audit_intake.py && python -m src.modeling.track_a.audit_intake --config configs/track_a.yaml --predictions outputs/modeling/track_a/predictions_test.parquet --metrics outputs/modeling/track_a/metrics.csv --output-dir outputs/modeling/track_a/audit_intake`
  - Done when: rerunning the CLI regenerates the same contract-compliant bundle and failure-path tests confirm missing-input diagnostics are explicit.
- [x] **T03: Lock downstream handoff wiring with intake contract regression + runbook updates** `est:45m`
  - Why: S01 only closes if future slices can consume the intake bundle without guessing paths, schema semantics, or baseline anchor fields.
  - Files: `tests/test_m003_intake_handoff_contract.py`, `src/modeling/README.md`, `.gsd/milestones/M003-rdpeu4/slices/S01/S01-UAT.md`
  - Do: Add a handoff regression test that asserts required manifest keys/column names and ready-for-audit status, update modeling docs with the authoritative intake command and bundle layout, and create an S01 UAT checklist that downstream slices can replay before fairness/mitigation/comparator runs.
  - Verify: `python -m pytest tests/test_m003_intake_handoff_contract.py && rg -n "audit_intake|ready_for_fairness_audit|scored_intake.parquet" src/modeling/README.md .gsd/milestones/M003-rdpeu4/slices/S01/S01-UAT.md`
  - Done when: tests and docs point to one canonical intake surface and a fresh agent can bootstrap S02/S03/S04 consumption using only the documented command and bundle.

## Files Likely Touched

- `src/modeling/common/audit_intake_contract.py`
- `src/modeling/common/__init__.py`
- `src/modeling/track_a/audit_intake.py`
- `src/modeling/track_a/__init__.py`
- `src/modeling/README.md`
- `tests/test_m003_audit_intake_contract.py`
- `tests/test_m003_track_a_audit_intake.py`
- `tests/test_m003_intake_handoff_contract.py`
- `.gsd/milestones/M003-rdpeu4/slices/S01/S01-UAT.md`
- `outputs/modeling/track_a/audit_intake/scored_intake.parquet`
- `outputs/modeling/track_a/audit_intake/manifest.json`
- `outputs/modeling/track_a/audit_intake/validation_report.json`
