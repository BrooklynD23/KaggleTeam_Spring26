# S04 — Research

**Date:** 2026-03-21

## Summary

S04 directly owns **R004** and is the slice that turns the already-reserved showcase planning boundary into actual repo planning content: a trust-marketplace narrative tied to real exported evidence, plus a repeatable intern-explainer workflow. The important constraint is that S04 should **not** invent new story surfaces or drift into website implementation. S03 already established the stable landing zone under `.gsd/feature-plans/showcase-system/`; S04 should fill that zone with content grounded in `outputs/exports/eda/`, not create parallel docs elsewhere.

The repo already has the right ingredients. `outputs/exports/eda/manifest.json` and the per-track export summaries provide the honest current-state evidence surface. `.gsd/feature-plans/showcase-system/FEATURE_PLAN.md` plus its sprint/phase docs already reserve the trust-narrative and intern-workflow seams. `CoWork Planning/yelp_project/docs_agent/AGENTS.md` and `CoWork Planning/yelp_project/docs/intern/README.md` provide strong prior art for tone, scope, and trigger conditions for intern-facing explanations. The missing work is synthesis and enforcement, not new architecture.

Primary recommendation: author **two new S04-owned planning docs inside the showcase-system lane** — one for the trust-marketplace story and one for the intern-explainer workflow — then link them from the existing showcase docs and protect them with a dedicated pytest drift harness. This follows the loaded `coding-standards` DRY/KISS guidance (reuse the existing planning surface, do not duplicate it), the `article-writing` guidance (lead with concrete evidence, not abstractions), and the `verification-loop` / `test` guidance (prove the docs with observable assertions, matching the repo’s pytest pattern).

## Recommendation

Implement S04 inside `.gsd/feature-plans/showcase-system/`, not under `CoWork Planning/` and not as milestone-only prose.

Recommended file shape:

- `.gsd/feature-plans/showcase-system/TRUST_NARRATIVE.md`
- `.gsd/feature-plans/showcase-system/INTERN_EXPLAINER_WORKFLOW.md`
- update `.gsd/feature-plans/showcase-system/FEATURE_PLAN.md`
- update `.gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/SPRINT.md`
- update `.gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/phases/PHASE-01-export-driven-experience-map.md`
- add `tests/test_trust_narrative_workflow.py`

What the docs should do:

1. **Trust narrative doc**
   - State the exact spine already established by milestone context: **prediction → surfacing → monitoring → onboarding → accountability**.
   - Map each trust function to the actual exported track surfaces:
     - Track A = prediction
     - Track B = surfacing
     - Track C = monitoring
     - Track D = onboarding
     - Track E = accountability
   - Cite current truth from `outputs/exports/eda/manifest.json`, `EXPORT_CONTRACT.md`, and the five per-track `summary.md` files.
   - Keep the story honest about current gaps: Track D is still blocked by `outputs/tables/track_a_s5_candidate_splits.parquet`; most upstream analytical artifacts remain `missing`; Track E validity evidence is metadata-only.

2. **Intern explainer workflow doc**
   - Formalize **when** to invoke the explainer-style agent, **what inputs it needs**, **what it must cover**, and **what it must not do**.
   - Reuse prior-art rules from `CoWork Planning/yelp_project/docs_agent/AGENTS.md`: plain language, explain why it matters, no jargon without explanation, no raw review text.
   - Reuse the navigation expectation from `CoWork Planning/yelp_project/docs/intern/README.md`: glossary first, workflows second, code/config/decisions as needed.
   - Define trigger situations that match the slice goal: onboarding a new intern, explaining a track before edits, clarifying blockers like Track D’s dependency, and translating export/status surfaces into beginner-friendly walkthroughs.

3. **Verification**
   - Add a dedicated pytest file for S04 content rather than overloading `tests/test_feature_plan_architecture.py` with narrative-specific rules.
   - Assert the new docs exist, are linked from the showcase feature/sprint/phase docs, mention the five trust functions, cite the export bundle boundary, preserve internal/aggregate-safe language, and define explainer triggers/inputs/outputs/guardrails.

## Implementation Landscape

### Key Files

- `.gsd/feature-plans/showcase-system/FEATURE_PLAN.md` — current reserved S04 landing zone; already cites export inputs, prior-art intern docs, and the local-hosted showcase constraint.
- `.gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/SPRINT.md` — sprint contract that currently reserves the narrative/workflow seam and should gain explicit links to the S04 docs.
- `.gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/phases/PHASE-01-export-driven-experience-map.md` — phase-level handoff doc that should cite the final S04 docs as the content contract for later M004 work.
- `outputs/exports/eda/manifest.json` — authoritative machine-readable evidence root; contains scope=`internal`, safety boundary=`aggregate-safe`, track inventory, status totals, and Track D blocker metadata.
- `outputs/exports/eda/EXPORT_CONTRACT.md` — governance contract; the trust story must respect this boundary and the intern workflow must explicitly inherit its no-raw-text / no-raw-storage rules.
- `outputs/exports/eda/tracks/track_a/summary.md` — current exported summary for the prediction lane; story input for the Track A part of the trust narrative.
- `outputs/exports/eda/tracks/track_b/summary.md` — current exported summary for the surfacing lane.
- `outputs/exports/eda/tracks/track_c/summary.md` — current exported summary for the monitoring lane.
- `outputs/exports/eda/tracks/track_d/summary.md` — current exported summary for the onboarding lane; explicitly calls out the missing Track A Stage 5 split artifact.
- `outputs/exports/eda/tracks/track_e/summary.md` — current exported summary for the accountability lane; explicitly keeps fairness work aggregate-only and non-causal.
- `outputs/exports/eda/tracks/track_d/manifest.json` — machine-readable blocker truth for the onboarding lane; use this instead of only prose.
- `outputs/exports/eda/tracks/track_e/manifest.json` — machine-readable validity-log metadata for the accountability lane.
- `CoWork Planning/yelp_project/docs_agent/AGENTS.md` — best prior art for the explainer workflow contract: audience, tone, glossary rules, “why this matters,” and no raw review text.
- `CoWork Planning/yelp_project/docs/intern/README.md` — prior-art navigation model for what interns should read first and how explanation surfaces should be organized.
- `tests/test_feature_plan_architecture.py` — existing S03 regression file; useful style reference, but S04 content verification should likely live beside it in a new dedicated test file.
- `tests/CLAUDE.md` — confirms repo convention: keep new tests in `tests/`, use pytest, and prefer contract/regression assertions over heavy execution.

### Build Order

1. **Lock the two S04-owned docs first.**
   Create `TRUST_NARRATIVE.md` and `INTERN_EXPLAINER_WORKFLOW.md` in `.gsd/feature-plans/showcase-system/` before editing existing feature/sprint/phase docs. This establishes the canonical content surface instead of burying narrative paragraphs inside three existing files.

2. **Write the trust narrative from export truth, not milestone aspiration.**
   Build the story from `outputs/exports/eda/manifest.json`, `EXPORT_CONTRACT.md`, and per-track summaries/manifests. This is the riskiest part because S04 must connect the five tracks without overstating missing artifacts.

3. **Write the intern workflow from prior-art rules, then bind it to current evidence surfaces.**
   Use `docs_agent/AGENTS.md` for tone/process rules and `docs/intern/README.md` for navigation expectations, but make the workflow specific to the current repo handoff: export bundle first, track summaries second, code/workflow docs only as needed.

4. **Back-link the showcase planning docs.**
   Update `FEATURE_PLAN.md`, `SPRINT.md`, and `PHASE-01-export-driven-experience-map.md` so later M004 agents can discover the new S04 docs from the existing showcase lane without re-research.

5. **Add a dedicated drift harness last.**
   Add `tests/test_trust_narrative_workflow.py` asserting required content markers and links. This keeps architecture coverage (`test_feature_plan_architecture.py`) separate from slice-specific story/workflow coverage.

### Verification Approach

- `python -m pytest tests/test_trust_narrative_workflow.py`
- `python - <<'PY'
from pathlib import Path
for path in [
    Path('.gsd/feature-plans/showcase-system/TRUST_NARRATIVE.md'),
    Path('.gsd/feature-plans/showcase-system/INTERN_EXPLAINER_WORKFLOW.md'),
]:
    print(path.as_posix(), path.exists())
PY`
- `python - <<'PY'
from pathlib import Path
text = Path('.gsd/feature-plans/showcase-system/TRUST_NARRATIVE.md').read_text(encoding='utf-8')
for marker in [
    'prediction',
    'surfacing',
    'monitoring',
    'onboarding',
    'accountability',
    'outputs/exports/eda/manifest.json',
    'aggregate-safe',
    'internal',
    'track_a',
    'track_b',
    'track_c',
    'track_d',
    'track_e',
]:
    assert marker in text, marker
PY`
- `python - <<'PY'
from pathlib import Path
text = Path('.gsd/feature-plans/showcase-system/INTERN_EXPLAINER_WORKFLOW.md').read_text(encoding='utf-8')
for marker in [
    'when to invoke',
    'inputs',
    'outputs',
    'glossary',
    'raw review text',
    'CoWork Planning/yelp_project/docs_agent/AGENTS.md',
    'CoWork Planning/yelp_project/docs/intern/README.md',
]:
    assert marker in text, marker
PY`

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Trust-story evidence source | `outputs/exports/eda/manifest.json`, `EXPORT_CONTRACT.md`, and per-track exported summaries/manifests | These are already the verified aggregate-safe handoff surfaces from S02; inventing a second story dataset would drift immediately. |
| Intern explainer tone and scope | `CoWork Planning/yelp_project/docs_agent/AGENTS.md` | It already defines audience, no-jargon rules, glossary upkeep, “why it matters,” and the no-raw-review-text guardrail. |
| Intern navigation model | `CoWork Planning/yelp_project/docs/intern/README.md` | It already tells interns where to start and how to navigate glossary/workflows/code/config/decisions. |
| Regression style | existing pytest docs/tests under `tests/` | The repo already validates document contracts with pytest; S04 should match that pattern instead of inventing a shell-only checker. |

## Constraints

- S04 directly owns **R004** and must formalize the explainer workflow in repo planning, not just in legacy prior-art docs.
- S04 must stay inside the established planning architecture; do not create a parallel narrative tree outside `.gsd/feature-plans/showcase-system/` unless a later planner proves a stronger reason.
- The trust story must remain grounded in current export truth: `existing=6`, `missing=109`, Track D blocked by `outputs/tables/track_a_s5_candidate_splits.parquet`, Track E validity evidence metadata-only.
- The story and workflow must preserve the export governance boundary: internal, aggregate-safe, no raw review text, and no copied `.parquet`, `.ndjson`, or `.log` artifacts.
- No website scaffold exists yet. S04 is planning/story/workflow work only, not M004 implementation.

## Common Pitfalls

- **Writing the story like marketing copy** — avoid abstract claims that are not visible in `outputs/exports/eda/`. Follow the `article-writing` rule: lead with concrete evidence and explain after.
- **Editing `CoWork Planning/yelp_project/docs/intern/` as if it were the S04 contract** — those docs are prior art and intern-facing output, not the canonical planning surface for this slice.
- **Hiding blocker truth to make the story cleaner** — the narrative must carry forward Track D’s blocker and the generally stripped-worktree state instead of implying readiness.
- **Burying the workflow inside existing showcase docs only** — later agents need dedicated, discoverable docs, not scattered paragraphs across `FEATURE_PLAN.md`, `SPRINT.md`, and `PHASE`.
- **Folding S04 assertions into `test_feature_plan_architecture.py` only** — that file is about S03 structure; content-specific S04 drift is cleaner in a separate pytest file.

## Open Risks

- There is still no existing filename convention for S04-owned narrative docs, so the first implementation pass must choose stable names and then reference them consistently.
- If the trust narrative over-indexes on the ideal five-part story without showing current missing artifacts, S05 will likely fail integrated handoff review on honesty/consistency grounds.
- If the intern workflow is written too generically, later agents will still need to re-scope what evidence to read first and when to invoke the explainer.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| planning / long-form narrative docs | `article-writing` | installed |
| architecture consistency / DRY-KISS | `coding-standards` | installed |
| verification / pytest-aligned regression coverage | `test` | installed |
| completion proof / observable checks | `verification-loop` | installed |
| DuckDB | `silvainfm/claude-skills@duckdb` | available |
| Python data pipelines | `jorgealves/agent_skills@python-data-pipeline-designer` | available |
| Parquet | `majesticlabs-dev/majestic-marketplace@parquet-coder` | available |