# S03 — Research

**Date:** 2026-03-21

## Summary

S03 directly owns **R003** and only supports **R004** at the boundary level. The repo already has good short-horizon planning artifacts under `.gsd/milestones/M001-4q3lxl/` plus rich brownfield prior art in `CoWork Planning/yelp_project/`, but it does **not** have a long-lived execution surface for downstream work after M001. There is no existing `.gsd/feature-plans/` or equivalent root, and there is no model-layer or web-app scaffold in the codebase yet (`src/modeling/` and any Next.js app are absent). That means S03 should create planning architecture, not pretend implementation scaffolds already exist.

Primary recommendation: add a **dedicated planning root under `.gsd/`**, separate from milestone folders, then seed it with feature-plan folders that map to the repo’s real ownership seams: the five trust-marketplace tracks plus the later showcase and multimodal work. This follows the `coding-standards` DRY/KISS guidance: keep milestone drafts (`.gsd/milestones/M002-c1uww6/` through `M005-i0a235/`) as the source of future-milestone truth, keep `outputs/exports/eda/` as the source of current evidence truth, and make the new feature plans a routing/execution layer that links those two instead of duplicating both.

A milestone-only planning structure would still force later agents to re-scope broad work inside M002 and M004. The repo is already organized by track (`src/eda/track_a/` … `track_e/`), the trust story is already organized by dimension (prediction, surfacing, monitoring, onboarding, accountability), and the new export bundle is already organized per track under `outputs/exports/eda/tracks/`. So the most agent-ready structure is:

- `.gsd/feature-plans/track-a-prediction/`
- `.gsd/feature-plans/track-b-surfacing/`
- `.gsd/feature-plans/track-c-monitoring/`
- `.gsd/feature-plans/track-d-onboarding/`
- `.gsd/feature-plans/track-e-accountability/`
- `.gsd/feature-plans/showcase-system/`
- `.gsd/feature-plans/multimodal-experiments/`

Each plan should then contain `sprints/` subfolders and phase docs that point to concrete repo paths, commands, export inputs, and blockers. Per the `verification-loop` skill, S03 should also add an observable, repeatable verification surface — ideally a pytest file — so the architecture is proven by filesystem structure and document content, not by “the docs exist.”

## Recommendation

Create a new planning layer rooted at **`.gsd/feature-plans/`** rather than embedding long-lived feature execution docs under `.gsd/milestones/` or `CoWork Planning/`.

Recommended structure:

- Root index: `.gsd/feature-plans/README.md`
- One folder per feature/trust dimension plus later cross-cutting work:
  - `track-a-prediction`
  - `track-b-surfacing`
  - `track-c-monitoring`
  - `track-d-onboarding`
  - `track-e-accountability`
  - `showcase-system`
  - `multimodal-experiments`
- Inside each feature plan:
  - a top-level plan doc (`FEATURE_PLAN.md` or `README.md`)
  - `sprints/SPRINT-01-.../SPRINT.md`
  - `sprints/SPRINT-01-.../phases/PHASE-01-...md` style phase docs

Why this shape:

1. **It matches real repo seams.** Future code work will land in track-specific Python packages, not inside one giant “M002” folder.
2. **It preserves existing GSD milestone docs as authoritative context.** The feature plans should link to `M002`–`M005` drafts rather than restate them.
3. **It keeps S03 scoped correctly.** S03 establishes the architecture and repo-grounded execution surface. S04 can then write the trust-story and intern-explainer content into the already-stable structure instead of redefining where it belongs.
4. **It is verifiable with existing project testing patterns.** The repo already uses pytest heavily, and the `test` skill says to match existing framework conventions rather than invent a new one.

Recommended minimum content per feature plan:

- trust-marketplace role
- future milestone crosswalk (`M002`, `M003`, `M004`, `M005` as relevant)
- concrete repo areas touched now or later
- current evidence inputs from `outputs/exports/eda/`
- blockers / dependencies (especially Track D)
- sprint list
- phase docs with: goals, inputs, target files/dirs, commands, verification, exit criteria

Recommended sprint pattern:

- Track A–D plans: baseline modeling → stronger modeling / audit handoff → showcase evidence handoff
- Track E plan: audit target selection → mitigation / tradeoff measurement → showcase evidence handoff
- Showcase plan: site foundation → report/deck assembly → local demo hardening
- Multimodal plan: scope gate → first experiment → expand-or-stop decision

S03 should **not** fully author the intern-explainer workflow. It should only reserve stable surfaces that S04 can fill, while linking current prior art in `CoWork Planning/yelp_project/docs_agent/AGENTS.md` and `CoWork Planning/yelp_project/docs/intern/README.md`.

## Implementation Landscape

### Key Files

- `.gsd/PROJECT.md` — current project status and milestone sequence; confirms S03 is the remaining planning-architecture slice in M001.
- `.gsd/REQUIREMENTS.md` — authoritative requirement owner map; S03 owns `R003`, while `R004` belongs to S04 and should be treated as a boundary, not absorbed into this slice.
- `.gsd/milestones/M002-c1uww6/M002-c1uww6-CONTEXT-DRAFT.md` — draft baseline-modeling context; use as the seed for Track A–D feature-plan goals instead of restating modeling scope from scratch.
- `.gsd/milestones/M003-rdpeu4/M003-rdpeu4-CONTEXT-DRAFT.md` — draft fairness / stronger-modeling context; especially important for Track E and for identifying which upstream plans need an audit handoff.
- `.gsd/milestones/M004-fjc2zy/M004-fjc2zy-CONTEXT-DRAFT.md` — draft local showcase context; should seed the `showcase-system` feature plan and its site/report/deck sprints.
- `.gsd/milestones/M005-i0a235/M005-i0a235-CONTEXT-DRAFT.md` — draft multimodal future-work context; should seed a narrow, explicitly non-critical-path feature plan.
- `outputs/exports/eda/manifest.json` — current machine-readable evidence handoff; feature plans should cite this bundle, not absent upstream parquet or hypothetical live storage.
- `outputs/exports/eda/EXPORT_CONTRACT.md` — aggregate-safe export contract; later plans should treat this as the website/report consumption boundary.
- `outputs/tables/eda_command_checklist.md` — canonical launcher order and Track D dependency wording; useful for phase docs that reference current EDA prerequisites.
- `src/eda/track_a/` through `src/eda/track_e/` — real code ownership seams that justify track-aligned feature-plan folders.
- `CoWork Planning/yelp_project/01_PRD_Yelp_Open_Dataset.md` — semester roadmap, deliverables, and week-by-week framing; useful for naming sprints and keeping plans aligned with the original semester cadence.
- `CoWork Planning/yelp_project/07_Implementation_Plan_Ingestion_TrackA_TrackB.md` — existing phase/execution-order model for Tracks A and B; useful for phase naming and for what “agent-ready” detail looks like in practice.
- `CoWork Planning/yelp_project/10_Implementation_Plan_TrackC_TrackD.md` — strongest existing phase-table prior art; already includes explicit phase ordering and success criteria that can be compressed into S03 phase docs.
- `CoWork Planning/yelp_project/docs_agent/AGENTS.md` — intern-docs prior art that S04 will later formalize into a workflow; S03 should reference this but avoid taking over the content.
- `CoWork Planning/yelp_project/docs/intern/README.md` — existing intern-facing navigation hub; another boundary reference for S04.
- `scripts/check_docs_drift.py` — good pattern if execution wants a lightweight planning-drift checker or dependency map later.
- `tests/test_check_repo_readme_drift.py` — good pytest pattern for filesystem/document-structure assertions against docs-oriented scripts.

### Build Order

1. **Lock the root convention first.**
   Add `.gsd/feature-plans/README.md` and choose the canonical feature-plan slugs before writing content. This is the main architectural decision; everything else hangs off it.

2. **Seed feature-plan folders from authoritative inputs, not blank prose.**
   Create the seven plan folders and top-level plan docs by crosswalking:
   - future milestone drafts (`.gsd/milestones/M002...M005`)
   - current export/evidence surfaces (`outputs/exports/eda/`)
   - actual code ownership seams (`src/eda/track_*`)

3. **Add sprint folders and phase docs only after the feature split is stable.**
   Reuse the phase discipline already visible in `CoWork Planning/yelp_project/07_...` and `10_...`: ordered phases, explicit dependencies, explicit success criteria. Do not create generic “phase 1/2/3” docs with no repo grounding.

4. **Add structural verification last, but in the same slice.**
   Preferred path: add `tests/test_feature_plan_architecture.py` (name can vary) that asserts required plan folders, sprint folders, and phase docs exist and contain required headings / path references. This follows the `test` skill’s guidance to match the repo’s existing pytest workflow.

### Verification Approach

- **Automated structure check (recommended):** add a pytest file such as `tests/test_feature_plan_architecture.py` that asserts:
  - `.gsd/feature-plans/README.md` exists
  - all required feature-plan folders exist
  - every feature plan has a top-level plan doc plus a `sprints/` directory
  - every sprint has a `SPRINT.md` and at least one phase doc
  - every plan references at least one concrete repo path and one milestone draft or export surface
  - the Track D plan explicitly mentions `outputs/tables/track_a_s5_candidate_splits.parquet`

- **Content-level spot checks:** use executable grep-style assertions for critical cross-links, e.g. confirming that at least one plan cites `outputs/exports/eda/manifest.json` and that the showcase plan cites `M004-fjc2zy`.

- **Manual sanity pass:** verify the feature-plan split eliminates re-scoping pressure. If a later agent can open one feature folder and see sprint/phase order, dependencies, files, and verification targets without rereading milestone drafts, S03 succeeded.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Future milestone scope | `.gsd/milestones/M002-c1uww6/` through `M005-i0a235/` context drafts | These already capture the intended milestone sequencing and boundaries; feature plans should point to them, not recreate them. |
| Phase ordering patterns | `CoWork Planning/yelp_project/07_Implementation_Plan_Ingestion_TrackA_TrackB.md` and `10_Implementation_Plan_TrackC_TrackD.md` | These docs already show concrete phase tables, dependency ordering, and success criteria that can be compressed into agent-ready phase docs. |
| Docs/testing pattern | `scripts/check_docs_drift.py` and `tests/test_check_repo_readme_drift.py` | The repo already has a pattern for verifying documentation structure with Python + pytest; reuse it instead of inventing a one-off shell-only validator. |
| Evidence inputs | `outputs/exports/eda/manifest.json` and `outputs/exports/eda/EXPORT_CONTRACT.md` | These are already the stable, aggregate-safe handoff surfaces after S02; later plans should consume them directly. |

## Constraints

- S03 directly owns **R003**. It should not try to fully satisfy **R004**, which belongs to S04.
- The planning layer should live under `.gsd/` per milestone context, not inside `CoWork Planning/`, which is prior-art planning rather than the new execution surface.
- There is **no** model-layer scaffold and **no** web-app scaffold in the repo today. Plans must distinguish “future target folder” from “existing source folder.”
- Track D remains blocked by `outputs/tables/track_a_s5_candidate_splits.parquet`; any planning architecture that hides this will drift from live repo truth.
- Later showcase/report plans should use `outputs/exports/eda/` as their evidence contract, not query Parquet/DuckDB live.
- Planning docs must stay aggregate-safe and must not introduce raw review text.

## Common Pitfalls

- **Planning by milestone only** — A single broad `M002` plan will still force later agents to split A/B/C/D themselves. Use track-/feature-aligned folders instead.
- **Duplicating milestone draft prose** — If every feature plan rewrites `M002`–`M005` context, drift will start immediately. Cross-link instead.
- **Letting S03 swallow S04** — Reserve stable surfaces for the trust narrative and intern-explainer workflow, but do not fully write those docs here.
- **Ignoring live evidence surfaces** — S02 already created `outputs/exports/eda/`; future planning should cite that bundle rather than absent intermediate artifacts.
- **Weak verification** — File existence alone is not enough. Verify structure plus critical references so later agents cannot create empty shells that technically satisfy folder counts.

## Open Risks

- If the plan set is too large or too prose-heavy, it will become stale before M002 execution starts.
- If the plan set is too shallow, later agents will still need to re-scope baseline modeling and showcase work, failing `R003` in practice.
- Track-aligned feature plans plus a showcase plan need explicit boundaries so evidence handoff is referenced once and not copy-pasted across all plans.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| planning / long-form execution docs | `article-writing` | installed |
| repo verification / pytest-aligned test writing | `test` | installed |
| architecture consistency / DRY/KISS | `coding-standards` | installed |
| completion proof / observable evidence | `verification-loop` | installed |
| DuckDB | `silvainfm/claude-skills@duckdb` | available |
| Python data pipelines | `jorgealves/agent_skills@python-data-pipeline-designer` | available |
| Parquet | `majesticlabs-dev/majestic-marketplace@parquet-coder` | available |