---
estimated_steps: 4
estimated_files: 2
skills_used:
  - article-writing
  - coding-standards
  - test
  - verification-loop
---

# T01: Lock the feature-plan root contract and verification harness

**Slice:** S03 — Agent-ready planning architecture
**Milestone:** M001-4q3lxl

## Description

Define the planning architecture before feature-specific docs proliferate. This task establishes the canonical `.gsd/feature-plans/` root, the seven approved feature slugs, the document naming convention, and the first regression checks so later tasks can extend one stable execution surface instead of inventing parallel structures.

## Steps

1. Create `.gsd/feature-plans/README.md` with the canonical feature-plan slugs, required file layout (`FEATURE_PLAN.md`, `sprints/SPRINT-*/SPRINT.md`, `phases/PHASE-*.md`), and the rule that plans must cross-link to real repo paths, current export surfaces, and milestone drafts.
2. State the planning boundaries in the root README: do not imply `src/modeling/` or a web app already exist, do not introduce raw review text, and reserve S04-owned narrative/intern workflow content instead of writing it here.
3. Add `tests/test_feature_plan_architecture.py` with root-level assertions for the index file, slug inventory, and naming convention; keep the first passing scope focused on the root contract.
4. Run targeted pytest and fix the README/test wording until the root contract is mechanically stable.

## Must-Haves

- [ ] `.gsd/feature-plans/README.md` names all seven canonical feature slugs and explains how downstream plans should cite milestone drafts and `outputs/exports/eda/`.
- [ ] The root README makes the S03/S04 boundary explicit by reserving, not completing, the trust-narrative and intern-explainer surfaces.
- [ ] `tests/test_feature_plan_architecture.py` contains passing root-level assertions that later tasks can extend without changing the architecture convention.

## Verification

- `python -m pytest tests/test_feature_plan_architecture.py -k "root_index"`
- `python - <<'PY'
from pathlib import Path
readme = Path('.gsd/feature-plans/README.md').read_text(encoding='utf-8')
for slug in [
    'track-a-prediction',
    'track-b-surfacing',
    'track-c-monitoring',
    'track-d-onboarding',
    'track-e-accountability',
    'showcase-system',
    'multimodal-experiments',
]:
    assert slug in readme, slug
PY`

## Inputs

- `.gsd/REQUIREMENTS.md` — confirms S03 owns `R003` and only supports the S04 boundary
- `.gsd/milestones/M002-c1uww6/M002-c1uww6-CONTEXT-DRAFT.md` — representative future milestone draft the root index must point feature plans toward
- `outputs/exports/eda/manifest.json` — current machine-readable evidence surface every future plan should treat as the handoff boundary
- `outputs/exports/eda/EXPORT_CONTRACT.md` — export contract the root index should name as the downstream consumption surface

## Expected Output

- `.gsd/feature-plans/README.md` — canonical root index and architecture contract for long-lived feature planning
- `tests/test_feature_plan_architecture.py` — root-level regression coverage for the planning architecture

## Observability Impact

- The new `.gsd/feature-plans/README.md` becomes the first inspectable planning status surface for downstream agents: if a future task drifts on slugs, layout, evidence inputs, or milestone cross-links, the mismatch is visible in one file before feature docs proliferate.
- `tests/test_feature_plan_architecture.py` turns the root contract into a regression harness with explicit failure messages for missing README content, missing canonical slugs, or naming-convention drift.
- During T01 verification, future agents can inspect both the targeted pytest output and direct README substring checks to separate "contract missing" from "feature folders not authored yet" without rereading the whole slice plan.
