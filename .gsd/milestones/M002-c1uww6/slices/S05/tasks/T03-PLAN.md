---
estimated_steps: 5
estimated_files: 6
skills_used:
  - verification-loop
  - debug-like-expert
  - article-writing
---

# T03: Execute S05 verification and finalize Track D handoff semantics

**Slice:** S05 — Track D1 cold-start baseline with optional D2 gate
**Milestone:** M002-c1uww6

## Description

Close S05 with integration-grade proof: run the full test/runtime verification loop, validate artifact schemas and comparator semantics, and lock wording so downstream slices can consume Track D outputs without ambiguity about required D1 vs optional D2 scope.

## Steps

1. Ensure required Track D input surfaces are available in this worktree, especially Stage 3/4/7 artifacts used by the D1 baseline runtime.
2. Run `python -m pytest tests/test_track_d_baseline_model.py tests/test_track_d_cohorts.py tests/test_m002_modeling_contract.py` and fix any contract drift.
3. Run `python -m src.modeling.track_d.baseline --config configs/track_d.yaml`, then execute artifact assertions for metrics schema, comparator presence, score-table columns, and D2 optional-gate status fields.
4. Execute the invalid-config-path failure check and tighten summary/config/report language so D1-required / D2-optional non-blocking semantics are explicit.
5. Re-run the full S05 verification command set until all checks are green and artifacts are stable across reruns.

## Must-Haves

- [ ] Full S05 verification commands pass without manual patching between runs.
- [ ] `summary.md`, `config_snapshot.json`, and `d2_optional_report.csv` all state D2 optional/non-blocking status.
- [ ] Invalid-config-path run fails loudly with inspectable diagnostics.

## Verification

- `python -m pytest tests/test_track_d_baseline_model.py tests/test_track_d_cohorts.py tests/test_m002_modeling_contract.py`
- `python -m src.modeling.track_d.baseline --config configs/track_d.yaml && test -f outputs/modeling/track_d/metrics.csv && test -f outputs/modeling/track_d/scores_test.parquet && test -f outputs/modeling/track_d/config_snapshot.json && test -f outputs/modeling/track_d/summary.md && test -f outputs/modeling/track_d/d2_optional_report.csv && test -f outputs/modeling/track_d/figures/d1_recall_ndcg_by_cohort.png`
- `python - <<'PY'
import json
from pathlib import Path
import pandas as pd

metrics = pd.read_csv('outputs/modeling/track_d/metrics.csv')
assert {'model_name','split_name','metric_name','metric_value','subtrack'}.issubset(metrics.columns)

summary = Path('outputs/modeling/track_d/summary.md').read_text(encoding='utf-8').lower()
for phrase in ['d1 required', 'd2 optional', 'non-blocking']:
    assert phrase in summary, phrase

snapshot = json.loads(Path('outputs/modeling/track_d/config_snapshot.json').read_text(encoding='utf-8'))
assert snapshot.get('d2_gate', {}).get('is_required') is False
assert snapshot.get('d2_gate', {}).get('status') in {'not_attempted', 'attempted', 'skipped'}

report = pd.read_csv('outputs/modeling/track_d/d2_optional_report.csv')
assert {'status','is_required'}.issubset(report.columns)
assert set(report['is_required'].astype(bool)) == {False}
print('track_d optional-gate semantics verified')
PY`

## Observability Impact

- Signals added/changed: final verified `metrics.csv`, `scores_test.parquet`, `config_snapshot.json`, and `d2_optional_report.csv` become S05’s canonical inspection surfaces.
- How a future agent inspects this: rerun S05 verification commands and inspect artifact schemas/content under `outputs/modeling/track_d/`.
- Failure state exposed: missing artifacts, comparator schema drift, or weak D2 gating language surfaces via direct pytest or inline assertion failures.

## Inputs

- `tests/test_track_d_baseline_model.py` — Track D helper/runtime contract tests from T02
- `tests/test_track_d_cohorts.py` — Track D as-of cohort semantics regression suite
- `tests/test_m002_modeling_contract.py` — milestone-level modeling scaffold contract check
- `configs/track_d.yaml` — runtime config for D1 baseline execution
- `outputs/modeling/track_d/summary.md` — summary wording and handoff surface to finalize
- `outputs/modeling/track_d/config_snapshot.json` — optional-gate and run-config contract surface
- `outputs/modeling/track_d/d2_optional_report.csv` — explicit D2 optional report surface

## Expected Output

- `outputs/modeling/track_d/metrics.csv` — validated D1/comparator metrics artifact
- `outputs/modeling/track_d/scores_test.parquet` — validated held-out score artifact
- `outputs/modeling/track_d/config_snapshot.json` — finalized D2 optional-gate contract snapshot
- `outputs/modeling/track_d/summary.md` — finalized D1-required / D2-optional summary
- `outputs/modeling/track_d/d2_optional_report.csv` — finalized optional D2 status report
- `outputs/modeling/track_d/figures/d1_recall_ndcg_by_cohort.png` — validated interpretable figure
