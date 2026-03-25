---
estimated_steps: 5
estimated_files: 8
skills_used:
  - coding-standards
  - backend-patterns
  - best-practices
  - verification-loop
---

# T01: Implement Track D D1 baseline runtime and optional D2 gate artifacts

**Slice:** S05 — Track D1 cold-start baseline with optional D2 gate
**Milestone:** M002-c1uww6

## Description

Create the first Track D modeling runtime entrypoint that turns Stage 3/4/7 artifacts into a reproducible D1 ranking baseline. The runtime must evaluate against an explicit as-of popularity comparator, emit the full `outputs/modeling/track_d/` artifact bundle, and report D2 as optional/non-blocking by contract.

## Steps

1. Create `src/modeling/track_d/baseline.py` with Track A/B/C-style structure: config loading, path resolution, required-input checks, helper functions, run function, and CLI `main()`.
2. Build D1 evaluation frame assembly by joining `outputs/tables/track_d_s7_eval_candidate_members.parquet` (`subtrack='D1'`) with Stage 3 business early signals and Stage 4 as-of popularity rows on `(candidate_business_id, as_of_date)`.
3. Fit one deterministic pointwise baseline scorer for D1 candidates, compute explicit comparator scores from as-of popularity signals, and evaluate both with `Recall@20`, `NDCG@10`, and `label_coverage_rate` by split/cohort.
4. Write `metrics.csv`, `scores_test.parquet`, `config_snapshot.json`, `summary.md`, and `figures/d1_recall_ndcg_by_cohort.png` under `outputs/modeling/track_d/`, keeping D1/D2 paths separated.
5. Write `outputs/modeling/track_d/d2_optional_report.csv` and snapshot/summary language that explicitly marks D2 as optional/non-blocking (attempted or not attempted) for S05.

## Must-Haves

- [ ] `python -m src.modeling.track_d.baseline --config configs/track_d.yaml` runs and writes the full Track D artifact bundle.
- [ ] `metrics.csv` includes both `d1_pointwise_baseline` and `asof_popularity_baseline` for D1 at `recall_at_20` and `ndcg_at_10`.
- [ ] `metrics.csv` includes explicit D1 `label_coverage_rate` so denominator semantics are inspectable.
- [ ] `d2_optional_report.csv`, `summary.md`, and `config_snapshot.json` explicitly state D2 optional/non-blocking status.

## Verification

- `python -m src.modeling.track_d.baseline --config configs/track_d.yaml`
- `test -f outputs/modeling/track_d/metrics.csv && test -f outputs/modeling/track_d/scores_test.parquet && test -f outputs/modeling/track_d/config_snapshot.json && test -f outputs/modeling/track_d/summary.md && test -f outputs/modeling/track_d/d2_optional_report.csv && test -f outputs/modeling/track_d/figures/d1_recall_ndcg_by_cohort.png`

## Observability Impact

- Signals added/changed: `outputs/modeling/track_d/metrics.csv`, `outputs/modeling/track_d/scores_test.parquet`, and `outputs/modeling/track_d/d2_optional_report.csv` provide direct runtime and contract diagnostics.
- How a future agent inspects this: rerun `python -m src.modeling.track_d.baseline --config configs/track_d.yaml` and inspect Track D artifacts under `outputs/modeling/track_d/`.
- Failure state exposed: missing Stage 3/4/7 inputs, empty D1 training/eval slices, or join/comparator drift fail with explicit runtime exceptions.

## Inputs

- `configs/track_d.yaml` — Track D thresholds, evaluation K values, leakage constraints, and candidate caps
- `outputs/tables/track_d_s3_business_early_signals.parquet` — D1 feature source keyed by business/as-of date
- `outputs/tables/track_d_s4_popularity_baseline_asof.parquet` — explicit as-of popularity comparator source
- `outputs/tables/track_d_s7_eval_cohorts.parquet` — candidate-set and label metadata
- `outputs/tables/track_d_s7_eval_candidate_members.parquet` — candidate member rows and label flags
- `src/modeling/track_a/baseline.py` — artifact-writing/runtime structure reference
- `src/modeling/track_b/baseline.py` — grouped ranking metrics/comparator reporting reference
- `src/modeling/README.md` — shared M002 modeling artifact contract

## Expected Output

- `src/modeling/track_d/baseline.py` — Track D modeling runtime entrypoint
- `src/modeling/track_d/__init__.py` — Track D modeling package export/update
- `outputs/modeling/track_d/metrics.csv` — D1 model vs comparator metrics including label coverage
- `outputs/modeling/track_d/scores_test.parquet` — held-out D1 candidate scores with label flags
- `outputs/modeling/track_d/config_snapshot.json` — resolved run settings and optional-gate status
- `outputs/modeling/track_d/summary.md` — D1-required / D2-optional summary contract
- `outputs/modeling/track_d/d2_optional_report.csv` — explicit optional D2 gate report
- `outputs/modeling/track_d/figures/d1_recall_ndcg_by_cohort.png` — interpretable D1 comparator figure
