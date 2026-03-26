---
estimated_steps: 4
estimated_files: 7
skills_used:
  - article-writing
  - coding-standards
  - test
  - verification-loop
---

# T02: Author Track A and Track B execution plans

**Slice:** S03 — Agent-ready planning architecture
**Milestone:** M001-4q3lxl

## Description

Create the first two real feature-plan lanes for downstream implementation agents. These docs must turn the current EDA/export state plus the M002 modeling draft into concrete execution surfaces for prediction and surfacing work, while preserving Track A's temporal rules and Track B's snapshot-only framing.

## Steps

1. Write the Track A feature plan under `.gsd/feature-plans/track-a-prediction/` with a repo-grounded crosswalk to `src/eda/track_a/`, `outputs/exports/eda/tracks/track_a/manifest.json`, `outputs/tables/eda_command_checklist.md`, and `.gsd/milestones/M002-c1uww6/M002-c1uww6-CONTEXT-DRAFT.md`.
2. Write the Track B feature plan under `.gsd/feature-plans/track-b-surfacing/` with the same structure, but keep the framing explicitly snapshot-only and age-controlled rather than temporal vote-growth analysis.
3. For each feature, add one concrete sprint folder and one phase doc that name current evidence inputs, future target folders (clearly labeled as future), commands, verification, and exit criteria for a first implementation agent.
4. Extend `tests/test_feature_plan_architecture.py` with Track A/Track B assertions and run the targeted test subset until it passes.

## Must-Haves

- [ ] Track A planning explicitly preserves as-of/temporal leakage guardrails and points future modeling work back to `review_fact.parquet`-based evidence rather than snapshot-only shortcuts.
- [ ] Track B planning explicitly preserves snapshot-only usefulness ranking rules and avoids implying vote-growth or temporal trend inference.
- [ ] Both feature plans include a top-level `FEATURE_PLAN.md`, one `SPRINT.md`, and one phase doc with concrete repo paths, commands, verification, and clearly labeled future target folders where code does not yet exist.

## Verification

- `python -m pytest tests/test_feature_plan_architecture.py -k "track_a or track_b"`
- `python - <<'PY'
from pathlib import Path
for path in [
    Path('.gsd/feature-plans/track-a-prediction/FEATURE_PLAN.md'),
    Path('.gsd/feature-plans/track-b-surfacing/FEATURE_PLAN.md'),
]:
    text = path.read_text(encoding='utf-8')
    assert 'outputs/exports/eda/' in text
    assert 'M002-c1uww6' in text
PY`

## Inputs

- `.gsd/feature-plans/README.md` — root contract created in T01
- `.gsd/milestones/M002-c1uww6/M002-c1uww6-CONTEXT-DRAFT.md` — baseline-modeling draft for Tracks A and B
- `outputs/exports/eda/tracks/track_a/manifest.json` — current Track A evidence surface
- `outputs/exports/eda/tracks/track_b/manifest.json` — current Track B evidence surface
- `outputs/tables/eda_command_checklist.md` — canonical launcher order and dependency wording
- `src/eda/track_a/summary_report.py` — representative Track A ownership seam and current summary contract
- `src/eda/track_b/summary_report.py` — representative Track B ownership seam and current summary contract
- `tests/test_feature_plan_architecture.py` — shared regression file to extend

## Expected Output

- `.gsd/feature-plans/track-a-prediction/FEATURE_PLAN.md` — Track A execution plan
- `.gsd/feature-plans/track-a-prediction/sprints/SPRINT-01-baseline-modeling/SPRINT.md` — first Track A sprint doc
- `.gsd/feature-plans/track-a-prediction/sprints/SPRINT-01-baseline-modeling/phases/PHASE-01-temporal-baseline-contract.md` — first Track A phase doc
- `.gsd/feature-plans/track-b-surfacing/FEATURE_PLAN.md` — Track B execution plan
- `.gsd/feature-plans/track-b-surfacing/sprints/SPRINT-01-snapshot-ranking-baseline/SPRINT.md` — first Track B sprint doc
- `.gsd/feature-plans/track-b-surfacing/sprints/SPRINT-01-snapshot-ranking-baseline/phases/PHASE-01-snapshot-baseline-contract.md` — first Track B phase doc
- `tests/test_feature_plan_architecture.py` — extended with Track A/Track B structure and content assertions

## Observability Impact

- `.gsd/feature-plans/track-a-prediction/FEATURE_PLAN.md` and `.gsd/feature-plans/track-b-surfacing/FEATURE_PLAN.md` become the first per-feature inspection surfaces under the root README contract, so future agents can confirm each lane's repo seams, evidence inputs, milestone crosswalk, and future-target labeling without rereading milestone drafts.
- The paired sprint and phase docs make incomplete work visible at a finer grain: if a first implementation agent lacks commands, verification, or exit criteria, the missing section is discoverable directly in the feature folder instead of surfacing later as execution ambiguity.
- `tests/test_feature_plan_architecture.py` now needs to distinguish root-contract drift from Track A/Track B content drift, so failures should reveal whether the breakage is missing files, missing cross-links to `outputs/exports/eda/`, or lost framing constraints such as Track A temporal leakage language or Track B snapshot-only wording.
