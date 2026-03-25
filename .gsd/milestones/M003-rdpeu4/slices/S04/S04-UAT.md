# S04 UAT — Stronger comparator materiality gate

## Scope

Validate that S04 delivers a deterministic, fairness-aware stronger/combined comparator bundle for Track A with canonical status semantics (`ready_for_closeout`, `blocked_upstream`) and handoff-safe continuity payloads.

## Preconditions

1. Run from repo root:
   - `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.gsd/worktrees/M003-rdpeu4`
2. Use the project venv Python:
   - `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python`
3. Upstream S01/S02 artifacts exist:
   - `outputs/modeling/track_a/audit_intake/{scored_intake.parquet,manifest.json,validation_report.json}`
   - `outputs/modeling/track_e/fairness_audit/{subgroup_metrics.parquet,disparity_summary.parquet,manifest.json,validation_report.json}`
4. Candidate metrics fixture exists:
   - `tests/fixtures/m003_candidate_metrics.csv`

---

## Test Case 1 — Contract + runtime + handoff regression suite

### Steps

1. Run:

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest \
  tests/test_m003_comparator_contract.py \
  tests/test_m003_track_a_stronger_comparator.py \
  tests/test_m003_comparator_handoff_contract.py -q
```

### Expected outcome

- Exit code `0`.
- All tests pass (current expected count: 13).
- This confirms:
  - strict comparator schema/status validators,
  - ready/blocked runtime behavior,
  - continuity/redaction handoff invariants.

---

## Test Case 2 — Canonical ready replay (materiality bundle generation)

### Steps

1. Run comparator CLI:

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_a.stronger_comparator \
  --config configs/track_a.yaml \
  --intake-dir outputs/modeling/track_a/audit_intake \
  --fairness-dir outputs/modeling/track_e/fairness_audit \
  --candidate-metrics tests/fixtures/m003_candidate_metrics.csv \
  --output-dir outputs/modeling/track_a/stronger_comparator
```

2. Validate generated artifacts and contract fields:

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY'
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

assert manifest['status'] in {'ready_for_closeout', 'blocked_upstream'}, manifest['status']
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
PY
```

### Expected outcome

- CLI exits `0` and writes canonical bundle under `outputs/modeling/track_a/stronger_comparator/`.
- Assertion script prints `m003 s04 comparator bundle verified`.
- Gate columns are strict bool dtype.
- No forbidden raw-text/demographic columns appear.

---

## Test Case 3 — Targeted edge-branch regression: blocked + no-fairness-signal

### Steps

1. Run branch-focused test filter:

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest \
  tests/test_m003_track_a_stronger_comparator.py -k "blocked_upstream or no_fairness_signal" -q
```

### Expected outcome

- Exit code `0`.
- `blocked_upstream` and `no_fairness_signal` branch tests pass.
- Confirms required S04 behavior:
  - blocked branches still emit deterministic artifacts,
  - no-fairness-signal remains `ready_for_closeout` with `adopt_recommendation=false`.

---

## Test Case 4 — Manual blocked replay (candidate schema failure)

### Steps

1. Create malformed candidate metrics (missing `runtime_seconds`):

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY'
from pathlib import Path
import pandas as pd

path = Path('outputs/modeling/track_a/stronger_comparator_replay/candidate_metrics_missing_runtime.csv')
path.parent.mkdir(parents=True, exist_ok=True)
pd.DataFrame([
    {'model_name': 'track_a_candidate_v2', 'metric': 'rmse', 'value': 0.80}
]).to_csv(path, index=False)
print(path)
PY
```

2. Run comparator against malformed candidate input:

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_a.stronger_comparator \
  --config configs/track_a.yaml \
  --intake-dir outputs/modeling/track_a/audit_intake \
  --fairness-dir outputs/modeling/track_e/fairness_audit \
  --candidate-metrics outputs/modeling/track_a/stronger_comparator_replay/candidate_metrics_missing_runtime.csv \
  --output-dir outputs/modeling/track_a/stronger_comparator_replay/blocked_case
```

3. Assert blocked semantics and diagnostics:

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY'
import json
from pathlib import Path
import pandas as pd

root = Path('outputs/modeling/track_a/stronger_comparator_replay/blocked_case')
manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
validation = json.loads((root / 'validation_report.json').read_text(encoding='utf-8'))
table = pd.read_parquet(root / 'materiality_table.parquet')

assert manifest['status'] == 'blocked_upstream', manifest['status']
assert manifest['validation_status'] == 'fail', manifest['validation_status']
assert validation['status'] == 'fail', validation['status']
assert validation['phase'] == 'validate_upstream', validation['phase']
assert table.empty

check_map = {check['name']: check for check in validation['checks']}
assert check_map['candidate_metrics_schema']['status'] == 'fail'
print('S04 blocked replay verified')
PY
```

### Expected outcome

- Comparator process still exits `0` (artifact-first blocked semantics).
- Manifest/validation encode `blocked_upstream` + failure diagnostics.
- `materiality_table.parquet` remains contract-valid but empty.

---

## Test Case 5 — Documentation discoverability contract

### Steps

1. Run keyword scan across modeling README + S04 UAT:

```bash
rg -n "stronger_comparator|materiality_table.parquet|ready_for_closeout|blocked_upstream|adopt_recommendation" \
  src/modeling/README.md \
  .gsd/milestones/M003-rdpeu4/slices/S04/S04-UAT.md
```

### Expected outcome

- Exit code `0`.
- Both docs include canonical command/path, output files, and status/adoption interpretation keywords.

---

## Triage Guide (if a case fails)

1. Open `outputs/modeling/track_a/stronger_comparator/validation_report.json` and inspect `phase` + failing `checks[]`.
2. For blocked runs, trust `manifest.status`/`validation.status` rather than process exit code.
3. If continuity checks fail, compare `baseline_anchor` and `split_context` against upstream intake/fairness artifacts for exact equality.
4. If schema checks fail, verify candidate metrics columns: `model_name`, `metric`, `value`, `runtime_seconds`.

## Edge Cases Explicitly Covered

- **No fairness signal available:** still `ready_for_closeout`, but deterministic do-not-adopt recommendation.
- **Malformed candidate metrics schema:** deterministic `blocked_upstream` with contract-valid blocked bundle output.
- **Strict boolean typing drift:** caught by contract/runtime/handoff tests and artifact assertion script.
