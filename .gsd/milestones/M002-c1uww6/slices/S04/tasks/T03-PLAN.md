---
estimated_steps: 5
estimated_files: 5
skills_used:
  - verification-loop
  - debug-like-expert
  - article-writing
---

# T03: Execute slice verification and lock Track C monitoring handoff surfaces

**Slice:** S04 — Track C monitoring baseline
**Milestone:** M002-c1uww6

## Description

Close S04 with integration-grade proof: run the complete test/runtime verification loop, validate artifact semantics, and finalize the Track C summary/config wording so downstream slices can consume the monitoring bundle without reinterpreting intent.

## Steps

1. Ensure required input surfaces are visible from this worktree (including `data/` and `outputs/tables/` paths) before running verification, using the known auto-mode worktree guidance when those ignored trees are absent.
2. Run `python -m pytest tests/test_track_c_baseline_model.py tests/test_track_c_common.py tests/test_m002_modeling_contract.py` and fix any contract drift found in Track C baseline artifacts.
3. Run `python -m src.modeling.track_c.baseline --config configs/track_c.yaml`, then execute artifact-content assertions for ranked-surface integrity (`monitoring_change_score` ordering), metrics schema, and summary/config phrase requirements.
4. Execute the invalid-config-path failure check and tighten summary language so it explicitly states monitoring evidence, drift/stability interpretation, ranked change surface semantics, and “not a forecast”.
5. Re-run the full S04 verification command set until all checks are green and the output bundle is stable.

## Must-Haves

- [ ] Full S04 verification commands pass without manual patching between runs.
- [ ] `summary.md` explicitly states monitoring-only framing and includes the required non-forecast statement.
- [ ] Invalid-config-path run fails loudly with inspectable diagnostics.

## Verification

- `python -m pytest tests/test_track_c_baseline_model.py tests/test_track_c_common.py tests/test_m002_modeling_contract.py`
- `python -m src.modeling.track_c.baseline --config configs/track_c.yaml && test -f outputs/modeling/track_c/summary.md && test -f outputs/modeling/track_c/metrics.csv && test -f outputs/modeling/track_c/config_snapshot.json && test -f outputs/modeling/track_c/drift_surface.parquet && test -f outputs/modeling/track_c/figures/monitoring_change_by_city.png`
- `python - <<'PY'
import json
from pathlib import Path
import pandas as pd

surface = pd.read_parquet('outputs/modeling/track_c/drift_surface.parquet')
assert surface['monitoring_change_score'].is_monotonic_decreasing

summary = Path('outputs/modeling/track_c/summary.md').read_text(encoding='utf-8').lower()
for phrase in ['monitoring', 'drift', 'stability', 'ranked change surface', 'not a forecast']:
    assert phrase in summary, phrase

config = json.loads(Path('outputs/modeling/track_c/config_snapshot.json').read_text(encoding='utf-8'))
assert 'drift' in config and 'rolling_window_months' in config['drift']
print('track_c summary/config/drift surface semantics verified')
PY`

## Observability Impact

- Signals added/changed: verified outputs in `outputs/modeling/track_c/` become the canonical inspection surface for S04 runtime health.
- How a future agent inspects this: run the S04 verification command set and inspect `summary.md`, `metrics.csv`, and `drift_surface.parquet` directly.
- Failure state exposed: failed required-input checks, missing artifacts, malformed drift surface ordering, or weak summary phrasing surface via explicit assertion/test failures.

## Inputs

- `tests/test_track_c_baseline_model.py` — Track C helper contract tests from T02
- `tests/test_track_c_common.py` — Track C no-raw-text guardrail regression
- `tests/test_m002_modeling_contract.py` — milestone-level modeling scaffold contract check
- `configs/track_c.yaml` — runtime config and monitoring thresholds
- `outputs/modeling/track_c/summary.md` — summary phrasing and handoff surface to finalize
- `outputs/modeling/track_c/metrics.csv` — machine-readable metrics output to validate
- `outputs/modeling/track_c/drift_surface.parquet` — ranked change surface to validate
- `outputs/modeling/track_c/config_snapshot.json` — configuration contract surface to validate

## Expected Output

- `outputs/modeling/track_c/summary.md` — finalized monitoring-only Track C handoff summary
- `outputs/modeling/track_c/metrics.csv` — validated metrics artifact
- `outputs/modeling/track_c/drift_surface.parquet` — validated ranked change surface artifact
- `outputs/modeling/track_c/config_snapshot.json` — validated config snapshot artifact
- `outputs/modeling/track_c/figures/monitoring_change_by_city.png` — validated interpretable figure artifact
