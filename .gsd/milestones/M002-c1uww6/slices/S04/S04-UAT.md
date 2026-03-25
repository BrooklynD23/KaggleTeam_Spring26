# S04: Track C monitoring baseline contract — UAT

**Milestone:** M002-c1uww6
**Written:** 2026-03-23

## UAT Type

- UAT mode: mixed
- Why this mode is sufficient: S04 is accepted on executable monitoring runtime behavior plus drift-surface/schema/wording contract checks.

## Preconditions

- Stage 4, Stage 6, and Stage 8 aggregate artifacts expected by `configs/track_c.yaml` are available.
- Python environment can run project modules and pytest.
- `outputs/modeling/track_c/` is writable.

## Smoke Test

Run:

```bash
python -m src.modeling.track_c.baseline --config configs/track_c.yaml
```

Then verify:

```bash
test -f outputs/modeling/track_c/drift_surface.parquet
test -f outputs/modeling/track_c/metrics.csv
test -f outputs/modeling/track_c/config_snapshot.json
test -f outputs/modeling/track_c/summary.md
```

## Test Cases

### 1. Monitoring helper and shared contract tests

1. Run:
   ```bash
   python -m pytest tests/test_track_c_baseline_model.py tests/test_track_c_common.py tests/test_m002_modeling_contract.py
   ```
2. **Expected:** all tests pass.

### 2. Drift-surface monotonicity and non-forecast framing

1. Run baseline command from Smoke Test.
2. Run:
   ```bash
   python - <<'PY'
   import pandas as pd
   from pathlib import Path

   surface = pd.read_parquet('outputs/modeling/track_c/drift_surface.parquet')
   assert not surface.empty
   assert surface['monitoring_change_score'].is_monotonic_decreasing

   summary = Path('outputs/modeling/track_c/summary.md').read_text(encoding='utf-8').lower()
   required = ['monitoring', 'drift', 'stability', 'ranked change surface', 'not a forecast']
   for phrase in required:
       assert phrase in summary, f'missing phrase: {phrase}'
   print('Track C monitoring surface and framing checks passed')
   PY
   ```
3. **Expected:** script exits 0.

## Edge Cases

### Invalid config path

1. Run:
   ```bash
   python -m src.modeling.track_c.baseline --config configs/does_not_exist.yaml
   ```
2. **Expected:** non-zero exit with explicit missing-config diagnostics.

## Failure Signals

- `monitoring_change_score` is unsorted or missing in `drift_surface.parquet`.
- Summary introduces forecast-style claims or drops monitoring-only phrases.
- Required `drift` keys are missing in `config_snapshot.json`.
- Invalid-config run succeeds or fails without actionable error.

## Requirements Proved By This UAT

- R007 — Confirms Track C drift/trend characterization baseline is executable and contract-stable.

## Not Proven By This UAT

- Forecasting performance (out of scope for R007).
- Cross-track milestone closure requirements (covered in S06).

## Notes for Tester

Treat any phrase-level summary regression as real drift: S06 integrated checks consume Track C framing language directly.