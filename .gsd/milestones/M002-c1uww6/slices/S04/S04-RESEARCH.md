# S04 — Research

**Date:** 2026-03-23

## Summary

S04 is a **targeted research** slice. The Track C EDA stack already produced the exact upstream monitoring surfaces we need: monthly city sentiment (`track_c_s4_sentiment_by_city_month.parquet`), city-level sentiment drift (`track_c_s6_sentiment_drift_by_city.parquet`), city-keyword topic drift (`track_c_s6_topic_drift_by_city.parquet`), and optional check-in correlation context (`track_c_s8_checkin_sentiment_correlation.parquet`). The modeling scaffold is also already in place under `src/modeling/track_c/` and `outputs/modeling/track_c/`.

Current gap: **no Track C modeling runtime exists yet** (`src/modeling/track_c/` only has `__init__.py`). S04 therefore needs to implement the first monitoring baseline entrypoint and artifact bundle under `outputs/modeling/track_c/` (metrics + ranked change surface + config snapshot + summary + interpretable figure). Existing EDA tables prove data readiness, but per `debug-like-expert` core rule (“verify, don’t assume”), they are not baseline-model proof by themselves.

Requirement targeting for this slice: primary coverage is **R007 (monitoring layer)** with support for **R012** (trust-marketplace narrative coherence). Slice acceptance from roadmap also demands explicit non-forecasting framing.

## Recommendation

Implement `src/modeling/track_c/baseline.py` as a **monitoring-only scoring pipeline** that consumes Stage 4/6/8 Track C artifacts and emits a city-level ranked change surface. Keep this lane intentionally non-predictive: no forward forecasting, no temporal extrapolation, no model-zoo scope.

Follow existing Track A/B modeling patterns for structure and artifacts (path resolution, required-input checks, config snapshot, summary contract, figure output). Apply `coding-standards` KISS/YAGNI guidance: one clear monitoring score built from observable drift/stability signals is enough for M002. Apply `test`/`tdd-workflow` guidance by locking helper behavior with focused pytest coverage before relying on full-run outputs.

## Implementation Landscape

### Key Files

- `src/modeling/track_c/__init__.py` — currently empty package marker; baseline entrypoint does not exist yet.
- `src/modeling/track_a/baseline.py` — best template for artifact-writing contract, summary structure, config snapshot pattern, and CLI entrypoint style.
- `src/modeling/track_b/baseline.py` — best template for ranked-metric outputs and “comparator + summary phrasing checks” pattern.
- `src/modeling/README.md` — canonical M002 contract; Track C must emit metrics artifact + drift/stability/ranked surface + config snapshot + summary under `outputs/modeling/track_c/`.
- `configs/track_c.yaml` — source of monitoring knobs already present (`drift.slope_p_threshold`, `drift.rolling_window_months`, quality thresholds).
- `src/eda/track_c/drift_detection.py` — authoritative semantics for Stage 6 drift columns (`slope`, `p_value`, `r_squared`, `is_significant`) and significance threshold handling.
- `src/eda/track_c/common.py` — reusable path utilities and no-raw-text contract (`BANNED_TEXT_COLUMNS`, parquet leak-safety helper behavior).
- `outputs/tables/track_c_s4_sentiment_by_city_month.parquet` — city-month stability source (19,078 rows, 378 cities).
- `outputs/tables/track_c_s6_sentiment_drift_by_city.parquet` — city drift source (378 rows, 21 significant at current threshold).
- `outputs/tables/track_c_s6_topic_drift_by_city.parquet` — city-keyword drift source (2,297 rows, 63 significant).
- `outputs/tables/track_c_s8_checkin_sentiment_correlation.parquet` — optional monitoring context for paired coverage/correlation diagnostics.
- `tests/test_track_a_baseline_model.py` and `tests/test_track_b_baseline_model.py` — style references for helper-first regression tests in modeling slices.
- `tests/test_track_c_common.py` — Track C-specific guardrail pattern around raw-text leakage checks.

### Build Order

1. **Create Track C baseline runtime skeleton first**
   - Add `src/modeling/track_c/baseline.py` with `run_baseline()` + CLI `main()`.
   - Implement required-input checks for Stage 4/6 (and Stage 8 if used).
   - This unblocks all downstream work by giving the slice a canonical executable surface.

2. **Assemble monitoring features from existing EDA outputs**
   - Build city-level table keyed by `city/state/normalized_city` with:
     - sentiment drift fields from Stage 6,
     - topic drift rollups (e.g., `sig_topic_keyword_count`, `max_topic_abs_slope`),
     - stability features from Stage 4 (volatility + rolling-window shift using config window).
   - Keep every metric descriptive/diagnostic; no forward prediction target.

3. **Define ranked change surface + metrics artifact**
   - Compute one explicit `monitoring_change_score` for ranking cities.
   - Write ranked city surface parquet (e.g., `drift_surface.parquet`).
   - Write compact `metrics.csv` with portfolio-level monitoring stats (counts/significance/stability aggregates).

4. **Write summary + config snapshot + figure**
   - Artifacts under `outputs/modeling/track_c/`:
     - `metrics.csv`
     - `drift_surface.parquet` (or equivalent ranked surface name)
     - `config_snapshot.json`
     - `summary.md`
     - `figures/<track_c_monitoring_figure>.png`
   - Summary must explicitly state “monitoring evidence, not forecasting claim.”

5. **Add Track C helper regression tests, then run integration verification**
   - Add `tests/test_track_c_baseline_model.py` for pure helper logic (score composition, rollups, ranking determinism, summary phrase checks).
   - Run pytest + real entrypoint command, then assert artifact presence/content.

## Constraints

- Monitoring-only framing is mandatory: no forecasting language or predictive target creation.
- No raw review text may be exported to modeling artifacts (reuse Track C no-text contract posture).
- Respect existing config-driven thresholds (`slope_p_threshold`, `rolling_window_months`) rather than hardcoding.
- Keep outputs in `outputs/modeling/track_c/` only (per shared modeling contract).

## Common Pitfalls

- Treating existing EDA drift tables as “baseline complete” without a reproducible Track C modeling entrypoint.
- Producing prose-only summary without machine-readable ranked surface artifact.
- Accidentally reframing as forecasting (e.g., “next-month sentiment prediction”) instead of monitoring.
- Ranking cities by raw slope without accounting for stability/coverage context (high-noise cities can dominate).

## Verification Approach

- Helper regression tests (new):
  - `python -m pytest tests/test_track_c_baseline_model.py`
- Existing guardrail regression:
  - `python -m pytest tests/test_track_c_common.py tests/test_m002_modeling_contract.py`
- Runtime integration:
  - `python -m src.modeling.track_c.baseline --config configs/track_c.yaml`
- Post-run artifact assertions:
  - check for `metrics.csv`, `drift_surface.parquet`, `config_snapshot.json`, `summary.md`, and figure under `outputs/modeling/track_c/`
  - assert summary contains explicit non-forecasting language and references drift/stability/ranked surface

## Skills Discovered

Core technologies without currently installed project-local specialized skills were checked via `npx skills find`:

- DuckDB candidate: `npx skills add silvainfm/claude-skills@duckdb` (highest installs in query output)
- Pandas candidate: `npx skills add jeffallan/claude-skills@pandas-pro`
- scikit-learn candidate: `npx skills add davila7/claude-code-templates@scikit-learn`
- Matplotlib candidate: `npx skills add davila7/claude-code-templates@matplotlib`

No installation performed in this slice.
