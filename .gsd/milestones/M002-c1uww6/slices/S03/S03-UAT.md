# S03: Track B baseline modeling contract — UAT

**Milestone:** M002-c1uww6
**Written:** 2026-03-23

## UAT Type

- UAT mode: mixed
- Why this mode is sufficient: S03 acceptance requires runtime generation plus grouped-ranking/comparator contract checks on persisted artifacts.

## Preconditions

- Track B input artifacts expected by `configs/track_b.yaml` are available.
- Python environment can run project modules and pytest.
- `outputs/modeling/track_b/` is writable.

## Smoke Test

Run:

```bash
python -m src.modeling.track_b.baseline --config configs/track_b.yaml
```

Then verify:

```bash
test -f outputs/modeling/track_b/metrics.csv
test -f outputs/modeling/track_b/config_snapshot.json
test -f outputs/modeling/track_b/summary.md
test -f outputs/modeling/track_b/scores_test.parquet
```

## Test Cases

### 1. Helper + shared modeling contract tests

1. Run:
   ```bash
   python -m pytest tests/test_track_b_baseline_model.py tests/test_label_scheme_ranking.py tests/test_feasibility_signoff.py tests/test_m002_modeling_contract.py
   ```
2. **Expected:** all tests pass.

### 2. Held-out comparator ordering and guardrail wording

1. Run baseline command from Smoke Test.
2. Run:
   ```bash
   python - <<'PY'
   import pandas as pd
   from pathlib import Path

   metrics = pd.read_csv('outputs/modeling/track_b/metrics.csv')
   all_test = metrics[(metrics['split_name'] == 'test') & (metrics['group_name'] == 'ALL')]
   score = dict(zip(all_test['model_name'], all_test['ndcg_at_10']))
   assert score['pointwise_percentile_regressor'] > score['text_length_only'] > score['review_stars_only']

   summary = Path('outputs/modeling/track_b/summary.md').read_text(encoding='utf-8').lower()
   assert 'snapshot' in summary and 'pointwise' in summary and 'group split strategy' in summary
   print('Track B comparator ordering and summary checks passed')
   PY
   ```
3. **Expected:** assertion script exits 0.

## Edge Cases

### Missing config diagnostics

1. Run:
   ```bash
   python -m src.modeling.track_b.baseline --config configs/does_not_exist.yaml
   ```
2. **Expected:** non-zero exit with clear missing-config path in stderr.

## Failure Signals

- `outputs/modeling/track_b/metrics.csv` no longer contains held-out `ALL` grouped rows.
- Comparator ordering fails (`pointwise_percentile_regressor` not top).
- Summary/config artifacts lose snapshot-only framing or banned-feature context.
- Invalid-config run does not fail clearly.

## Requirements Proved By This UAT

- R006 — Confirms executable Track B baseline and grouped ranking quality contract.

## Not Proven By This UAT

- Integrated cross-track handoff state (covered in S06).
- Track B model class upgrades beyond current pointwise baseline.

## Notes for Tester

Track B runtime can be the longest single baseline run in M002; allow completion before judging artifact absence as failure.