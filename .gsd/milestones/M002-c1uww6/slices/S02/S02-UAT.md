# S02: Track A baseline modeling contract — UAT

**Milestone:** M002-c1uww6
**Written:** 2026-03-23

## UAT Type

- UAT mode: mixed
- Why this mode is sufficient: S02 acceptance depends on both executable baseline runtime behavior and artifact-level contract wording/comparator evidence.

## Preconditions

- Worktree has access to `data/curated/review_fact.parquet` and required Stage 3/5 artifacts used by Track A baseline joins.
- Python environment can run project modules and pytest.
- No stale manual edits in `outputs/modeling/track_a/` that should be replaced by a fresh baseline run.

## Smoke Test

Run:

```bash
python -m src.modeling.track_a.baseline --config configs/track_a.yaml --train-cap 100000 --eval-cap 200000
```

Then confirm files exist:

```bash
test -f outputs/modeling/track_a/metrics.csv
test -f outputs/modeling/track_a/config_snapshot.json
test -f outputs/modeling/track_a/summary.md
```

## Test Cases

### 1. Helper and contract regression surface

1. Run:
   ```bash
   python -m pytest tests/test_track_a_baseline_model.py tests/test_m002_modeling_contract.py
   ```
2. **Expected:** pytest passes with no failures, confirming helper-level feature/metric behavior and shared modeling contract checks.

### 2. Comparator quality and handoff narrative check

1. Run baseline command from Smoke Test.
2. Run:
   ```bash
   python - <<'PY'
   import pandas as pd
   from pathlib import Path

   metrics = pd.read_csv('outputs/modeling/track_a/metrics.csv')
   model_mae = metrics.loc[(metrics.model_name == 'hist_gradient_boosting') & (metrics.split_name == 'test'), 'mae'].iloc[0]
   naive_mean_mae = metrics.loc[(metrics.model_name == 'naive_mean') & (metrics.split_name == 'test'), 'mae'].iloc[0]
   assert model_mae < naive_mean_mae, 'Track A model must beat naive_mean on test MAE'

   summary = Path('outputs/modeling/track_a/summary.md').read_text(encoding='utf-8')
   assert 'Known limitations' in summary
   assert 'M003 audit suitability' in summary
   assert 'Track A remains the preferred default' in summary
   print('Track A comparator and handoff summary checks passed')
   PY
   ```
3. **Expected:** assertion script prints success and exits 0.

## Edge Cases

### Invalid configuration path

1. Run:
   ```bash
   python -m src.modeling.track_a.baseline --config configs/does_not_exist.yaml
   ```
2. **Expected:** command fails non-zero with an inspectable missing-config error.

## Failure Signals

- `hist_gradient_boosting` test MAE no longer beats `naive_mean` in `outputs/modeling/track_a/metrics.csv`.
- `outputs/modeling/track_a/summary.md` no longer contains required handoff headings/phrases.
- Required files are missing after runtime execution.
- Invalid-config command exits 0 or fails without actionable path diagnostics.

## Requirements Proved By This UAT

- R005 — Confirms Track A baseline runtime and comparator evidence are executable and reproducible.

## Not Proven By This UAT

- Cross-track integrated handoff consistency (covered in S06 gate).
- Fairness/disparity outcomes for Track A (deferred to R009 work).

## Notes for Tester

If this UAT fails after upstream artifact refreshes, check Stage 3/5 input availability and schema before editing baseline code.