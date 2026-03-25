# S07: Mitigation ready-path delta closure + closeout rerun

**Goal:** Unblock canonical M003 closeout by making S03 mitigation produce a non-empty, contract-valid pre/post fairness-vs-accuracy delta bundle on sparse real replay input, then rerun S05 so closeout resolves to `ready_for_handoff` with explicit escalation evidence.
**Demo:** Running `python -m src.modeling.track_e.mitigation_experiment --config configs/track_e.yaml --intake-dir outputs/modeling/track_a/audit_intake --fairness-dir outputs/modeling/track_e/fairness_audit --output-dir outputs/modeling/track_e/mitigation_experiment` followed by `python -m src.modeling.m003_closeout_gate --track-a-config configs/track_a.yaml --track-e-config configs/track_e.yaml --predictions outputs/modeling/track_a/predictions_test.parquet --metrics outputs/modeling/track_a/metrics.csv --candidate-metrics tests/fixtures/m003_candidate_metrics.csv --output-dir outputs/modeling/m003_closeout` yields `manifest.status=ready_for_closeout` for S03 and `manifest.status=ready_for_handoff` for S05 with `stage_rollup.readiness_block_stage_ids=[]`.

## Must-Haves

- Advance **R009 (active)** by closing the S03 sparse-path blocker so canonical mitigation replay emits a non-empty `pre_post_delta.parquet` with `status=ready_for_closeout` and `validation.status=pass`.
- Advance **R010 (active, supporting)** by preserving comparator continuity and readiness interpretation semantics when S05 is rerun after S03 is unblocked.
- Advance **R012 (active, supporting)** by preserving machine-readable continuity payloads (`baseline_anchor`, `split_context`) and canonical replay/triage documentation for M004 handoff consumers.
- Advance **R022 (active, supporting via rerun)** by proving closeout escalation remains evidence-based (`local_sufficient` unless runtime-capacity evidence appears) after mitigation ready-path closure.

## Proof Level

- This slice proves: final-assembly
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_mitigation_contract.py tests/test_m003_track_e_mitigation_experiment.py tests/test_m003_mitigation_handoff_contract.py tests/test_m003_milestone_closeout_gate.py tests/test_m003_closeout_handoff_contract.py -q`
- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.mitigation_experiment --config configs/track_e.yaml --intake-dir outputs/modeling/track_a/audit_intake --fairness-dir outputs/modeling/track_e/fairness_audit --output-dir outputs/modeling/track_e/mitigation_experiment`
- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY'
import json
from pathlib import Path
import pandas as pd
from src.modeling.common import REQUIRED_PRE_POST_DELTA_COLUMNS

root = Path('outputs/modeling/track_e/mitigation_experiment')
manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
validation = json.loads((root / 'validation_report.json').read_text(encoding='utf-8'))
delta = pd.read_parquet(root / 'pre_post_delta.parquet')

assert manifest['status'] == 'ready_for_closeout', manifest['status']
assert validation['status'] == 'pass', validation['status']
assert len(delta) > 0, 'pre_post_delta must be non-empty'
assert set(REQUIRED_PRE_POST_DELTA_COLUMNS).issubset(delta.columns), set(REQUIRED_PRE_POST_DELTA_COLUMNS) - set(delta.columns)

forbidden = {'review_id','business_id','user_id','review_text','raw_text','text','gender','race','income','ethnicity','nationality'}
assert forbidden.isdisjoint(set(delta.columns)), forbidden.intersection(set(delta.columns))

lever_metadata = manifest.get('lever_metadata', {})
assert lever_metadata.get('evaluation_diagnostics'), 'evaluation diagnostics must be present'
print('m003 s07 mitigation ready-path bundle verified')
PY`
- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.m003_closeout_gate --track-a-config configs/track_a.yaml --track-e-config configs/track_e.yaml --predictions outputs/modeling/track_a/predictions_test.parquet --metrics outputs/modeling/track_a/metrics.csv --candidate-metrics tests/fixtures/m003_candidate_metrics.csv --output-dir outputs/modeling/m003_closeout`
- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY'
import json
from pathlib import Path
import pandas as pd

root = Path('outputs/modeling/m003_closeout')
manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
validation = json.loads((root / 'validation_report.json').read_text(encoding='utf-8'))
table = pd.read_parquet(root / 'stage_status_table.parquet')

assert manifest['status'] == 'ready_for_handoff', manifest['status']
assert manifest['compute_escalation_decision'] in {'local_sufficient', 'overflow_required'}
assert validation['status'] == 'pass', validation['status']
assert manifest['stage_rollup']['readiness_block_stage_ids'] == [], manifest['stage_rollup']

for key in ('baseline_anchor', 'split_context'):
    assert isinstance(manifest.get(key), dict) and manifest[key], f'{key} must be non-empty'

row = table.loc[table['stage_id'] == 's03_mitigation'].iloc[0]
assert row['manifest_status'] == 'ready_for_closeout', row.to_dict()
print('m003 s07 closeout ready-for-handoff verified')
PY`

## Observability / Diagnostics

- Runtime signals: mitigation `insufficient_signal`/`lever_metadata.evaluation_diagnostics` and closeout `stage_rollup` + `escalation` payloads must clearly show sparse-path behavior and readiness state.
- Inspection surfaces: `outputs/modeling/track_e/mitigation_experiment/{manifest.json,validation_report.json,pre_post_delta.parquet}`, `outputs/modeling/m003_closeout/{manifest.json,validation_report.json,stage_status_table.parquet,closeout_summary.md}`, and S07-targeted pytest suites.
- Failure visibility: blocked branches must expose deterministic reason codes (`no_correction_groups`, `no_comparison_rows_after_alignment`, or successor diagnostics) and phase-local checks rather than silent empty-success artifacts.
- Redaction constraints: mitigation and closeout artifacts remain aggregate-safe with no raw review text, row-level IDs, or demographic-inference columns.

## Integration Closure

- Upstream surfaces consumed: `outputs/modeling/track_a/audit_intake/`, `outputs/modeling/track_e/fairness_audit/`, `src/modeling/track_e/mitigation_experiment.py`, `src/modeling/m003_closeout_gate.py`, `tests/fixtures/m003_candidate_metrics.csv`, `configs/track_e.yaml`, `configs/track_a.yaml`.
- New wiring introduced in this slice: sparse-support mitigation evaluation path + diagnostics in S03 runtime, handoff contract assertions for sparse-path semantics, and canonical S05 rerun/assertion flow that confirms no readiness blocks remain.
- What remains before the milestone is truly usable end-to-end: nothing within M003 once S07 verification passes; M004 can consume canonical closeout evidence directly.

## Tasks

- [x] **T01: Implement sparse-support mitigation ready path with deterministic diagnostics** `est:2h`
  - Why: S07 is blocked by S03 `blocked_insufficient_signal` on tiny replay (`no_comparison_rows_after_alignment`) despite S06 fairness sufficiency being healthy.
  - Files: `src/modeling/track_e/mitigation_experiment.py`, `tests/test_m003_track_e_mitigation_experiment.py`, `tests/test_m003_mitigation_contract.py`
  - Do: Add regression-first coverage for sparse replay where primary test alignment is insufficient; implement bounded fallback evaluation that can still emit contract-valid non-empty pre/post deltas when mitigation evidence is materially computable; preserve existing status vocabulary and blocked semantics; publish explicit path diagnostics in `lever_metadata`/`insufficient_signal` so downstream readers can distinguish primary vs sparse fallback behavior.
  - Verify: `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_e_mitigation_experiment.py tests/test_m003_mitigation_contract.py -q`
  - Done when: mitigation runtime tests pass and sparse replay fixtures produce `status=ready_for_closeout` with non-empty `pre_post_delta.parquet` while blocked branches remain fail-closed and deterministic.
- [x] **T02: Lock sparse-path handoff contract and canonical mitigation replay docs** `est:1h15m`
  - Why: S07 needs continuity-safe, machine-readable diagnostics so S05/M004 consumers can interpret mitigation readiness without ad hoc branch inference.
  - Files: `tests/test_m003_mitigation_handoff_contract.py`, `src/modeling/README.md`, `.gsd/milestones/M003-rdpeu4/slices/S07/S07-UAT.md`
  - Do: Extend handoff tests to assert sparse-path diagnostics presence/shape plus exact continuity equality (`baseline_anchor`, `split_context`); update modeling docs with canonical sparse-path triage order and status interpretation; author S07 UAT playbook that runs mitigation replay + artifact assertions against canonical output paths.
  - Verify: `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_mitigation_contract.py tests/test_m003_track_e_mitigation_experiment.py tests/test_m003_mitigation_handoff_contract.py -q && rg -n "sparse|no_comparison_rows_after_alignment|ready_for_closeout|S07" src/modeling/README.md .gsd/milestones/M003-rdpeu4/slices/S07/S07-UAT.md`
  - Done when: handoff tests protect sparse-path diagnostics/continuity semantics and docs provide one authoritative S07 mitigation replay + triage flow.
- [x] **T03: Rerun closeout with S03-ready artifacts and lock handoff-readiness evidence** `est:1h30m`
  - Why: Slice completion requires proof that S05 now clears readiness blocks and emits handoff-ready evidence with escalation semantics unchanged.
  - Files: `tests/test_m003_milestone_closeout_gate.py`, `tests/test_m003_closeout_handoff_contract.py`, `outputs/modeling/track_e/mitigation_experiment/manifest.json`, `outputs/modeling/track_e/mitigation_experiment/validation_report.json`, `outputs/modeling/m003_closeout/manifest.json`, `outputs/modeling/m003_closeout/validation_report.json`, `.gsd/REQUIREMENTS.md`
  - Do: Add or tighten closeout regressions to assert S03 ready-path propagation into `stage_rollup.readiness_block_stage_ids=[]`; run canonical S03 then S05 commands to regenerate authoritative artifacts; assert `ready_for_handoff` + decision-vocabulary validity and continuity echoes; update requirement traceability notes for R009/R010/R012 (and R022 support) with S07 evidence references.
  - Verify: `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_milestone_closeout_gate.py tests/test_m003_closeout_handoff_contract.py -q && /mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.mitigation_experiment --config configs/track_e.yaml --intake-dir outputs/modeling/track_a/audit_intake --fairness-dir outputs/modeling/track_e/fairness_audit --output-dir outputs/modeling/track_e/mitigation_experiment && /mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.m003_closeout_gate --track-a-config configs/track_a.yaml --track-e-config configs/track_e.yaml --predictions outputs/modeling/track_a/predictions_test.parquet --metrics outputs/modeling/track_a/metrics.csv --candidate-metrics tests/fixtures/m003_candidate_metrics.csv --output-dir outputs/modeling/m003_closeout`
  - Done when: closeout tests pass, regenerated closeout artifact reports `ready_for_handoff` with empty readiness-block list, and requirement notes capture S07 advancement evidence.

## Files Likely Touched

- `src/modeling/track_e/mitigation_experiment.py`
- `tests/test_m003_track_e_mitigation_experiment.py`
- `tests/test_m003_mitigation_contract.py`
- `tests/test_m003_mitigation_handoff_contract.py`
- `tests/test_m003_milestone_closeout_gate.py`
- `tests/test_m003_closeout_handoff_contract.py`
- `src/modeling/README.md`
- `.gsd/milestones/M003-rdpeu4/slices/S07/S07-UAT.md`
- `.gsd/REQUIREMENTS.md`
- `outputs/modeling/track_e/mitigation_experiment/pre_post_delta.parquet`
- `outputs/modeling/track_e/mitigation_experiment/manifest.json`
- `outputs/modeling/track_e/mitigation_experiment/validation_report.json`
- `outputs/modeling/m003_closeout/stage_status_table.parquet`
- `outputs/modeling/m003_closeout/manifest.json`
- `outputs/modeling/m003_closeout/validation_report.json`
- `outputs/modeling/m003_closeout/closeout_summary.md`
