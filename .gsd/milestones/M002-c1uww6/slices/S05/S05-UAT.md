# S05: Track D baseline and optional D2 gate contract — UAT

**Milestone:** M002-c1uww6
**Written:** 2026-03-23

## UAT Type

- UAT mode: mixed
- Why this mode is sufficient: S05 acceptance depends on executable D1 baseline behavior, persisted comparator evidence, and explicit optional/non-blocking D2 semantics.

## Preconditions

- Stage 3, Stage 4, and Stage 7 artifacts required by `configs/track_d.yaml` are present.
- Python environment can run project modules and pytest.
- `outputs/modeling/track_d/` is writable.

## Smoke Test

Run:

```bash
python -m src.modeling.track_d.baseline --config configs/track_d.yaml
```

Then verify:

```bash
test -f outputs/modeling/track_d/metrics.csv
test -f outputs/modeling/track_d/scores_test.parquet
test -f outputs/modeling/track_d/config_snapshot.json
test -f outputs/modeling/track_d/summary.md
test -f outputs/modeling/track_d/d2_optional_report.csv
```

## Test Cases

### 1. Helper + cohort + contract regression tests

1. Run:
   ```bash
   python -m pytest tests/test_track_d_baseline_model.py tests/test_track_d_cohorts.py tests/test_m002_modeling_contract.py
   ```
2. **Expected:** all tests pass.

### 2. D1 comparator evidence and D2 optional semantics

1. Run baseline command from Smoke Test.
2. Run:
   ```bash
   python - <<'PY'
   import pandas as pd
   from pathlib import Path

   metrics = pd.read_csv('outputs/modeling/track_d/metrics.csv')
   assert {'d1_pointwise_baseline', 'd1_popularity_rank'} <= set(metrics['model_name']), 'missing Track D comparator rows'
   assert 'label_coverage_rate' in metrics.columns

   report = pd.read_csv('outputs/modeling/track_d/d2_optional_report.csv')
   assert 'is_required' in report.columns and not report['is_required'].astype(bool).any()

   summary = Path('outputs/modeling/track_d/summary.md').read_text(encoding='utf-8').lower()
   assert 'd1 required' in summary and 'd2 optional' in summary and 'non-blocking' in summary
   print('Track D comparator and D2 optional-gate checks passed')
   PY
   ```
3. **Expected:** script exits 0.

## Edge Cases

### Invalid configuration path

1. Run:
   ```bash
   python -m src.modeling.track_d.baseline --config configs/does_not_exist.yaml
   ```
2. **Expected:** non-zero exit with clear diagnostic message.

## Failure Signals

- `metrics.csv` missing either model/comparator rows or `label_coverage_rate`.
- `d2_optional_report.csv` indicates required semantics unexpectedly.
- Summary/config surfaces drop `D1 required` / `D2 optional` / `non-blocking` contract language.
- Invalid-config run does not produce clear failure diagnostics.

## Requirements Proved By This UAT

- R008 — Confirms Track D cold-start baseline executes and compares against explicit popularity baseline.

## Not Proven By This UAT

- D2 promoted to required status (intentionally not part of M002 acceptance).
- Milestone-wide integrated closure across all tracks (covered in S06).

## Notes for Tester

If tests fail on cohort joins, inspect upstream Stage 7 schema and key columns before modifying scoring logic.