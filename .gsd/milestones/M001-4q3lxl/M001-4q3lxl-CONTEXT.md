# M001-4q3lxl: EDA completion, evidence packaging, and planning handoff

**Gathered:** 2026-03-21
**Status:** Ready for planning

## Project Description

This milestone turns the current brownfield Yelp repo into a clean handoff surface for the rest of the semester. The repo already contains shared ingestion, curated Parquet outputs, and implemented EDA pipelines for Tracks A, B, C, D, and E, but the semester path still has gaps: some track outputs are missing or incomplete, there is no standardized export contract for the final report or the future website, there is no agent-ready sprint/phase planning structure, and the repo does not yet formalize the project’s **trust marketplace** story.

The story being preserved here is exact and deliberate: **“A review platform is a trust marketplace — and every dimension of that trust is measurable, predictable, and auditable.”** M001 is the milestone that makes that sentence operational. It finishes the evidence base, packages it for downstream use, and writes the planning architecture the team will use for the four-week push.

## Why This Milestone

Baseline modeling across every track depends on the EDA layer being complete, trustworthy, and presentation-ready. The user explicitly called out **weak modeling** and **weak story** as the failure modes that would disappoint them most. Right now the repo has strong implementation momentum but not yet a clean, verified handoff into modeling, reporting, and the local-hosted showcase. M001 solves that first.

## User-Visible Outcome

### When this milestone is complete, the user can:

- run the existing Python pipeline and see complete, verified, aggregate-safe EDA summary artifacts for all five tracks
- inspect a detailed planning structure that breaks the semester work into distinct feature plans, sprint folders, and phase docs for downstream implementation agents

### Entry point / environment

- Entry point: `python scripts/run_pipeline.py` plus repo planning artifacts under `.gsd/`
- Environment: local dev
- Live dependencies involved: none

## Completion Class

- Contract complete means: all five tracks have verified final EDA summaries, an explicit completeness status, standardized export targets, and a documented planning structure for the next milestones
- Integration complete means: existing pipeline outputs, export packaging rules, the trust-marketplace narrative, and the agent-planning structure agree with each other and point to the same downstream work
- Operational complete means: the required local commands and file checks succeed on the current repo without relying on hypothetical future infrastructure

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- the repo can materialize or verify final EDA summary artifacts for Tracks A, B, C, D, and E from the current CLI-first pipeline
- the repo exposes aggregate-safe export surfaces that a later local-hosted Next.js + Motion site can consume without querying Parquet or DuckDB live
- the planning layer now explains the trust-marketplace story, the intern-explainer workflow, and the feature-plan / sprint / phase structure well enough that later agents can execute without re-scoping the project

## Risks and Unknowns

- Track completeness drift — the repo contains implemented track code, but not every track currently has visible materialized summary outputs, which can create false confidence about readiness
- Story fragmentation — five strong track analyses can still fail the final presentation if they do not ladder into the trust-marketplace narrative
- Export contract brittleness — the future local website and report flow will be fragile if export packaging is not explicit and robust
- Planning drift from real code — sprint and phase docs will be noise if they are not grounded in the actual repo layout, current outputs, and track constraints

## Existing Codebase / Prior Art

- `scripts/run_pipeline.py` — canonical local entry point for shared and per-track pipeline execution
- `scripts/pipeline_dispatcher.py` — execution engine with existing stage/output contracts for shared work and Tracks A–E
- `src/eda/track_a/` through `src/eda/track_e/` — implemented EDA stages for the five framing questions
- `outputs/tables/track_a_s8_eda_summary.md`, `outputs/tables/track_b_s8_eda_summary.md`, `outputs/tables/track_c_s9_eda_summary.md` — evidence that much of the brownfield analytical flow is already materialized
- `CoWork Planning/yelp_project/docs_agent/AGENTS.md` and `CoWork Planning/yelp_project/docs/intern/` — prior art for the intern-facing explanation workflow the user now wants formalized in planning

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

- R001 — Finish all five EDA tracks to presentation-ready quality
- R002 — Standardize robust aggregate-safe export artifacts for downstream reporting and site consumption
- R003 — Create a detailed execution planning structure with distinct feature plans, sprint subfolders, and phase docs
- R004 — Document an intern-explainer agent workflow in the repo planning
- R013 — Preserve governance-safe outputs for internal academic team and department showcase use only

## Scope

### In Scope

- verify the current brownfield state of Tracks A–E and close gaps between implemented EDA code and materialized final outputs
- define and package the aggregate-safe export contract for later report, presentation, and website use
- write the feature-plan / sprint / phase planning structure for downstream implementation agents
- formalize the trust-marketplace story and the intern-explainer workflow in repo planning
- run a local handoff verification proving that M002 can start from this evidence base

### Out of Scope / Non-Goals

- building the baseline modeling layer itself
- scaffolding the Next.js + Motion site itself
- public cloud hosting, live backend work, or production deployment concerns
- true multimodal photo/image modeling

## Technical Constraints

- No raw review text in shared outputs, figures, logs, reports, or later website exports
- Track rules already encoded in the repo stay in force: Track A as-of temporal rules, Track B snapshot-only ranking rules, Track D D1/D2 separation, Track E audit positioning
- The future website is local-hosted and should read exported artifacts rather than analytical storage directly
- The user wants detailed feature-plan / sprint / phase structure before downstream implementation agents take over
- There is no website setup yet; the mock-up and Motion landing-page template pull should happen later when the website sprint arrives

## Integration Points

- Existing CLI pipeline — verifies and materializes the EDA layer
- `data/curated/` Parquet outputs — current shared analytical backbone
- `outputs/tables/`, `outputs/figures/`, `outputs/logs/` — current evidence surfaces to standardize and package
- `.gsd/` planning artifacts — new agent-ready planning layer for milestone, sprint, and phase execution
- Future local-hosted website — downstream consumer of the export contract defined here

## Open Questions

- Which exact per-track files and commands become the canonical modeling handoff artifacts after export packaging is standardized? — Current thinking: the export contract should make this explicit in M001 rather than leave it implicit in `outputs/`
- How detailed should the first pass of feature-plan / sprint / phase planning be before implementation begins? — Current thinking: detailed enough for agent execution, but still grounded in milestone/slice/task boundaries rather than giant prose docs
- Does Track D need any EDA repair beyond a missing or unverified final summary artifact? — Current thinking: verify the current output state first, then close only the real gaps
