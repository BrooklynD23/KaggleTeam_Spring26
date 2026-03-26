---
id: S05
parent: M002-c1uww6
milestone: M002-c1uww6
provides:
  - Track D D1 cold-start baseline runtime with as-of popularity comparator metrics and explicit D2 optional/non-blocking gate artifacts.
requires:
  - slice: M001-4q3lxl/S01
    provides: Stage 3/4/7 artifacts needed to build D1 candidate/member/cohort modeling frame.
affects:
  - S06
  - M003-rdpeu4
key_files:
  - src/modeling/track_d/baseline.py
  - tests/test_track_d_baseline_model.py
  - outputs/modeling/track_d/metrics.csv
  - outputs/modeling/track_d/scores_test.parquet
  - outputs/modeling/track_d/config_snapshot.json
  - outputs/modeling/track_d/d2_optional_report.csv
  - outputs/modeling/track_d/summary.md
key_decisions:
  - D025: Use deterministic covariance-weighted D1 pointwise scoring with explicit as-of popularity comparator and a 1,000,000-row train cap for baseline tractability.
patterns_established:
  - Track D helper tests must lock strict D1 filtering/join keys and label-coverage denominator semantics so cohort metrics stay interpretable under sparse labels.
observability_surfaces:
  - python -m src.modeling.track_d.baseline --config configs/track_d.yaml
  - python -m pytest tests/test_track_d_baseline_model.py tests/test_track_d_cohorts.py tests/test_m002_modeling_contract.py
  - outputs/modeling/track_d/metrics.csv
  - outputs/modeling/track_d/scores_test.parquet
  - outputs/modeling/track_d/config_snapshot.json
  - outputs/modeling/track_d/d2_optional_report.csv
  - outputs/modeling/track_d/summary.md
drill_down_paths:
  - .gsd/milestones/M002-c1uww6/slices/S05/tasks/T01-SUMMARY.md
  - .gsd/milestones/M002-c1uww6/slices/S05/tasks/T02-SUMMARY.md
  - .gsd/milestones/M002-c1uww6/slices/S05/tasks/T03-SUMMARY.md
duration: 2h 49m
verification_result: passed
completed_at: 2026-03-23
---

# S05: Track D baseline and optional D2 gate contract

**Shipped the Track D D1 cold-start baseline with explicit popularity comparator evidence and codified D2 as optional/non-blocking in both runtime artifacts and tests.**

## What Happened

S05 implemented `src/modeling/track_d/baseline.py` as the first Track D modeling entrypoint. The runtime validates required Stage 3/4/7 inputs, builds D1 modeling joins on `(candidate_business_id, as_of_date)`, trains deterministic pointwise scores, evaluates against as-of popularity comparator baselines, and writes full artifacts under `outputs/modeling/track_d/`.

The slice expanded helper-level tests to cover strict D1 subtrack filtering, comparator fallback behavior when popularity rank is absent, and grouped metric denominator semantics via `label_coverage_rate`. Slice close reran full verification plus an explicit stability rerun to prove the contract does not pass only once by chance.

Concrete verification artifacts for this slice are:
- `python -m src.modeling.track_d.baseline --config configs/track_d.yaml`
- `python -m pytest tests/test_track_d_baseline_model.py tests/test_track_d_cohorts.py tests/test_m002_modeling_contract.py`
- `outputs/modeling/track_d/metrics.csv` with model + comparator rows and label-coverage diagnostics.

## Verification

All T01–T03 verification passed, including runtime artifact generation, helper/integration pytest gates, contract assertions over metrics/scores/config/summary wording, invalid-config failure diagnostics, and a second stability rerun bundle.

## Requirements Advanced

- R008 — Delivered and validated the Track D cold-start baseline with explicit as-of popularity comparator evaluation.
- R012 — Added durable onboarding-handoff diagnostics and artifact semantics (`D1 required`, `D2 optional/non-blocking`).

## Requirements Validated

- R008 — Slice-level evidence demonstrates repeatable runtime success and comparator-backed evaluation persisted in Track D artifact bundle.

## New Requirements Surfaced

- none.

## Requirements Invalidated or Re-scoped

- none.

## Deviations

Used absolute worktree pytest paths in one verification pass to avoid known mirror-root resolution false negatives in this harness.

## Known Limitations

Current Track D delivery is centered on D1; D2 remains optional and explicitly non-blocking for M002 closure.

## Follow-ups

- If D2 moves toward required scope in M003+, convert optional-report semantics and tests in a dedicated contract change.
- Keep `label_coverage_rate` in grouped metrics to prevent silent denominator drift under sparse labels.

## Files Created/Modified

- `src/modeling/track_d/baseline.py` — D1 baseline runtime, comparator evaluation, artifact writing, and optional D2 gate reporting.
- `tests/test_track_d_baseline_model.py` — helper coverage for D1 filtering, comparator fallback, and denominator semantics.
- `outputs/modeling/track_d/metrics.csv` — model/comparator grouped metrics including `label_coverage_rate`.
- `outputs/modeling/track_d/d2_optional_report.csv` — explicit optional gate status evidence.
- `outputs/modeling/track_d/summary.md` — handoff narrative for D1-required and D2-optional semantics.

## Forward Intelligence

### What the next slice should know
- Integrated handoff checks treat D2 as optional but expect explicit optional/non-blocking wording in summary and config surfaces.

### What's fragile
- Join-key assumptions (`candidate_business_id`, `as_of_date`) in Stage 3/4/7 assembly; upstream schema drift will break Track D quickly.

### Authoritative diagnostics
- `outputs/modeling/track_d/metrics.csv` and `d2_optional_report.csv` — they expose comparator health and optional-gate truth without reading code.

### What assumptions changed
- “D2 must ship now to close baseline milestone” — slice evidence validated that D1 + explicit optional D2 contract is sufficient for M002.
