# S05: Integrated closeout gate with conditional compute-escalation decision

**Goal:** Deliver one canonical M003 closeout runtime that reruns S01→S04, aggregates readiness/continuity evidence, and emits an explicit compute-escalation decision (`local_sufficient` or `overflow_required`) with machine-readable diagnostics.
**Demo:** Running `python -m src.modeling.m003_closeout_gate ...` writes `outputs/modeling/m003_closeout/` containing `stage_status_table.parquet`, `manifest.json`, `validation_report.json`, and `closeout_summary.md`, where stage statuses, continuity echoes, and escalation trigger evaluation are deterministic and contract-validated.

## Must-Haves

- Advance **R009** by composing S02 fairness + S03 mitigation evidence into one closeout surface that preserves blocked-insufficient-signal truth (no success masking, no exit-code-only interpretation).
- Advance **R010** by carrying S04 comparator materiality/adoption context (including runtime/fairness gates) into the integrated closeout decision payload.
- Close **R022** ownership by evaluating explicit escalation triggers and emitting only `local_sufficient` or `overflow_required` based on measured runtime/diagnostic evidence.
- Advance **R012** continuity by publishing canonical replay/handoff docs/tests and aligning `.gsd/REQUIREMENTS.md` traceability for S05-supported closeout evidence.

## Proof Level

- This slice proves: final-assembly
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_closeout_contract.py tests/test_m003_milestone_closeout_gate.py tests/test_m003_closeout_handoff_contract.py -q`
- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_audit_intake_contract.py tests/test_m003_track_a_audit_intake.py tests/test_m003_intake_handoff_contract.py tests/test_m003_fairness_audit_contract.py tests/test_m003_track_e_fairness_audit.py tests/test_m003_fairness_audit_handoff_contract.py tests/test_m003_mitigation_contract.py tests/test_m003_track_e_mitigation_experiment.py tests/test_m003_mitigation_handoff_contract.py tests/test_m003_comparator_contract.py tests/test_m003_track_a_stronger_comparator.py tests/test_m003_comparator_handoff_contract.py tests/test_m003_closeout_contract.py tests/test_m003_milestone_closeout_gate.py tests/test_m003_closeout_handoff_contract.py -q`
- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.m003_closeout_gate --track-a-config configs/track_a.yaml --track-e-config configs/track_e.yaml --predictions outputs/modeling/track_a/predictions_test.parquet --metrics outputs/modeling/track_a/metrics.csv --candidate-metrics tests/fixtures/m003_candidate_metrics.csv --output-dir outputs/modeling/m003_closeout`
- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY'
import json
from pathlib import Path
import pandas as pd

root = Path('outputs/modeling/m003_closeout')
required = {'stage_status_table.parquet', 'manifest.json', 'validation_report.json', 'closeout_summary.md'}
missing = [name for name in required if not (root / name).is_file()]
assert not missing, missing

manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
validation = json.loads((root / 'validation_report.json').read_text(encoding='utf-8'))
table = pd.read_parquet(root / 'stage_status_table.parquet')

assert manifest['status'] in {'ready_for_handoff', 'blocked_upstream'}, manifest['status']
assert manifest['compute_escalation_decision'] in {'local_sufficient', 'overflow_required'}, manifest['compute_escalation_decision']
assert validation['status'] in {'pass', 'fail'}, validation['status']

expected_stages = {'s01_intake', 's02_fairness', 's03_mitigation', 's04_comparator'}
assert expected_stages.issubset(set(table['stage_id'].tolist())), table['stage_id'].tolist()
required_cols = {
    'stage_id', 'manifest_status', 'validation_status', 'phase',
    'duration_seconds', 'is_hard_block', 'is_soft_block', 'artifact_dir'
}
assert required_cols.issubset(set(table.columns)), required_cols - set(table.columns)

forbidden_cols = {'review_id', 'user_id', 'business_id', 'review_text', 'raw_text', 'text', 'gender', 'race', 'income', 'ethnicity', 'nationality'}
assert forbidden_cols.isdisjoint(set(table.columns)), forbidden_cols.intersection(set(table.columns))

assert 'baseline_anchor' in manifest, 'baseline_anchor missing'
assert 'split_context' in manifest, 'split_context missing'
print('m003 s05 closeout bundle verified')
PY`

## Observability / Diagnostics

- Runtime signals: closeout `manifest.json` and `validation_report.json` expose stage matrix rollup, continuity checks, trigger evaluations, escalation decision, and phase-local diagnostics.
- Inspection surfaces: `python -m src.modeling.m003_closeout_gate ...`, `outputs/modeling/m003_closeout/{stage_status_table.parquet,manifest.json,validation_report.json,closeout_summary.md}`, and S05 contract/integration/handoff tests.
- Failure visibility: explicit hard/soft block flags per stage, missing input echoes, failed check names, and escalation trigger rationale rather than ambiguous command-exit interpretation.
- Redaction constraints: closeout artifacts remain aggregate/contract metadata only (no raw review text, no row-level IDs, no demographic inference columns).

## Integration Closure

- Upstream surfaces consumed: `outputs/modeling/track_a/audit_intake/`, `outputs/modeling/track_e/fairness_audit/`, `outputs/modeling/track_e/mitigation_experiment/`, `outputs/modeling/track_a/stronger_comparator/`, `configs/track_a.yaml`, `configs/track_e.yaml`, and `tests/fixtures/m003_candidate_metrics.csv`.
- New wiring introduced in this slice: `src/modeling/common/closeout_contract.py` + `src/modeling/m003_closeout_gate.py` composition runtime, S05 contract/integration/handoff tests, and canonical S05 replay docs.
- What remains before the milestone is truly usable end-to-end: nothing inside M003 once closeout replay and escalation disposition pass; M004 consumes this handoff surface for reporting/showcase assembly.

## Tasks

- [x] **T01: Define S05 closeout contract and escalation/status validators** `est:45m`
  - Why: S05 needs a shared contract first so closeout status, stage-table schema, and escalation decision semantics cannot drift across runtime/tests/docs.
  - Files: `src/modeling/common/closeout_contract.py`, `src/modeling/common/__init__.py`, `tests/test_m003_closeout_contract.py`
  - Do: Add closeout schema constants (required stage rows/columns, status vocabulary, escalation decision vocabulary), validation helpers for stage table + manifest fields, and deterministic diagnostics payloads for invalid status/decision/schema branches.
  - Verify: `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_closeout_contract.py -q`
  - Done when: contract tests pass and invalid stage IDs, malformed booleans, invalid status values, and invalid escalation decisions all fail with machine-readable diagnostics.
- [x] **T02: Implement integrated closeout runtime and decision gate over S01→S04 bundles** `est:2h`
  - Why: R009/R010/R022 closure depends on one executable rerun that composes prior slices and emits a deterministic closeout + escalation decision artifact bundle.
  - Files: `src/modeling/m003_closeout_gate.py`, `src/modeling/__init__.py`, `tests/test_m003_milestone_closeout_gate.py`, `outputs/modeling/m003_closeout/stage_status_table.parquet`, `outputs/modeling/m003_closeout/manifest.json`, `outputs/modeling/m003_closeout/validation_report.json`, `outputs/modeling/m003_closeout/closeout_summary.md`
  - Do: Implement CLI orchestration for canonical S01/S02/S03/S04 commands, always ingest stage manifests/validation reports, derive hard/soft block matrix, evaluate escalation triggers (including overflow-required branches and non-trigger handling for fairness-signal scarcity), and write deterministic ready/blocked closeout artifacts.
  - Verify: `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_milestone_closeout_gate.py -q && /mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.m003_closeout_gate --track-a-config configs/track_a.yaml --track-e-config configs/track_e.yaml --predictions outputs/modeling/track_a/predictions_test.parquet --metrics outputs/modeling/track_a/metrics.csv --candidate-metrics tests/fixtures/m003_candidate_metrics.csv --output-dir outputs/modeling/m003_closeout`
  - Done when: integration tests cover ready/local-sufficient, blocked-upstream propagation, blocked-insufficient-signal (still local-sufficient), and overflow-required branches, and canonical closeout bundle files are regenerated.
- [x] **T03: Lock S05 handoff continuity docs and requirement traceability alignment** `est:1h`
  - Why: R012 continuity requires a canonical closeout replay/triage surface and requirement traceability that downstream M004 work can consume without reconstruction.
  - Files: `tests/test_m003_closeout_handoff_contract.py`, `src/modeling/README.md`, `.gsd/milestones/M003-rdpeu4/slices/S05/S05-UAT.md`, `.gsd/REQUIREMENTS.md`
  - Do: Add handoff regression checks for stage coverage, continuity echoes (`baseline_anchor`, `split_context`), status/decision vocab, and redaction constraints; document canonical S05 replay + triage semantics; update requirements traceability text so R022 is mapped to S05 conditional closure and R009/R010/R012 notes reference closeout evidence.
  - Verify: `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_closeout_contract.py tests/test_m003_milestone_closeout_gate.py tests/test_m003_closeout_handoff_contract.py -q && rg -n "m003_closeout_gate|stage_status_table.parquet|compute_escalation_decision|ready_for_handoff|overflow_required" src/modeling/README.md .gsd/milestones/M003-rdpeu4/slices/S05/S05-UAT.md .gsd/REQUIREMENTS.md`
  - Done when: handoff tests pass, docs give one authoritative replay/triage flow, and requirements traceability reflects S05’s active closeout/escalation ownership/support semantics.

## Files Likely Touched

- `src/modeling/common/closeout_contract.py`
- `src/modeling/common/__init__.py`
- `src/modeling/m003_closeout_gate.py`
- `src/modeling/__init__.py`
- `src/modeling/README.md`
- `tests/test_m003_closeout_contract.py`
- `tests/test_m003_milestone_closeout_gate.py`
- `tests/test_m003_closeout_handoff_contract.py`
- `.gsd/milestones/M003-rdpeu4/slices/S05/S05-UAT.md`
- `.gsd/REQUIREMENTS.md`
- `outputs/modeling/m003_closeout/stage_status_table.parquet`
- `outputs/modeling/m003_closeout/manifest.json`
- `outputs/modeling/m003_closeout/validation_report.json`
- `outputs/modeling/m003_closeout/closeout_summary.md`
