# M002-c1uww6: Baseline modeling by track — Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

## Project Description

This milestone turns the completed EDA layer into real baseline models for the trust-marketplace story. In this framing, the work is not “do some modeling somewhere in the repo.” It is the first milestone that has to prove the project can actually **predict, surface, monitor, and support onboarding** rather than only describe those ideas.

The milestone covers the baseline modeling path for four concrete trust dimensions:

- **Track A** — future star rating prediction under strict temporal rules
- **Track B** — usefulness ranking under age-controlled snapshot rules
- **Track C** — drift/trend monitoring rather than heavyweight forecasting
- **Track D1** — business cold-start recommendation against explicit as-of popularity baselines

Track E is not a standalone predictor here. It remains downstream in M003 as the fairness-audit layer on top of an upstream model, with **Track A locked in as the default audit target** unless later evidence forces a rethink.

## Why This Milestone

The team explicitly wants more than EDA. M001 created the analytical handoff layer and export surfaces, but the weak point in the semester story is still the jump from “we profiled the problem” to “we can actually model it.”

This milestone exists to make that jump real without letting scope sprawl. It should establish one honest, reproducible baseline per required track, prove the local-first compute path, and create the evidence surface that later fairness-audit and showcase work can build on.

This also matters now because M003 depends on at least one real upstream model. If M002 stays vague or drifts into premature model-zoo work, the accountability story arrives late and weaker than it needs to be.

## User-Visible Outcome

### When this milestone is complete, the user can:

- inspect evaluated baseline model reports for Tracks A, B, C, and D1
- point to one concrete baseline capability for prediction, surfacing, monitoring, and onboarding
- hand off a clean upstream model surface to M003 without reinterpreting milestone intent

### Entry point / environment

- Entry point: Python modeling scripts and evaluation/report artifacts produced through a shared modeling contract to be defined during planning
- Environment: local dev first, with native Windows preferred for any compute-heavy runs
- Live dependencies involved: local compute by default; Colab Pro or HPC only as conditional fallback if local execution is not enough

## Completion Class

- Contract complete means: Track A, Track B, Track C, and Track D1 each have at least one reproducible baseline with track-appropriate evaluation surfaces and trivial comparators where applicable
- Integration complete means: the baselines read the existing curated inputs and EDA handoff artifacts cleanly, and write through one shared modeling contract rather than ad hoc per-track output conventions
- Operational complete means: the team can run the baseline workflow on the local-first path and identify the intended M003 fairness-audit handoff target without needing fallback infrastructure by default

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- Track A has a real future-star baseline evaluated under strict temporal rules with leakage-safe evidence surfaces
- Track B has a snapshot-only usefulness baseline evaluated inside age-controlled ranking groups
- Track C has a drift/trend monitoring baseline with explicit drift evidence and no forecasting overreach
- Track D1 has a business cold-start baseline evaluated against an explicit as-of popularity comparator
- the required baseline outputs are packaged through one shared modeling contract that downstream M003/M004 work can consume without cleanup
- what cannot be simulated if this milestone is to be considered truly done: the local-first execution path for the baseline workflow has to work in the real repo environment rather than existing only as a planning assumption

## Risks and Unknowns

- Baseline scope creep — the four-week window can get consumed by extra model families before the first honest baseline path is secure
- Track C ambiguity — if “monitoring” is not kept concrete, the lane can collapse into prose-only summary work or bloat into forecasting
- Track D expansion pressure — D2 user cold start exists in the broader track framing, but making it an implicit requirement here would add recommender scope the milestone does not need
- Artifact drift — if each track emits different output shapes and conventions, M003 fairness audit work and M004 storytelling inherit cleanup instead of reusable evidence
- Compute optimism — local compute may be enough for baseline work, but the milestone should prove that rather than assume it

## Existing Codebase / Prior Art

- `src/eda/track_a/` through `src/eda/track_d/` — existing track-specific logic, leakage rules, and evaluation framing the baselines must respect
- `data/curated/review_fact.parquet` and `data/curated/review_fact_track_b.parquet` — current curated inputs that anchor Track A and Track B baseline work
- `src/eda/track_c/drift_detection.py` and `src/eda/track_c/sentiment_baseline.py` — prior art for keeping Track C grounded in drift/trend characterization instead of heavy forecasting
- `src/eda/track_d/popularity_baseline.py` and `src/eda/track_d/evaluation_cohorts.py` — prior art for Track D’s explicit as-of popularity comparison and cohort framing
- `CoWork Planning/yelp_project/01_PRD_Yelp_Open_Dataset.md` — canonical evaluation philosophy, per-track success metrics, and the baseline-modeling milestone slot in the semester roadmap
- `.gsd/milestones/M001-4q3lxl/M001-4q3lxl-CONTEXT.md` — the upstream trust-marketplace framing and M001 export/handoff decisions this milestone inherits

## Current Worktree Truth

- The current worktree already exposes the curated modeling inputs `data/curated/review_fact.parquet`, `data/curated/review_fact_track_b.parquet`, `data/curated/review.parquet`, `data/curated/business.parquet`, `data/curated/user.parquet`, and `data/curated/snapshot_metadata.json`.
- The current worktree also already has key Track A–D EDA artifacts under `outputs/tables/`, including `track_a_s5_candidate_splits.parquet`, Track B ranking-prep tables through `track_b_s8_eda_summary.md`, Track C drift/monitoring tables through `track_c_s9_eda_summary.md`, and Track D cold-start preparation artifacts through `track_d_s8_leakage_report.parquet`.
- As a result, stale inherited wording about missing upstream artifacts or Track D being blocked on Track A Stage 5 should be treated as retired for this milestone; the remaining first-order need is the shared modeling contract, not regenerating prerequisite EDA outputs.
- Scope lock remains explicit for all downstream slices: D1 required, D2 optional, Track A preferred as the default M003 fairness-audit target.

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

- R005 — This milestone advances the prediction layer by requiring a real Track A baseline under strict temporal rules
- R006 — This milestone advances the surfacing layer by requiring a real Track B usefulness-ranking baseline in the snapshot-only framing
- R007 — This milestone advances the monitoring layer by requiring Track C to stay a drift/trend detection baseline rather than a forecasting project
- R008 — This milestone advances the onboarding layer by requiring a Track D cold-start baseline against explicit as-of popularity baselines, with D1 as the required semester-safe path
- R009 — This milestone prepares the upstream model surface that M003 will audit, with Track A chosen now as the default fairness-audit handoff target
- R012 — This milestone keeps the “trust marketplace” story concrete by turning four trust dimensions into actual baseline evidence rather than disconnected EDA summaries

## Scope

### In Scope

- one evaluated baseline path each for Track A, Track B, Track C, and Track D1
- a shared modeling package/artifact contract for the baseline work rather than loose per-track scripting only
- local-first execution proof for the baseline workflow
- clean handoff surfaces for M003 fairness audit and later report/showcase packaging
- explicit preservation of the prediction / surfacing / monitoring / onboarding story across the four required tracks

### Out of Scope / Non-Goals

- Track E fairness audit implementation itself
- mandatory Track D2 delivery in this milestone
- heavyweight forecasting for Track C
- stronger comparative model-zoo work beyond what is needed to establish disciplined baselines
- public deployment or website implementation

## Technical Constraints

- Track-specific repo rules from the current codebase remain binding, including leakage prevention and banned snapshot-only fields
- Track B remains a single-snapshot ranking task and must not drift into vote-growth prediction
- Track C stays in drift/trend monitoring framing, not forecasting framing
- Track D1 and D2 remain separate; D1 is the required path for M002 and D2 is not silently folded into the milestone contract
- Shared outputs must remain aggregate-safe and free of raw review text
- The milestone should prove the local-first compute path before formalizing any Colab Pro or HPC fallback workflow

## Integration Points

- `data/curated/` — supplies the curated Parquet inputs the baseline models will consume
- `outputs/tables/`, `outputs/figures/`, and `outputs/logs/` — provide existing EDA evidence the baseline layer should align with rather than duplicate blindly
- shared modeling package/artifact contract — provides the stable surface that M002 baseline outputs will write through
- M003-rdpeu4 — consumes at least one upstream model from this milestone for fairness auditing, with Track A as the default audit target
- M004-fjc2zy — later consumes the resulting metrics, summaries, and evidence surfaces for the final story and showcase packaging

## Open Questions

- Which exact baseline family is right for each track while staying honest about compute and schedule? — Current thinking: decide during planning, but keep the bar at one disciplined baseline per required track rather than a model zoo
- How much comparative experimentation belongs in M002 versus M003? — Current thinking: M002 should stop at baseline proof plus obvious comparators; stronger or broader comparisons belong later only if they materially improve the framing questions
- If local compute proves insufficient for one track, what is the minimum fallback plan worth documenting without bloating the milestone? — Current thinking: keep fallback infrastructure conditional and lightweight rather than making Colab Pro or HPC part of the default contract
