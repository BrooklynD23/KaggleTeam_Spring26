---
estimated_steps: 4
estimated_files: 7
skills_used:
  - article-writing
  - coding-standards
  - test
  - verification-loop
---

# T03: Author Track C and Track D execution plans

**Slice:** S03 — Agent-ready planning architecture
**Milestone:** M001-4q3lxl

## Description

Plan the monitoring and onboarding lanes without losing the repo's hardest-earned constraints. Track C must stay framed as drift/monitoring work instead of heavyweight forecasting, and Track D must visibly inherit its dependency on Track A Stage 5 rather than pretending candidate splits already exist.

## Steps

1. Write the Track C feature plan under `.gsd/feature-plans/track-c-monitoring/` using `src/eda/track_c/`, `outputs/exports/eda/tracks/track_c/manifest.json`, and `.gsd/milestones/M002-c1uww6/M002-c1uww6-CONTEXT-DRAFT.md` as the grounding surfaces.
2. Write the Track D feature plan under `.gsd/feature-plans/track-d-onboarding/` using `src/eda/track_d/`, `outputs/exports/eda/tracks/track_d/manifest.json`, `outputs/tables/eda_command_checklist.md`, and `outputs/tables/track_a_s5_candidate_splits.parquet` as the blocker reference.
3. For each feature, add one sprint folder and one phase doc with current evidence inputs, future target folders clearly marked as future, concrete commands, verification, and exit criteria that a fresh agent can execute.
4. Extend `tests/test_feature_plan_architecture.py` with Track C/Track D assertions and run the targeted test subset until it passes.

## Must-Haves

- [ ] Track C planning explicitly keeps the lane in drift/monitoring framing and does not describe the work as generic forecasting.
- [ ] Track D planning explicitly names `outputs/tables/track_a_s5_candidate_splits.parquet` as a dependency/blocker and does not claim that artifact is already materialized.
- [ ] Both feature plans include a top-level `FEATURE_PLAN.md`, one `SPRINT.md`, and one phase doc with concrete repo paths, commands, verification, and clearly labeled future target folders.

## Verification

- `python -m pytest tests/test_feature_plan_architecture.py -k "track_c or track_d"`
- `python - <<'PY'
from pathlib import Path
track_c = Path('.gsd/feature-plans/track-c-monitoring/FEATURE_PLAN.md').read_text(encoding='utf-8')
track_d = Path('.gsd/feature-plans/track-d-onboarding/FEATURE_PLAN.md').read_text(encoding='utf-8')
assert 'drift' in track_c.lower()
assert 'track_a_s5_candidate_splits.parquet' in track_d
PY`

## Inputs

- `.gsd/feature-plans/README.md` — root contract created in T01
- `.gsd/milestones/M002-c1uww6/M002-c1uww6-CONTEXT-DRAFT.md` — baseline-modeling draft for Tracks C and D
- `outputs/exports/eda/tracks/track_c/manifest.json` — current Track C evidence surface
- `outputs/exports/eda/tracks/track_d/manifest.json` — current Track D evidence surface
- `outputs/tables/eda_command_checklist.md` — canonical launcher order and Track D dependency wording
- `outputs/tables/track_a_s5_candidate_splits.parquet` — blocker artifact Track D must treat as dependency, not assumption
- `src/eda/track_c/drift_detection.py` — representative Track C ownership seam and drift framing anchor
- `src/eda/track_d/popularity_baseline.py` — representative Track D ownership seam and cold-start baseline anchor
- `tests/test_feature_plan_architecture.py` — shared regression file to extend

## Expected Output

- `.gsd/feature-plans/track-c-monitoring/FEATURE_PLAN.md` — Track C execution plan
- `.gsd/feature-plans/track-c-monitoring/sprints/SPRINT-01-drift-baseline/SPRINT.md` — first Track C sprint doc
- `.gsd/feature-plans/track-c-monitoring/sprints/SPRINT-01-drift-baseline/phases/PHASE-01-drift-signal-baseline.md` — first Track C phase doc
- `.gsd/feature-plans/track-d-onboarding/FEATURE_PLAN.md` — Track D execution plan
- `.gsd/feature-plans/track-d-onboarding/sprints/SPRINT-01-cold-start-baseline/SPRINT.md` — first Track D sprint doc
- `.gsd/feature-plans/track-d-onboarding/sprints/SPRINT-01-cold-start-baseline/phases/PHASE-01-candidate-split-gate.md` — first Track D phase doc
- `tests/test_feature_plan_architecture.py` — extended with Track C/Track D structure and content assertions

## Observability Impact

- `.gsd/feature-plans/track-c-monitoring/FEATURE_PLAN.md` becomes the first human-readable inspection surface for whether Track C is still framed as drift/monitoring work, which evidence exports exist now, and which future modeling folders remain explicitly future.
- `.gsd/feature-plans/track-d-onboarding/FEATURE_PLAN.md` becomes the corresponding dependency surface for Track D; future agents should be able to confirm from this file and `outputs/exports/eda/tracks/track_d/manifest.json` that `outputs/tables/track_a_s5_candidate_splits.parquet` is a blocker dependency rather than an assumed artifact.
- `tests/test_feature_plan_architecture.py` gains mechanical checks for Track C/Track D structure and framing, so failures reveal whether drift language disappeared, the Track D blocker reference was dropped, or the required sprint/phase surfaces went missing.
- The existing per-slug inventory verification command becomes more informative after this task because it will show Track C and Track D as populated while unfinished later slugs remain visibly empty.
