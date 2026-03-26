# S01: Upstream audit-intake contract on reproducible scored artifacts — UAT

**Milestone:** M003-rdpeu4  
**Slice:** S01  
**Written:** 2026-03-23

## UAT Type

- UAT mode: integration + contract + failure-path diagnostics
- Why this mode is sufficient: S01 acceptance depends on one reproducible intake runtime plus schema/handoff regression coverage and explicit blocked-upstream visibility.

## Preconditions

1. Run from repo root in this worktree: `.gsd/worktrees/M003-rdpeu4`.
2. Use project interpreter (required in this harness):
   - `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python`
3. Required upstream inputs exist:
   - `outputs/modeling/track_a/predictions_test.parquet`
   - `outputs/modeling/track_a/metrics.csv`
   - `data/curated/review_fact.parquet`
   - `outputs/tables/track_a_s5_candidate_splits.parquet`
4. Output directory is writable:
   - `outputs/modeling/track_a/audit_intake/`

## Smoke Test (full slice gate)

Run in order:

1. ` /mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_audit_intake_contract.py tests/test_m003_track_a_audit_intake.py tests/test_m003_intake_handoff_contract.py`
2. ` /mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_a.audit_intake --config configs/track_a.yaml --predictions outputs/modeling/track_a/predictions_test.parquet --metrics outputs/modeling/track_a/metrics.csv --output-dir outputs/modeling/track_a/audit_intake`
3. Run the contract verification snippet below (Test Case 3).
4. ` /mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_a_audit_intake.py -k missing_predictions_emits_diagnostics`

Expected smoke outcome: all commands pass; bundle is `ready_for_fairness_audit`; failure-path diagnostics remain explicit.

## Test Cases

### 1) Contract + runtime + handoff regression suite

Run:

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest \
  tests/test_m003_audit_intake_contract.py \
  tests/test_m003_track_a_audit_intake.py \
  tests/test_m003_intake_handoff_contract.py
```

Expected:

- All tests pass.
- Contract checks cover required columns, non-null, duplicate PK, forbidden columns.
- Runtime checks cover happy path + missing predictions + malformed schema.
- Handoff checks enforce `ready_for_fairness_audit`, `split_context`, `baseline_anchor`, and minimum scored-intake schema.

### 2) Canonical intake CLI regeneration

Run:

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_a.audit_intake \
  --config configs/track_a.yaml \
  --predictions outputs/modeling/track_a/predictions_test.parquet \
  --metrics outputs/modeling/track_a/metrics.csv \
  --output-dir outputs/modeling/track_a/audit_intake
```

Expected:

- Exit code is 0.
- `outputs/modeling/track_a/audit_intake/` contains:
  - `scored_intake.parquet`
  - `manifest.json`
  - `validation_report.json`

### 3) Bundle contract verification (required fields + readiness state)

Run:

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY'
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
assert manifest['phase'] == 'write_bundle'
assert validation['phase'] == 'write_bundle'

print('m003 s01 intake bundle verified')
PY
```

Expected:

- Script prints `m003 s01 intake bundle verified`.
- No required columns missing.
- Manifest/validation statuses indicate downstream-ready handoff.

### 4) Edge case: missing predictions input emits blocked-upstream diagnostics

Run:

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest \
  tests/test_m003_track_a_audit_intake.py -k missing_predictions_emits_diagnostics
```

Expected:

- Test passes.
- Failure path emits diagnostics JSON with:
  - `manifest.status == "blocked_upstream"`
  - `validation_report.status == "fail"`
  - `validation_report.phase == "load_predictions"`
  - `missing_inputs` includes `predictions`

### 5) Edge case: malformed predictions schema fails at validation phase

Run:

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest \
  tests/test_m003_track_a_audit_intake.py -k malformed_predictions_schema_emits_validation_failure
```

Expected:

- Test passes.
- Failure path reports:
  - `validation_report.status == "fail"`
  - `validation_report.phase == "validate_schema"`
  - missing column includes `y_pred`

### 6) Observability shape check (phase timeline + counts)

Run:

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY'
import json
from pathlib import Path

root = Path('outputs/modeling/track_a/audit_intake')
manifest = json.loads((root / 'manifest.json').read_text())
validation = json.loads((root / 'validation_report.json').read_text())

assert manifest['row_count'] == validation['row_count']
required_phases = {'load_predictions','load_metrics','load_review_fact','join_keys','validate_schema','write_bundle'}
seen = {phase['name'] for phase in validation.get('phases', [])}
missing = required_phases - seen
assert not missing, missing

print('observability surfaces verified')
PY
```

Expected:

- Script prints `observability surfaces verified`.
- Timeline includes every declared S01 phase.

## Executed Evidence (2026-03-23)

| # | Command | Exit | Evidence |
|---|---|---|---|
| 1 | Full S01 pytest gate (3 files) | 0 | `10 passed` |
| 2 | `src.modeling.track_a.audit_intake` canonical rerun | 0 | Logger confirms bundle ready |
| 3 | Required-columns + ready/pass verification snippet | 0 | Printed `m003 s01 intake bundle verified` |
| 4 | Missing-predictions edge test | 0 | `1 passed` |
| 5 | Malformed-schema edge test | 0 | `1 passed` |
| 6 | Observability shape snippet | 0 | Printed `observability surfaces verified` |

## Failure Signals

- Any non-zero exit from pytest gate or CLI regeneration.
- `manifest.status != ready_for_fairness_audit` on happy path.
- `validation_report.status != pass` on happy path.
- Missing required intake columns in `scored_intake.parquet`.
- Failure diagnostics missing phase/status/missing-input fields.

## Requirements Proved by This UAT

- S01 prerequisite proof for R009: reproducible upstream intake contract ready for fairness audit runtime.
- S01 prerequisite proof for R010: baseline anchor metadata available for materiality comparator inputs.
- Continuity support toward R012: deterministic handoff surface for downstream M003 evidence assembly.

## Not Proved by This UAT

- Fairness disparity metric outcomes (S02).
- Mitigation pre/post fairness-accuracy deltas (S03).
- Stronger/combined model adoption decisions under materiality gate (S04).
- Integrated closeout rerun and compute escalation disposition (S05).
