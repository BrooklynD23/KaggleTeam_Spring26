---
estimated_steps: 5
estimated_files: 7
skills_used:
  - coding-standards
  - backend-patterns
  - best-practices
  - verification-loop
---

# T01: Implement Track C monitoring baseline runtime and artifact bundle

**Slice:** S04 — Track C monitoring baseline
**Milestone:** M002-c1uww6

## Description

Create the first Track C modeling runtime entrypoint so monitoring evidence is reproducible from existing Stage 4/6/8 artifacts. This task converts drift/stability signals into a ranked city change surface and writes the full `outputs/modeling/track_c/` bundle required by the M002 contract.

## Steps

1. Create `src/modeling/track_c/baseline.py` with Track A/B-style structure: config loading, path resolution, required-input checks, helper functions, run function, and CLI `main()`.
2. Load Stage 4/6/8 Track C artifacts and assemble a city-level monitoring frame keyed by `city`/`normalized_city`/`state`, including sentiment drift fields, topic-drift rollups, and rolling-window stability features using `drift.rolling_window_months`.
3. Compute a deterministic `monitoring_change_score` (monitoring-only, no forecasting target), sort descending, and build the ranked `drift_surface.parquet` output.
4. Write `metrics.csv`, `config_snapshot.json`, `summary.md`, and `figures/monitoring_change_by_city.png` under `outputs/modeling/track_c/`, and enforce no banned raw-text columns in all persisted artifacts.
5. Update `src/modeling/track_c/__init__.py` exports if needed so the runtime entrypoint is discoverable and consistent with the modeling package layout.

## Must-Haves

- [ ] `src/modeling/track_c/baseline.py` is runnable via `python -m src.modeling.track_c.baseline --config configs/track_c.yaml`.
- [ ] `outputs/modeling/track_c/drift_surface.parquet` includes `monitoring_change_score` sorted descending.
- [ ] The artifact bundle includes `metrics.csv`, `config_snapshot.json`, `summary.md`, and `figures/monitoring_change_by_city.png`.
- [ ] Output artifacts contain no banned text columns and keep monitoring-only framing.

## Verification

- `python -m src.modeling.track_c.baseline --config configs/track_c.yaml`
- `test -f outputs/modeling/track_c/summary.md && test -f outputs/modeling/track_c/metrics.csv && test -f outputs/modeling/track_c/config_snapshot.json && test -f outputs/modeling/track_c/drift_surface.parquet && test -f outputs/modeling/track_c/figures/monitoring_change_by_city.png`

## Observability Impact

- Signals added/changed: `outputs/modeling/track_c/metrics.csv`, `outputs/modeling/track_c/drift_surface.parquet`, and `outputs/modeling/track_c/config_snapshot.json` expose run state and scoring outcomes.
- How a future agent inspects this: rerun `python -m src.modeling.track_c.baseline --config configs/track_c.yaml` and inspect artifacts under `outputs/modeling/track_c/`.
- Failure state exposed: missing Stage 4/6/8 tables or malformed columns fail with explicit input-check/runtime errors before artifact writing.

## Inputs

- `configs/track_c.yaml` — Track C monitoring thresholds (`slope_p_threshold`, `rolling_window_months`) and quality settings
- `outputs/tables/track_c_s4_sentiment_by_city_month.parquet` — monthly city sentiment stability source
- `outputs/tables/track_c_s6_sentiment_drift_by_city.parquet` — city-level sentiment drift source
- `outputs/tables/track_c_s6_topic_drift_by_city.parquet` — city-keyword topic drift source
- `outputs/tables/track_c_s8_checkin_sentiment_correlation.parquet` — optional correlation context for monitoring diagnostics
- `src/modeling/track_a/baseline.py` — Track A artifact-writing/runtime structure reference
- `src/modeling/track_b/baseline.py` — Track B grouped-metrics and summary/config contract reference

## Expected Output

- `src/modeling/track_c/baseline.py` — Track C monitoring baseline runtime entrypoint
- `src/modeling/track_c/__init__.py` — Track C modeling package export/update
- `outputs/modeling/track_c/metrics.csv` — machine-readable monitoring metrics
- `outputs/modeling/track_c/drift_surface.parquet` — ranked city change surface
- `outputs/modeling/track_c/config_snapshot.json` — resolved run configuration snapshot
- `outputs/modeling/track_c/summary.md` — monitoring-only baseline summary
- `outputs/modeling/track_c/figures/monitoring_change_by_city.png` — interpretable monitoring figure
