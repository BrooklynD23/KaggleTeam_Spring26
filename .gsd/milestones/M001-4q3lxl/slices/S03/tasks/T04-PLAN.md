---
estimated_steps: 4
estimated_files: 7
skills_used:
  - article-writing
  - coding-standards
  - test
  - verification-loop
---

# T04: Author Track E and showcase-system execution plans

**Slice:** S03 — Agent-ready planning architecture
**Milestone:** M001-4q3lxl

## Description

Create the two cross-boundary plans that most directly feed S04. Track E must be planned as an accountability/audit lane on top of an upstream model, and the showcase-system plan must stay export-driven while reserving a clean place for the later trust narrative and intern-explainer workflow.

## Steps

1. Write the Track E feature plan under `.gsd/feature-plans/track-e-accountability/` using `src/eda/track_e/`, `outputs/exports/eda/tracks/track_e/manifest.json`, and `.gsd/milestones/M003-rdpeu4/M003-rdpeu4-CONTEXT-DRAFT.md` as the grounding surfaces.
2. Write the showcase-system feature plan under `.gsd/feature-plans/showcase-system/` using `outputs/exports/eda/manifest.json`, `outputs/exports/eda/EXPORT_CONTRACT.md`, and `.gsd/milestones/M004-fjc2zy/M004-fjc2zy-CONTEXT-DRAFT.md` as the primary inputs.
3. For each feature, add one sprint folder and one phase doc; in the showcase docs, cite `CoWork Planning/yelp_project/docs_agent/AGENTS.md` and `CoWork Planning/yelp_project/docs/intern/README.md` as boundary references without drafting the S04 narrative workflow itself.
4. Extend `tests/test_feature_plan_architecture.py` with Track E/showcase assertions and run the targeted test subset until it passes.

## Must-Haves

- [ ] Track E planning explicitly treats the work as an upstream-model fairness/audit lane, not a standalone predictor.
- [ ] Showcase planning explicitly treats `outputs/exports/eda/` as the website/report consumption boundary instead of querying parquet or DuckDB live.
- [ ] The showcase docs reserve S04-owned narrative/intern workflow surfaces by citing the prior-art docs without filling in the workflow content here.

## Verification

- `python -m pytest tests/test_feature_plan_architecture.py -k "track_e or showcase"`
- `python - <<'PY'
from pathlib import Path
track_e = Path('.gsd/feature-plans/track-e-accountability/FEATURE_PLAN.md').read_text(encoding='utf-8')
showcase = Path('.gsd/feature-plans/showcase-system/FEATURE_PLAN.md').read_text(encoding='utf-8')
assert 'M003-rdpeu4' in track_e
assert 'outputs/exports/eda/manifest.json' in showcase
assert 'CoWork Planning/yelp_project/docs_agent/AGENTS.md' in showcase
PY`

## Inputs

- `.gsd/feature-plans/README.md` — root contract created in T01
- `.gsd/milestones/M003-rdpeu4/M003-rdpeu4-CONTEXT-DRAFT.md` — Track E fairness/stronger-modeling draft
- `.gsd/milestones/M004-fjc2zy/M004-fjc2zy-CONTEXT-DRAFT.md` — showcase-system draft
- `outputs/exports/eda/manifest.json` — root export manifest the showcase must consume
- `outputs/exports/eda/EXPORT_CONTRACT.md` — export contract the showcase must respect
- `outputs/exports/eda/tracks/track_e/manifest.json` — current Track E evidence surface
- `src/eda/track_e/fairness_baseline.py` — representative Track E ownership seam and audit framing anchor
- `CoWork Planning/yelp_project/docs_agent/AGENTS.md` — prior-art boundary reference for the intern-explainer workflow
- `CoWork Planning/yelp_project/docs/intern/README.md` — prior-art intern navigation surface reserved for S04
- `tests/test_feature_plan_architecture.py` — shared regression file to extend

## Expected Output

- `.gsd/feature-plans/track-e-accountability/FEATURE_PLAN.md` — Track E execution plan
- `.gsd/feature-plans/track-e-accountability/sprints/SPRINT-01-audit-target-selection/SPRINT.md` — first Track E sprint doc
- `.gsd/feature-plans/track-e-accountability/sprints/SPRINT-01-audit-target-selection/phases/PHASE-01-upstream-model-gate.md` — first Track E phase doc
- `.gsd/feature-plans/showcase-system/FEATURE_PLAN.md` — showcase-system execution plan
- `.gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/SPRINT.md` — first showcase sprint doc
- `.gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/phases/PHASE-01-export-driven-experience-map.md` — first showcase phase doc
- `tests/test_feature_plan_architecture.py` — extended with Track E/showcase structure and content assertions

## Observability Impact

- `.gsd/feature-plans/track-e-accountability/FEATURE_PLAN.md` becomes the inspection surface for whether Track E is still framed as an upstream-model fairness/audit lane tied to M003 instead of drifting into standalone prediction language.
- `.gsd/feature-plans/showcase-system/FEATURE_PLAN.md` becomes the inspection surface for whether the future showcase is still export-driven off `outputs/exports/eda/` and still reserves S04-owned narrative and intern-workflow surfaces instead of drafting them early.
- `tests/test_feature_plan_architecture.py` gains targeted Track E/showcase assertions so failures identify whether drift happened in milestone cross-links, export-boundary language, or reserved prior-art references.
- The task-level verification snippet makes incomplete handoff state visible by checking for `M003-rdpeu4`, `outputs/exports/eda/manifest.json`, and `CoWork Planning/yelp_project/docs_agent/AGENTS.md` directly rather than relying on prose review alone.
