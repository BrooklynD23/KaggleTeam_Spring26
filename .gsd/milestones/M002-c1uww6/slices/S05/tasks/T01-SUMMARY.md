---
id: T01
parent: S05
milestone: M002-c1uww6
provides:
  - Track D D1 baseline runtime with explicit as-of popularity comparator metrics and optional D2 gate artifacts
key_files:
  - src/modeling/track_d/baseline.py
  - src/modeling/track_d/__init__.py
  - tests/test_track_d_baseline_model.py
  - outputs/modeling/track_d/metrics.csv
  - outputs/modeling/track_d/config_snapshot.json
key_decisions:
  - D025 — Use a deterministic covariance-weighted D1 pointwise scorer with a 1,000,000-row train cap and explicit Stage 4 as-of popularity comparator
patterns_established:
  - Track D modeling joins Stage 7 D1 members+cohorts to Stage 3 signals and Stage 4 most_reviewed_in_city ranks on (candidate_business_id, as_of_date)
  - Grouped ranking outputs include label_coverage_rate alongside Recall@20/NDCG@10 so denominator semantics stay inspectable
observability_surfaces:
  - outputs/modeling/track_d/metrics.csv
  - outputs/modeling/track_d/scores_test.parquet
  - outputs/modeling/track_d/config_snapshot.json
  - outputs/modeling/track_d/d2_optional_report.csv
  - outputs/modeling/track_d/summary.md
  - python -m src.modeling.track_d.baseline --config configs/track_d.yaml
duration: 1h 18m
verification_result: passed
completed_at: 2026-03-23
blocker_discovered: false
---

# T01: Implement Track D D1 baseline runtime and optional D2 gate artifacts

**Implemented a runnable Track D D1 baseline runtime that scores Stage 7 candidates against an explicit as-of popularity comparator and emits the full S05 artifact bundle with D2 marked optional/non-blocking.**

## What Happened

I added `src/modeling/track_d/baseline.py` as the first Track D modeling entrypoint and wired it to load Stage 3/4/7 inputs, enforce required input checks, and fail with explicit diagnostics on missing/malformed inputs. The runtime builds a D1 modeling frame by joining Stage 7 candidate members/cohorts with Stage 3 early-signal features and Stage 4 `most_reviewed_in_city` popularity ranks on `(candidate_business_id, as_of_date)`, assigns deterministic train/test splits from as-of dates, fits a deterministic pointwise scorer, computes comparator scores, and evaluates both models with grouped `recall_at_20`, `ndcg_at_10`, and `label_coverage_rate` by split/cohort.

I also added full artifact writing under `outputs/modeling/track_d/`: `metrics.csv`, `scores_test.parquet`, `config_snapshot.json`, `summary.md`, `d2_optional_report.csv`, and `figures/d1_recall_ndcg_by_cohort.png`. Summary/config/report wording explicitly includes the D1-required and D2-optional/non-blocking contract. I updated `src/modeling/track_d/__init__.py` to keep package loading lightweight (avoids `runpy` warning on `python -m` execution), and created `tests/test_track_d_baseline_model.py` with helper-level regression coverage for split assignment, deterministic scoring, grouped metric semantics, required summary language, and D2 gate reporting.

## Verification

I ran the slice verification suite plus artifact-contract assertions and invalid-config diagnostics. All required checks pass in the worktree. Due the known auto-mode pytest rootdir quirk, I executed the pytest gate with absolute worktree test paths to avoid false file-not-found failures from mirror-root resolution.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest /mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.gsd/worktrees/M002-c1uww6/tests/test_track_d_baseline_model.py /mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.gsd/worktrees/M002-c1uww6/tests/test_track_d_cohorts.py /mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.gsd/worktrees/M002-c1uww6/tests/test_m002_modeling_contract.py` | 0 | ✅ pass | 1.83s |
| 2 | `python -m src.modeling.track_d.baseline --config configs/track_d.yaml && test -f outputs/modeling/track_d/metrics.csv && test -f outputs/modeling/track_d/scores_test.parquet && test -f outputs/modeling/track_d/config_snapshot.json && test -f outputs/modeling/track_d/summary.md && test -f outputs/modeling/track_d/figures/d1_recall_ndcg_by_cohort.png && test -f outputs/modeling/track_d/d2_optional_report.csv` | 0 | ✅ pass | 34.40s |
| 3 | `python - <<'PY' ... metrics/scores/summary/config snapshot contract assertions ... PY` | 0 | ✅ pass | 1.01s |
| 4 | `python - <<'PY' ... invalid config path failure diagnostics assertion ... PY` | 0 | ✅ pass | 0.68s |

## Diagnostics

Future inspection entrypoint: `python -m src.modeling.track_d.baseline --config configs/track_d.yaml`. Primary diagnostics are persisted in `outputs/modeling/track_d/metrics.csv`, `scores_test.parquet`, `config_snapshot.json`, `d2_optional_report.csv`, and `summary.md`. Failure states for missing Stage 3/4/7 artifacts, empty train data, join/schema drift, and invalid config path surface as explicit runtime exceptions/assertions.

## Deviations

- Used absolute worktree paths for the pytest verification command instead of relative `tests/...` paths because this auto-mode environment can resolve pytest rootdir to the `/mnt/c/...` mirror checkout and produce false `file or directory not found` failures for worktree-local tests.

## Known Issues

- None.

## Files Created/Modified

- `src/modeling/track_d/baseline.py` — added full Track D D1 baseline runtime (input checks, D1 assembly joins, deterministic scorer, comparator metrics, artifact writing, CLI).
- `src/modeling/track_d/__init__.py` — kept package export lightweight (`__all__ = ["baseline"]`) to avoid eager import/runpy warning on module execution.
- `tests/test_track_d_baseline_model.py` — added Track D baseline helper regression tests.
- `outputs/modeling/track_d/metrics.csv` — generated D1 model/comparator metrics including `label_coverage_rate`.
- `outputs/modeling/track_d/scores_test.parquet` — generated held-out D1 candidate scoring output.
- `outputs/modeling/track_d/config_snapshot.json` — generated reproducibility snapshot including D2 optional gate contract.
- `outputs/modeling/track_d/summary.md` — generated human-readable contract summary (`D1 required`, `D2 optional`, `non-blocking`).
- `outputs/modeling/track_d/d2_optional_report.csv` — generated explicit D2 optional gate report.
- `outputs/modeling/track_d/figures/d1_recall_ndcg_by_cohort.png` — generated cohort comparison figure.
