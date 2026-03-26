---
estimated_steps: 4
estimated_files: 8
skills_used:
  - article-writing
  - coding-standards
  - verification-loop
---

# T01: Author export-grounded trust narrative and explainer docs

**Slice:** S04 — Trust narrative and intern explainer workflow
**Milestone:** M001-4q3lxl

## Description

Create the two dedicated S04-owned showcase docs that turn the export bundle and prior-art intern guidance into a concrete content contract. The trust narrative must map the five trust functions to Tracks A-E using current `outputs/exports/eda/` truth, and the explainer workflow must formalize when an explainer-style agent should be invoked, what it must read first, what it must output, and which governance/tone guardrails it cannot violate.

## Steps

1. Read the current showcase lane contract and export evidence surfaces from `outputs/exports/eda/manifest.json`, `outputs/exports/eda/EXPORT_CONTRACT.md`, per-track exported summaries, and the Track D / Track E manifests so the new docs reflect current repo truth rather than milestone aspiration.
2. Author `.gsd/feature-plans/showcase-system/TRUST_NARRATIVE.md` with the spine prediction → surfacing → monitoring → onboarding → accountability, mapping those functions to `track_a` through `track_e`, carrying forward `existing=6`, `missing=109`, the Track D blocker, and Track E metadata-only validity evidence.
3. Author `.gsd/feature-plans/showcase-system/INTERN_EXPLAINER_WORKFLOW.md` using `CoWork Planning/yelp_project/docs_agent/AGENTS.md` and `CoWork Planning/yelp_project/docs/intern/README.md` as prior-art inputs, with explicit sections for when to invoke, required inputs, expected outputs, explanation order, and guardrails.
4. Self-check both docs for aggregate-safe/internal language, no raw review text, concrete repo paths, and discoverable wording that later M004 agents can cite directly without re-research.

## Must-Haves

- [ ] `TRUST_NARRATIVE.md` explicitly maps Track A/B/C/D/E to prediction, surfacing, monitoring, onboarding, and accountability using exported evidence paths.
- [ ] `TRUST_NARRATIVE.md` keeps current-state honesty visible, including `existing=6`, `missing=109`, `outputs/tables/track_a_s5_candidate_splits.parquet`, and Track E metadata-only validity evidence.
- [ ] `INTERN_EXPLAINER_WORKFLOW.md` states when to invoke the explainer, what files it must read first, what outputs it should produce, and how it must explain concepts in plain language.
- [ ] Both docs preserve the internal aggregate-safe boundary and forbid raw review text or new live-data surfaces.

## Verification

- `python - <<'PY'
from pathlib import Path
checks = {
    '.gsd/feature-plans/showcase-system/TRUST_NARRATIVE.md': ['prediction', 'surfacing', 'monitoring', 'onboarding', 'accountability', 'outputs/exports/eda/manifest.json', 'outputs/exports/eda/EXPORT_CONTRACT.md', 'aggregate-safe', 'internal', 'track_a', 'track_b', 'track_c', 'track_d', 'track_e', 'existing=6', 'missing=109', 'outputs/tables/track_a_s5_candidate_splits.parquet', 'metadata-only'],
    '.gsd/feature-plans/showcase-system/INTERN_EXPLAINER_WORKFLOW.md': ['When to invoke', 'Inputs', 'Outputs', 'Guardrails', 'glossary', 'plain language', 'raw review text', 'CoWork Planning/yelp_project/docs_agent/AGENTS.md', 'CoWork Planning/yelp_project/docs/intern/README.md'],
}
for raw_path, markers in checks.items():
    text = Path(raw_path).read_text(encoding='utf-8')
    for marker in markers:
        assert marker in text, (raw_path, marker)
print('S04 docs contain required markers')
PY`
- `python - <<'PY'
from pathlib import Path
for path in [
    Path('.gsd/feature-plans/showcase-system/TRUST_NARRATIVE.md'),
    Path('.gsd/feature-plans/showcase-system/INTERN_EXPLAINER_WORKFLOW.md'),
]:
    assert path.exists() and path.stat().st_size > 0, path
print('S04 docs exist and are non-empty')
PY`

## Inputs

- `.gsd/feature-plans/showcase-system/FEATURE_PLAN.md` — current showcase lane boundary and reserved S04 seam
- `outputs/exports/eda/manifest.json` — root export truth for scope, safety boundary, counts, and track pointers
- `outputs/exports/eda/EXPORT_CONTRACT.md` — governance contract the docs must inherit
- `outputs/exports/eda/tracks/track_a/summary.md` — prediction lane evidence
- `outputs/exports/eda/tracks/track_b/summary.md` — surfacing lane evidence
- `outputs/exports/eda/tracks/track_c/summary.md` — monitoring lane evidence
- `outputs/exports/eda/tracks/track_d/summary.md` — onboarding lane evidence with blocker language
- `outputs/exports/eda/tracks/track_d/manifest.json` — machine-readable Track D blocker truth
- `outputs/exports/eda/tracks/track_e/summary.md` — accountability lane evidence
- `outputs/exports/eda/tracks/track_e/manifest.json` — metadata-only validity evidence
- `CoWork Planning/yelp_project/docs_agent/AGENTS.md` — prior-art explainer tone and concept rules
- `CoWork Planning/yelp_project/docs/intern/README.md` — prior-art reading order and navigation model

## Expected Output

- `.gsd/feature-plans/showcase-system/TRUST_NARRATIVE.md` — dedicated trust-marketplace story doc grounded in current export evidence
- `.gsd/feature-plans/showcase-system/INTERN_EXPLAINER_WORKFLOW.md` — dedicated intern-explainer invocation and guardrail workflow doc

## Observability Impact

- Future agents gain two inspectable documentation surfaces under `.gsd/feature-plans/showcase-system/` that point back to `outputs/exports/eda/manifest.json`, `outputs/exports/eda/EXPORT_CONTRACT.md`, and the per-track summaries/manifests instead of restating unsupported claims.
- Failure state becomes visible through explicit blocker and status references in the docs: `existing=6`, `missing=109`, Track D `blocked_by`, and Track E validity evidence staying metadata-only.
- The explainer workflow adds a repeatable reading order and output contract that later agents can audit by checking for the required inputs, glossary-first explanation order, and raw-review-text prohibition.
- Redaction and governance signals remain inspectable because both docs must preserve `internal` + `aggregate-safe` language and forbid new live-data or raw-text surfaces.
