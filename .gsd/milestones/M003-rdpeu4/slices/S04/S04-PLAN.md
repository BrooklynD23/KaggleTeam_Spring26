# S04: Stronger/combined comparator with materiality gate

**Goal:** Deliver a canonical Track A stronger/combined comparator runtime that consumes S01 intake + S02 fairness artifacts and emits one machine-readable materiality decision bundle for adopt/do-not-adopt decisions.
**Demo:** Running `python -m src.modeling.track_a.stronger_comparator ...` writes `outputs/modeling/track_a/stronger_comparator/` with `materiality_table.parquet`, `manifest.json`, and `validation_report.json`; the bundle encodes baseline vs candidate gain, runtime cost, fairness-context gates, and `adopt_recommendation` with explicit decision reasons.

## Must-Haves

- Close **R010** ownership by producing a comparator artifact with baseline metric/runtime anchors, candidate metric/runtime values, signed gain/delta fields, materiality booleans, and a deterministic adoption decision gate.
- Advance **R009** support by wiring S02 fairness context directly into adoption logic (`fairness_context_ready`, `fairness_signal_available`) so metric-only improvements cannot auto-adopt.
- Advance **R012** continuity (+ **R022** support evidence) by preserving exact `split_context` + `baseline_anchor`, documenting one canonical replay path, and surfacing runtime-cost fields consumable by S05 escalation decisions.

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_comparator_contract.py tests/test_m003_track_a_stronger_comparator.py tests/test_m003_comparator_handoff_contract.py -q`
- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_a.stronger_comparator --config configs/track_a.yaml --intake-dir outputs/modeling/track_a/audit_intake --fairness-dir outputs/modeling/track_e/fairness_audit --candidate-metrics tests/fixtures/m003_candidate_metrics.csv --output-dir outputs/modeling/track_a/stronger_comparator`
- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY'
import json
from pathlib import Path
import pandas as pd

root = Path('outputs/modeling/track_a/stronger_comparator')
required_files = {'materiality_table.parquet', 'manifest.json', 'validation_report.json'}
missing = [name for name in required_files if not (root / name).is_file()]
assert not missing, missing

manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
validation = json.loads((root / 'validation_report.json').read_text(encoding='utf-8'))
table = pd.read_parquet(root / 'materiality_table.parquet')

allowed_status = {'ready_for_closeout', 'blocked_upstream'}
assert manifest['status'] in allowed_status, manifest['status']

required_cols = {
    'baseline_model_name', 'candidate_model_name', 'metric_name',
    'baseline_metric_value', 'candidate_metric_value', 'metric_gain',
    'min_metric_gain', 'material_improvement',
    'baseline_runtime_seconds', 'candidate_runtime_seconds', 'runtime_delta_seconds',
    'max_runtime_multiplier', 'runtime_within_budget',
    'fairness_context_ready', 'fairness_signal_available',
    'fairness_exceeds_threshold_count', 'adopt_recommendation', 'decision_reason'
}
assert required_cols.issubset(table.columns), required_cols - set(table.columns)

for bool_col in ['material_improvement', 'runtime_within_budget', 'fairness_context_ready', 'fairness_signal_available', 'adopt_recommendation']:
    assert pd.api.types.is_bool_dtype(table[bool_col]), (bool_col, table[bool_col].dtype)

if manifest['status'] == 'ready_for_closeout':
    assert validation['status'] == 'pass', validation['status']
else:
    assert validation['status'] == 'fail', validation['status']

forbidden = {'review_id', 'business_id', 'user_id', 'review_text', 'raw_text', 'text', 'gender', 'race', 'income', 'ethnicity', 'nationality'}
assert forbidden.isdisjoint(table.columns), forbidden.intersection(table.columns)
print('m003 s04 comparator bundle verified')
PY`
- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_a_stronger_comparator.py -k "blocked_upstream or no_fairness_signal" -q`

## Observability / Diagnostics

- Runtime signals: comparator `manifest.json` + `validation_report.json` expose phase progression, upstream gate checks, metric/runtime threshold checks, fairness-context booleans, and `adopt_recommendation` rationale.
- Inspection surfaces: `python -m src.modeling.track_a.stronger_comparator ...`, `outputs/modeling/track_a/stronger_comparator/{materiality_table.parquet,manifest.json,validation_report.json}`, and S04 regression tests.
- Failure visibility: blocked runs localize `load_upstream`, `validate_upstream`, `evaluate_materiality`, or `write_bundle` failures with `missing_inputs`, failed check names, and candidate-schema diagnostics.
- Redaction constraints: comparator outputs remain aggregate-only (no row-level IDs, no raw text, no demographic-inference columns).

## Integration Closure

- Upstream surfaces consumed: `outputs/modeling/track_a/audit_intake/{scored_intake.parquet,manifest.json,validation_report.json}`, `outputs/modeling/track_e/fairness_audit/{subgroup_metrics.parquet,disparity_summary.parquet,manifest.json,validation_report.json}`, `configs/track_a.yaml`, and `tests/fixtures/m003_candidate_metrics.csv`.
- New wiring introduced in this slice: `src/modeling/common/comparator_contract.py`, `src/modeling/track_a/stronger_comparator.py`, Track A/common export updates, comparator contract/runtime/handoff tests, and S04 README/UAT replay docs.
- What remains before the milestone is truly usable end-to-end: S05 must execute integrated closeout rerun and issue explicit `local_sufficient` vs `overflow_required` escalation disposition using S03 + S04 artifacts.

## Tasks

- [x] **T01: Define comparator contract and materiality schema validators** `est:45m`
  - Why: S04 needs a locked schema/status contract first so runtime outputs are machine-consumable and adoption semantics cannot drift.
  - Files: `src/modeling/common/comparator_contract.py`, `src/modeling/common/__init__.py`, `tests/test_m003_comparator_contract.py`
  - Do: Add comparator contract constants (schema/version, required columns, status vocabulary), dataframe validators for required fields + strict booleans, and manifest-status validator with deterministic diagnostics payloads.
  - Verify: `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_comparator_contract.py -q`
  - Done when: contract tests pass and validators fail deterministically on missing columns, malformed booleans, and invalid manifest statuses.
- [x] **T02: Implement stronger comparator runtime with fairness-aware materiality gate** `est:1h 45m`
  - Why: R010 closure requires an executable comparator on real S01/S02 artifacts that emits adoption decisions with runtime and fairness context, not narrative recommendations.
  - Files: `src/modeling/track_a/stronger_comparator.py`, `src/modeling/track_a/__init__.py`, `configs/track_a.yaml`, `tests/test_m003_track_a_stronger_comparator.py`, `tests/fixtures/m003_candidate_metrics.csv`, `outputs/modeling/track_a/stronger_comparator/materiality_table.parquet`, `outputs/modeling/track_a/stronger_comparator/manifest.json`, `outputs/modeling/track_a/stronger_comparator/validation_report.json`
  - Do: Build CLI gates for intake/fairness/candidate artifacts, compute baseline-vs-candidate metric gain + runtime budget checks + fairness-signal checks, derive `adopt_recommendation`/`decision_reason`, and write deterministic ready/blocked bundles.
  - Verify: `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_a_stronger_comparator.py -q && /mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_a.stronger_comparator --config configs/track_a.yaml --intake-dir outputs/modeling/track_a/audit_intake --fairness-dir outputs/modeling/track_e/fairness_audit --candidate-metrics tests/fixtures/m003_candidate_metrics.csv --output-dir outputs/modeling/track_a/stronger_comparator`
  - Done when: runtime tests prove ready/adopt, ready/do-not-adopt (no fairness signal), and blocked-upstream branches with deterministic artifact semantics.
- [x] **T03: Lock S04 handoff continuity and canonical replay docs for S05** `est:50m`
  - Why: S05/M004 need one authoritative comparator handoff surface with continuity guarantees and replayable triage instructions.
  - Files: `tests/test_m003_comparator_handoff_contract.py`, `src/modeling/README.md`, `.gsd/milestones/M003-rdpeu4/slices/S04/S04-UAT.md`
  - Do: Add handoff regression checks for exact `split_context`/`baseline_anchor` continuity, required materiality columns, and redaction constraints; document canonical S04 command/path/status semantics; author UAT replay + failure-triage steps.
  - Verify: `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_comparator_contract.py tests/test_m003_track_a_stronger_comparator.py tests/test_m003_comparator_handoff_contract.py -q && rg -n "stronger_comparator|materiality_table.parquet|ready_for_closeout|blocked_upstream|adopt_recommendation" src/modeling/README.md .gsd/milestones/M003-rdpeu4/slices/S04/S04-UAT.md`
  - Done when: handoff tests enforce continuity/contract invariants and docs let a fresh agent rerun + triage S04 without reconstructing paths or status rules.

## Files Likely Touched

- `src/modeling/common/comparator_contract.py`
- `src/modeling/common/__init__.py`
- `src/modeling/track_a/stronger_comparator.py`
- `src/modeling/track_a/__init__.py`
- `configs/track_a.yaml`
- `src/modeling/README.md`
- `tests/test_m003_comparator_contract.py`
- `tests/test_m003_track_a_stronger_comparator.py`
- `tests/test_m003_comparator_handoff_contract.py`
- `tests/fixtures/m003_candidate_metrics.csv`
- `.gsd/milestones/M003-rdpeu4/slices/S04/S04-UAT.md`
- `outputs/modeling/track_a/stronger_comparator/materiality_table.parquet`
- `outputs/modeling/track_a/stronger_comparator/manifest.json`
- `outputs/modeling/track_a/stronger_comparator/validation_report.json`
