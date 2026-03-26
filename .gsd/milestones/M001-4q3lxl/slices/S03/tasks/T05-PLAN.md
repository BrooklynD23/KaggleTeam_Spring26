---
estimated_steps: 4
estimated_files: 5
skills_used:
  - article-writing
  - coding-standards
  - test
  - verification-loop
---

# T05: Add the multimodal lane and close full architecture verification

**Slice:** S03 — Agent-ready planning architecture
**Milestone:** M001-4q3lxl

## Description

Close the architecture with the only intentionally optional lane. This task makes multimodal exploration explicit but non-critical-path, updates the root index to reflect the full plan set, and turns the shared pytest file into a full slice-proof that all seven feature plans exist and carry the critical references discovered in S01/S02 and the future milestone drafts.

## Steps

1. Write the multimodal feature plan under `.gsd/feature-plans/multimodal-experiments/` using `.gsd/milestones/M005-i0a235/M005-i0a235-CONTEXT-DRAFT.md` as the future-work source and keep the first sprint framed as a scope gate with an expand-or-stop decision.
2. Update `.gsd/feature-plans/README.md` so the final index and dependency map show how the seven plans connect from evidence packaging to modeling, audit, showcase, and optional multimodal exploration.
3. Expand `tests/test_feature_plan_architecture.py` to assert all seven feature folders/files exist, each `FEATURE_PLAN.md` references at least one concrete repo path plus an evidence or milestone input, and the critical special cases (Track D blocker, showcase export contract, multimodal M005 scope gate) are present.
4. Run the full pytest file and fix any structural or content drift until the suite passes.

## Must-Haves

- [ ] The multimodal plan is explicitly non-critical-path and uses a scope-gate / expand-or-stop structure instead of promising immediate implementation.
- [ ] The root README reflects the final seven-plan architecture and cross-feature dependencies.
- [ ] The shared pytest file proves the full architecture mechanically, not just by file count.

## Verification

- `python -m pytest tests/test_feature_plan_architecture.py`
- `python - <<'PY'
from pathlib import Path
multimodal = Path('.gsd/feature-plans/multimodal-experiments/FEATURE_PLAN.md').read_text(encoding='utf-8')
root = Path('.gsd/feature-plans/README.md').read_text(encoding='utf-8')
assert 'M005-i0a235' in multimodal
assert 'expand-or-stop' in multimodal.lower()
for slug in [
    'track-a-prediction',
    'track-b-surfacing',
    'track-c-monitoring',
    'track-d-onboarding',
    'track-e-accountability',
    'showcase-system',
    'multimodal-experiments',
]:
    assert slug in root, slug
PY`

## Inputs

- `.gsd/feature-plans/README.md` — root contract and index to finalize
- `.gsd/milestones/M005-i0a235/M005-i0a235-CONTEXT-DRAFT.md` — multimodal future-work draft
- `outputs/exports/eda/manifest.json` — evidence handoff surface the multimodal plan should treat as upstream context, not replace
- `tests/test_feature_plan_architecture.py` — shared regression file to expand into full slice-proof
- `.gsd/feature-plans/showcase-system/FEATURE_PLAN.md` — adjacent cross-feature plan the multimodal lane should remain downstream of

## Expected Output

- `.gsd/feature-plans/multimodal-experiments/FEATURE_PLAN.md` — multimodal execution plan
- `.gsd/feature-plans/multimodal-experiments/sprints/SPRINT-01-scope-gate/SPRINT.md` — first multimodal sprint doc
- `.gsd/feature-plans/multimodal-experiments/sprints/SPRINT-01-scope-gate/phases/PHASE-01-expand-or-stop-decision.md` — first multimodal phase doc
- `.gsd/feature-plans/README.md` — finalized root index and dependency map
- `tests/test_feature_plan_architecture.py` — full architecture regression coverage for all seven feature plans

## Observability Impact

- `.gsd/feature-plans/README.md` becomes the final human-readable architecture map; future agents should inspect it first to confirm the seven canonical lanes, the cross-feature dependency order, and the rule that multimodal work remains optional and downstream of core evidence/modeling surfaces.
- `.gsd/feature-plans/multimodal-experiments/FEATURE_PLAN.md` plus its sprint/phase docs become the inspectable status surface for whether the M005 lane is still only a scope gate or has earned expansion; failure should be visible as missing `expand-or-stop`, missing M005 cross-links, or language that incorrectly claims multimodal execution is already on the critical path.
- `tests/test_feature_plan_architecture.py` becomes the full slice drift harness; failures should pinpoint whether breakage is in the canonical inventory, missing file surfaces, absent repo/evidence/milestone references, or special-case contract regressions like the Track D blocker, showcase export boundary, or multimodal scope gate.
