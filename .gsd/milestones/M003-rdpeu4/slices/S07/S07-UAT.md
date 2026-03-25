# S07 UAT — Mitigation ready-path replay and closeout handoff

This playbook is the **only canonical replay order** for S07.

- Stage S03 target: mitigation bundle resolves to `ready_for_closeout` with non-empty `pre_post_delta.parquet`.
- Stage S05 target: closeout bundle resolves to `ready_for_handoff` with `stage_rollup.readiness_block_stage_ids=[]`.
- **Important:** treat artifact payloads (`manifest.json`, `validation_report.json`, tables/parquet) as the source of truth. Process exit code only indicates command execution, not readiness state.

## 1) Replay S03 mitigation bundle

Run from repo root:

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.mitigation_experiment \
  --config configs/track_e.yaml \
  --intake-dir outputs/modeling/track_a/audit_intake \
  --fairness-dir outputs/modeling/track_e/fairness_audit \
  --output-dir outputs/modeling/track_e/mitigation_experiment
```

Expected artifact root:

- `outputs/modeling/track_e/mitigation_experiment/manifest.json`
- `outputs/modeling/track_e/mitigation_experiment/validation_report.json`
- `outputs/modeling/track_e/mitigation_experiment/pre_post_delta.parquet`

### S03 assertion snippet

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY'
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
evaluation_diagnostics = lever_metadata.get('evaluation_diagnostics', {})
assert evaluation_diagnostics, 'evaluation diagnostics must be present'
assert evaluation_diagnostics.get('active_path') in {'primary_test_only', 'sparse_all_splits'}
assert isinstance(evaluation_diagnostics.get('sparse_fallback_activated'), bool)
print('S07 S03 mitigation ready-path bundle verified')
PY
```

## 2) Replay S05 closeout gate

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.m003_closeout_gate \
  --track-a-config configs/track_a.yaml \
  --track-e-config configs/track_e.yaml \
  --predictions outputs/modeling/track_a/predictions_test.parquet \
  --metrics outputs/modeling/track_a/metrics.csv \
  --candidate-metrics tests/fixtures/m003_candidate_metrics.csv \
  --output-dir outputs/modeling/m003_closeout
```

Expected artifact root:

- `outputs/modeling/m003_closeout/manifest.json`
- `outputs/modeling/m003_closeout/validation_report.json`
- `outputs/modeling/m003_closeout/stage_status_table.parquet`
- `outputs/modeling/m003_closeout/closeout_summary.md`

### S05 assertion snippet

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY'
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
print('S07 S05 closeout ready-for-handoff verified')
PY
```

## 3) Blocked-path triage (truthful fail-closed semantics)

If S03 is not ready:

- `manifest.status == blocked_insufficient_signal` means mitigation did not have enough evaluable subgroup signal.
- Inspect `manifest.insufficient_signal.reasons` and `manifest.lever_metadata.evaluation_diagnostics` first.
- `no_comparison_rows_after_alignment` is a valid, deterministic fail-closed reason (not a success state).
- `blocked_upstream` means S01/S02 inputs or contracts failed; fix upstream manifests/validation/schema before rerun.

Do not infer readiness from command success output; always inspect the artifacts above in order.
