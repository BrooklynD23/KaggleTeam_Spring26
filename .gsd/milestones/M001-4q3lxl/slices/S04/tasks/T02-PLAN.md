---
estimated_steps: 4
estimated_files: 6
skills_used:
  - coding-standards
  - test
  - verification-loop
  - review
---

# T02: Link the showcase lane to the new docs and lock them with pytest

**Slice:** S04 — Trust narrative and intern explainer workflow
**Milestone:** M001-4q3lxl

## Description

Wire the new S04 docs into the canonical showcase planning surface and add a dedicated pytest drift harness. This task makes the content discoverable from the existing feature/sprint/phase docs and turns `R004` into a mechanically verifiable contract rather than a narrative promise.

## Steps

1. Update `.gsd/feature-plans/showcase-system/FEATURE_PLAN.md`, the sprint doc, and the phase doc so each explicitly points to `TRUST_NARRATIVE.md` and `INTERN_EXPLAINER_WORKFLOW.md` as the S04-owned content contract while preserving the export-driven, local-hosted, no-live-parquet/DuckDB boundary.
2. Add `tests/test_trust_narrative_workflow.py` following the existing pytest contract-test style in `tests/test_feature_plan_architecture.py`.
3. In the new test file, assert file existence, required trust-function markers, export-boundary language, Track D blocker truth, Track E metadata-only validity language, intern-explainer triggers/inputs/outputs/guardrails, and cross-links from the feature/sprint/phase docs.
4. Run the dedicated pytest file and adjust the docs/tests until the suite passes cleanly with meaningful assertions rather than placeholder smoke checks.

## Must-Haves

- [ ] `FEATURE_PLAN.md`, `SPRINT.md`, and `PHASE-01-export-driven-experience-map.md` all point to the two new S04 docs and still preserve the S03 export-driven showcase guardrails.
- [ ] `tests/test_trust_narrative_workflow.py` checks more than file existence; it must cover content markers, cross-links, and governance language.
- [ ] The test explicitly protects Track D blocker visibility and Track E metadata-only validity language so the trust story cannot drift into false readiness.
- [ ] `python -m pytest tests/test_trust_narrative_workflow.py` passes at the end of the task.

## Verification

- `python -m pytest tests/test_trust_narrative_workflow.py`
- `python - <<'PY'
from pathlib import Path
link_targets = [
    '.gsd/feature-plans/showcase-system/FEATURE_PLAN.md',
    '.gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/SPRINT.md',
    '.gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/phases/PHASE-01-export-driven-experience-map.md',
]
markers = ['TRUST_NARRATIVE.md', 'INTERN_EXPLAINER_WORKFLOW.md']
for raw_path in link_targets:
    text = Path(raw_path).read_text(encoding='utf-8')
    for marker in markers:
        assert marker in text, (raw_path, marker)
print('showcase docs link to S04 narrative/workflow files')
PY`

## Inputs

- `.gsd/feature-plans/showcase-system/TRUST_NARRATIVE.md` — new S04 trust story doc from T01
- `.gsd/feature-plans/showcase-system/INTERN_EXPLAINER_WORKFLOW.md` — new S04 intern workflow doc from T01
- `.gsd/feature-plans/showcase-system/FEATURE_PLAN.md` — canonical showcase lane root doc to update
- `.gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/SPRINT.md` — showcase sprint doc to update
- `.gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/phases/PHASE-01-export-driven-experience-map.md` — showcase phase doc to update
- `tests/test_feature_plan_architecture.py` — existing pytest contract-test style reference

## Expected Output

- `.gsd/feature-plans/showcase-system/FEATURE_PLAN.md` — updated to link the S04 docs from the canonical showcase lane
- `.gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/SPRINT.md` — updated to cite the S04 docs in the sprint contract
- `.gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/phases/PHASE-01-export-driven-experience-map.md` — updated to cite the S04 docs in the phase handoff
- `tests/test_trust_narrative_workflow.py` — dedicated regression harness for S04 content and cross-links

## Observability Impact

- The machine-checkable inspection surface for this task is `tests/test_trust_narrative_workflow.py`, which now fails if the canonical showcase docs stop linking to the S04 docs or if export-boundary language drifts away from the local-hosted, no-live-parquet/DuckDB contract.
- Future agents should inspect `.gsd/feature-plans/showcase-system/FEATURE_PLAN.md`, `.../SPRINT.md`, and `.../PHASE-01-export-driven-experience-map.md` together with `outputs/exports/eda/manifest.json` and `outputs/exports/eda/tracks/track_e/manifest.json` to confirm cross-links, blocker truth, and metadata-only validity language still match the exported evidence.
- The visible failure state is intentional and specific: pytest points to the exact missing link or missing guardrail marker, while export diagnostics remain inspectable through `status_totals`, `blocked_by`, and `metadata_summaries`.
