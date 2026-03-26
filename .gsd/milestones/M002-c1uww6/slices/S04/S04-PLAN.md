# S04: Track C monitoring baseline

**Goal:** Implement the first runnable Track C modeling baseline that converts existing Stage 4/6/8 Track C EDA artifacts into measurable monitoring evidence (drift/stability metrics + ranked city change surface) under the shared `outputs/modeling/track_c/` contract.
**Demo:** Running `python -m src.modeling.track_c.baseline --config configs/track_c.yaml` writes `metrics.csv`, `drift_surface.parquet`, `config_snapshot.json`, `summary.md`, and `figures/monitoring_change_by_city.png` under `outputs/modeling/track_c/`, and the summary explicitly frames outputs as monitoring evidence rather than forecasting.

## Must-Haves

- S04 directly advances **R007** by adding a reproducible Track C monitoring runtime that emits machine-readable drift/stability evidence.
- S04 supports **R012** by producing an interpretable ranked change surface and figure that can slot into the trust-marketplace narrative without forecasting creep.
- Track C modeling outputs stay inside the shared artifact contract at `outputs/modeling/track_c/` with required metrics, ranked surface, config snapshot, and summary.
- The Track C summary and tests enforce monitoring-only language and preserve no-raw-review-text output constraints.

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `python -m pytest tests/test_track_c_baseline_model.py tests/test_track_c_common.py tests/test_m002_modeling_contract.py`
- `python -m src.modeling.track_c.baseline --config configs/track_c.yaml && test -f outputs/modeling/track_c/summary.md && test -f outputs/modeling/track_c/metrics.csv && test -f outputs/modeling/track_c/config_snapshot.json && test -f outputs/modeling/track_c/drift_surface.parquet && test -f outputs/modeling/track_c/figures/monitoring_change_by_city.png`
- `python - <<'PY'
import json
from pathlib import Path
import pandas as pd

surface = pd.read_parquet('outputs/modeling/track_c/drift_surface.parquet')
assert not surface.empty
assert 'monitoring_change_score' in surface.columns
assert surface['monitoring_change_score'].notna().all()
assert surface['monitoring_change_score'].is_monotonic_decreasing
assert not any(col.lower() in {'text', 'review_text', 'raw_text'} for col in surface.columns)

metrics = pd.read_csv('outputs/modeling/track_c/metrics.csv')
assert {'metric_name', 'metric_value'}.issubset(metrics.columns)
assert (metrics['metric_name'] == 'city_count').any()

summary = Path('outputs/modeling/track_c/summary.md').read_text(encoding='utf-8').lower()
for phrase in ['monitoring', 'drift', 'stability', 'ranked change surface', 'not a forecast']:
    assert phrase in summary, phrase

config = json.loads(Path('outputs/modeling/track_c/config_snapshot.json').read_text(encoding='utf-8'))
assert 'drift' in config
assert 'slope_p_threshold' in config['drift']
assert 'rolling_window_months' in config['drift']
print('track_c monitoring artifacts and non-forecast framing verified')
PY`
- `python - <<'PY'
import subprocess
import sys
cmd = [sys.executable, '-m', 'src.modeling.track_c.baseline', '--config', 'configs/does_not_exist.yaml']
proc = subprocess.run(cmd, capture_output=True, text=True)
assert proc.returncode != 0
combined = f"{proc.stdout}\n{proc.stderr}".lower()
assert 'does_not_exist.yaml' in combined or 'no such file' in combined
print('track_c baseline exposes inspectable failure diagnostics for invalid config path')
PY`

## Observability / Diagnostics

- Runtime signals: `outputs/modeling/track_c/metrics.csv`, `outputs/modeling/track_c/drift_surface.parquet`, `outputs/modeling/track_c/config_snapshot.json`, `outputs/modeling/track_c/summary.md`, and `outputs/modeling/track_c/figures/monitoring_change_by_city.png`
- Inspection surfaces: `python -m src.modeling.track_c.baseline --config configs/track_c.yaml`, `tests/test_track_c_baseline_model.py`, and direct artifact inspection under `outputs/modeling/track_c/`
- Failure visibility: missing Stage 4/6/8 inputs, invalid config path, malformed drift columns, or forbidden text-column leakage surface via explicit exceptions and pytest assertions
- Redaction constraints: no raw review text columns in any Track C modeling artifact; summary must remain aggregate-safe and monitoring-only

## Integration Closure

- Upstream surfaces consumed: `configs/track_c.yaml`, `outputs/tables/track_c_s4_sentiment_by_city_month.parquet`, `outputs/tables/track_c_s6_sentiment_drift_by_city.parquet`, `outputs/tables/track_c_s6_topic_drift_by_city.parquet`, `outputs/tables/track_c_s8_checkin_sentiment_correlation.parquet`
- New wiring introduced in this slice: `src/modeling/track_c/baseline.py` runtime entrypoint, Track C helper regression tests, and Track C modeling artifact bundle under `outputs/modeling/track_c/`
- What remains before the milestone is truly usable end-to-end: Track D1 baseline execution and integrated cross-track handoff verification in S05–S06

## Tasks

- [x] **T01: Implement Track C monitoring baseline runtime and artifact bundle** `est:1h 30m`
  - Why: S04 cannot prove R007 monitoring coverage without a real `src/modeling/track_c` runtime that transforms Stage 4/6/8 artifacts into reproducible modeling outputs.
  - Files: `src/modeling/track_c/baseline.py`, `src/modeling/track_c/__init__.py`, `outputs/modeling/track_c/metrics.csv`, `outputs/modeling/track_c/drift_surface.parquet`, `outputs/modeling/track_c/config_snapshot.json`, `outputs/modeling/track_c/summary.md`, `outputs/modeling/track_c/figures/monitoring_change_by_city.png`
  - Do: Build Track C baseline helpers for required-input checks, Stage 4/6/8 loading, city-level feature assembly, monitoring score computation, ranked-surface generation, config snapshot writing, summary generation, and figure export; keep all logic monitoring-only and config-driven (`drift.slope_p_threshold`, `drift.rolling_window_months`) with no forecasting target.
  - Verify: `python -m src.modeling.track_c.baseline --config configs/track_c.yaml && test -f outputs/modeling/track_c/metrics.csv && test -f outputs/modeling/track_c/drift_surface.parquet && test -f outputs/modeling/track_c/summary.md`
  - Done when: Track C baseline runs successfully and writes the full artifact bundle under `outputs/modeling/track_c/` with ranked city monitoring scores and no banned text columns.
- [x] **T02: Add Track C baseline helper regression tests** `est:1h`
  - Why: S04 needs deterministic guardrails so future edits cannot silently break score composition, ranking order, or monitoring-only summary language.
  - Files: `tests/test_track_c_baseline_model.py`, `src/modeling/track_c/baseline.py`
  - Do: Add focused pytest coverage for core helpers (topic rollups, stability-window calculations, monitoring score composition, deterministic descending ranking, and summary phrase requirements), following Track A/B test style.
  - Verify: `python -m pytest tests/test_track_c_baseline_model.py`
  - Done when: helper-level regressions fail loudly if Track C scoring, ranking determinism, or required summary wording drifts.
- [x] **T03: Execute slice verification and lock Track C monitoring handoff surfaces** `est:45m`
  - Why: S04 only closes if runtime + tests + output contract all pass together and the bundle is clearly consumable by S06 without interpretation drift.
  - Files: `outputs/modeling/track_c/metrics.csv`, `outputs/modeling/track_c/drift_surface.parquet`, `outputs/modeling/track_c/config_snapshot.json`, `outputs/modeling/track_c/summary.md`, `outputs/modeling/track_c/figures/monitoring_change_by_city.png`
  - Do: Run the full S04 verification suite (pytest, runtime command, artifact-content assertions, and invalid-config failure-path check), then tighten summary/config wording as needed so monitoring framing, drift/stability evidence, ranked change surface semantics, and non-forecast language are explicit.
  - Verify: `python -m pytest tests/test_track_c_baseline_model.py tests/test_track_c_common.py tests/test_m002_modeling_contract.py && python -m src.modeling.track_c.baseline --config configs/track_c.yaml`
  - Done when: S04 verification passes end-to-end and the Track C modeling bundle communicates monitoring evidence clearly enough for downstream milestone integration.

## Files Likely Touched

- `src/modeling/track_c/baseline.py`
- `src/modeling/track_c/__init__.py`
- `tests/test_track_c_baseline_model.py`
- `outputs/modeling/track_c/metrics.csv`
- `outputs/modeling/track_c/drift_surface.parquet`
- `outputs/modeling/track_c/config_snapshot.json`
- `outputs/modeling/track_c/summary.md`
- `outputs/modeling/track_c/figures/monitoring_change_by_city.png`
