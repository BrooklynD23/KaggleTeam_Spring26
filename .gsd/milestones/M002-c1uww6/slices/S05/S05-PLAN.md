# S05: Track D1 cold-start baseline with optional D2 gate

**Goal:** Implement the first runnable Track D modeling baseline that produces D1 cold-start ranking evidence against an explicit as-of popularity comparator, while keeping any D2 work explicitly optional and non-blocking.
**Demo:** Running `python -m src.modeling.track_d.baseline --config configs/track_d.yaml` writes `metrics.csv`, `scores_test.parquet`, `config_snapshot.json`, `summary.md`, `figures/d1_recall_ndcg_by_cohort.png`, and `d2_optional_report.csv` under `outputs/modeling/track_d/`, with summary/config language explicitly marking D1 as required and D2 as optional.

## Must-Haves

- S05 directly advances **R008** by shipping a reproducible D1 cold-start baseline evaluated against a named as-of popularity comparator (`Recall@20`, `NDCG@10`).
- S05 supports **R009** by emitting clean, machine-readable Track D modeling artifacts under `outputs/modeling/track_d/` for downstream audit/report workflows.
- S05 supports **R012** by producing interpretable D1 comparator evidence and clear summary language that can be consumed in the trust-marketplace narrative.
- D1 and D2 remain separated in runtime logic and artifacts; D2 is always reported as optional/non-blocking in S05 outputs.
- Track D baseline outputs remain leakage-safe (no banned snapshot leakage fields and no raw review text in artifacts).

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `python -m pytest tests/test_track_d_baseline_model.py tests/test_track_d_cohorts.py tests/test_m002_modeling_contract.py`
- `python -m src.modeling.track_d.baseline --config configs/track_d.yaml && test -f outputs/modeling/track_d/metrics.csv && test -f outputs/modeling/track_d/scores_test.parquet && test -f outputs/modeling/track_d/config_snapshot.json && test -f outputs/modeling/track_d/summary.md && test -f outputs/modeling/track_d/figures/d1_recall_ndcg_by_cohort.png && test -f outputs/modeling/track_d/d2_optional_report.csv`
- `python - <<'PY'
import json
from pathlib import Path
import pandas as pd

metrics = pd.read_csv('outputs/modeling/track_d/metrics.csv')
required_cols = {'model_name','split_name','metric_name','metric_value','subtrack'}
assert required_cols.issubset(metrics.columns), metrics.columns

d1_metrics = metrics[metrics['subtrack'] == 'D1']
assert not d1_metrics.empty
assert {'d1_pointwise_baseline', 'asof_popularity_baseline'}.issubset(set(d1_metrics['model_name']))
assert {'recall_at_20', 'ndcg_at_10', 'label_coverage_rate'}.issubset(set(d1_metrics['metric_name']))

scores = pd.read_parquet('outputs/modeling/track_d/scores_test.parquet')
assert not scores.empty
assert {'candidate_set_id','candidate_business_id','is_label','d1_pointwise_baseline','asof_popularity_baseline'}.issubset(scores.columns)

summary = Path('outputs/modeling/track_d/summary.md').read_text(encoding='utf-8').lower()
for phrase in ['d1 required', 'as-of popularity comparator', 'd2 optional', 'non-blocking']:
    assert phrase in summary, phrase

snapshot = json.loads(Path('outputs/modeling/track_d/config_snapshot.json').read_text(encoding='utf-8'))
assert snapshot.get('track') == 'track_d'
assert snapshot.get('d2_gate', {}).get('status') in {'not_attempted', 'attempted', 'skipped'}
assert snapshot.get('d2_gate', {}).get('is_required') is False

print('track_d d1/comparator metrics and optional d2 gate semantics verified')
PY`
- `python - <<'PY'
import subprocess
import sys
cmd = [sys.executable, '-m', 'src.modeling.track_d.baseline', '--config', 'configs/does_not_exist.yaml']
proc = subprocess.run(cmd, capture_output=True, text=True)
assert proc.returncode != 0
combined = f"{proc.stdout}\n{proc.stderr}".lower()
assert 'does_not_exist.yaml' in combined or 'no such file' in combined
print('track_d baseline exposes inspectable failure diagnostics for invalid config path')
PY`

## Observability / Diagnostics

- Runtime signals: `outputs/modeling/track_d/metrics.csv`, `outputs/modeling/track_d/scores_test.parquet`, `outputs/modeling/track_d/config_snapshot.json`, `outputs/modeling/track_d/d2_optional_report.csv`, and `outputs/modeling/track_d/summary.md`.
- Inspection surfaces: `python -m src.modeling.track_d.baseline --config configs/track_d.yaml`, `tests/test_track_d_baseline_model.py`, and direct artifact inspection under `outputs/modeling/track_d/`.
- Failure visibility: missing Stage 3/4/7 inputs, malformed join keys, empty D1 train/eval slices, or comparator/metric schema drift surface via explicit runtime exceptions and pytest assertions.
- Redaction constraints: no raw review text in modeling artifacts; keep banned leakage fields excluded from D1 features and persisted outputs.

## Integration Closure

- Upstream surfaces consumed: `configs/track_d.yaml`, `outputs/tables/track_d_s3_business_early_signals.parquet`, `outputs/tables/track_d_s4_popularity_baseline_asof.parquet`, `outputs/tables/track_d_s7_eval_cohorts.parquet`, `outputs/tables/track_d_s7_eval_candidate_members.parquet`, and milestone contract guidance in `src/modeling/README.md`.
- New wiring introduced in this slice: `src/modeling/track_d/baseline.py` runtime entrypoint, Track D helper regression tests, and Track D artifact bundle under `outputs/modeling/track_d/` including explicit D2 optional-gate reporting.
- What remains before the milestone is truly usable end-to-end: S06 integrated cross-track verification and final handoff packaging across Tracks A/B/C/D1.

## Tasks

- [x] **T01: Implement Track D D1 baseline runtime and optional D2 gate artifacts** `est:1h 45m`
  - Why: S05 cannot satisfy R008 without a real `src/modeling/track_d` runtime that scores D1 candidates and evaluates against an explicit as-of popularity comparator.
  - Files: `src/modeling/track_d/baseline.py`, `src/modeling/track_d/__init__.py`, `outputs/modeling/track_d/metrics.csv`, `outputs/modeling/track_d/scores_test.parquet`, `outputs/modeling/track_d/config_snapshot.json`, `outputs/modeling/track_d/summary.md`, `outputs/modeling/track_d/d2_optional_report.csv`, `outputs/modeling/track_d/figures/d1_recall_ndcg_by_cohort.png`
  - Do: Build Track D baseline helpers for required-input checks, D1-only candidate assembly from Stage 3/4/7 as-of joins, deterministic pointwise scoring, explicit as-of popularity comparator scoring, grouped metric computation (`Recall@20`, `NDCG@10`, label coverage), artifact writing, and summary/config wording that marks D2 optional/non-blocking via a dedicated report surface.
  - Verify: `python -m src.modeling.track_d.baseline --config configs/track_d.yaml && test -f outputs/modeling/track_d/metrics.csv && test -f outputs/modeling/track_d/scores_test.parquet && test -f outputs/modeling/track_d/d2_optional_report.csv`
  - Done when: Track D runtime produces the full artifact bundle with explicit D1-vs-popularity comparator metrics and explicit D2 optional-gate status.
- [x] **T02: Add Track D baseline helper regression tests** `est:1h`
  - Why: S05 needs deterministic guardrails so future edits cannot silently break D1 assembly, comparator semantics, metric denominators, or D2 optional gating language.
  - Files: `tests/test_track_d_baseline_model.py`, `src/modeling/track_d/baseline.py`, `tests/test_track_d_cohorts.py`
  - Do: Add focused tests for D1 candidate joins and feature coverage checks, ranking metrics (`Recall@20`/`NDCG@10`) and comparator behavior, label-coverage metric semantics, and summary/config phrases enforcing “D1 required / D2 optional non-blocking.”
  - Verify: `python -m pytest tests/test_track_d_baseline_model.py`
  - Done when: helper-level regressions fail loudly if D1 comparator contract, denominator semantics, or optional-gate framing drifts.
- [x] **T03: Execute S05 verification and finalize Track D handoff semantics** `est:50m`
  - Why: S05 only closes if runtime and tests pass together and artifacts clearly separate required D1 evidence from optional D2 scope.
  - Files: `outputs/modeling/track_d/metrics.csv`, `outputs/modeling/track_d/scores_test.parquet`, `outputs/modeling/track_d/config_snapshot.json`, `outputs/modeling/track_d/summary.md`, `outputs/modeling/track_d/d2_optional_report.csv`, `outputs/modeling/track_d/figures/d1_recall_ndcg_by_cohort.png`
  - Do: Run full S05 verification suite (pytest + runtime + artifact assertions + invalid-config failure check), then tighten summary/config/report wording until comparator naming, metric interpretation, and D2 optional non-blocking status are explicit and stable.
  - Verify: `python -m pytest tests/test_track_d_baseline_model.py tests/test_track_d_cohorts.py tests/test_m002_modeling_contract.py && python -m src.modeling.track_d.baseline --config configs/track_d.yaml`
  - Done when: S05 verification passes end-to-end and the Track D bundle is ready for S06 integration without ambiguity about D1 required vs D2 optional scope.

## Files Likely Touched

- `src/modeling/track_d/baseline.py`
- `src/modeling/track_d/__init__.py`
- `tests/test_track_d_baseline_model.py`
- `tests/test_track_d_cohorts.py`
- `outputs/modeling/track_d/metrics.csv`
- `outputs/modeling/track_d/scores_test.parquet`
- `outputs/modeling/track_d/config_snapshot.json`
- `outputs/modeling/track_d/summary.md`
- `outputs/modeling/track_d/d2_optional_report.csv`
- `outputs/modeling/track_d/figures/d1_recall_ndcg_by_cohort.png`
