# Project

## What This Is

An internal academic analytical platform for the Yelp Open Dataset that treats Yelp as a **trust marketplace**. The project answers five framing questions across prediction, content surfacing, platform health, cold-start onboarding, and fairness auditing, then turns the findings into a local-hosted showcase, final report, and presentation artifacts.

## Core Value

If scope shrinks, the thing that must survive is this: the team can **measure, predict, and audit platform trust** with reproducible evidence that is strong enough for the final report, final presentation, and internal department showcase.

## Current State

The repo already has substantial brownfield implementation:

- Shared ingestion, schema validation, curated Parquet construction, and orchestration are implemented in Python.
- EDA pipelines exist for Tracks A, B, C, D, and E under `src/eda/track_a/` through `src/eda/track_e/`.
- M001 is complete: the repo now has a verified EDA handoff surface for Tracks A-E, including the five final summary markdowns plus `outputs/tables/eda_artifact_census.md`, `outputs/tables/eda_artifact_census.csv`, and `outputs/tables/eda_command_checklist.md`.
- The aggregate-safe export bundle is complete under `outputs/exports/eda/`, with root and per-track JSON/CSV/PNG/MD surfaces suitable for downstream reporting and the later local showcase.
- The planning layer is complete for milestone handoff: `.gsd/feature-plans/README.md` plus seven canonical feature lanes now give downstream agents repo-grounded `FEATURE_PLAN.md` / `SPRINT.md` / `PHASE-*.md` execution surfaces, with `tests/test_feature_plan_architecture.py` guarding against drift.
- The showcase lane now includes the trust-marketplace narrative and the intern explainer workflow under `.gsd/feature-plans/showcase-system/`, with `tests/test_trust_narrative_workflow.py` protecting those contracts.
- M001 closeout reruns (`scripts/report_eda_completeness.py` → `scripts/package_eda_exports.py` → handoff pytest suite) preserved honest EDA/export truth at that stage (`existing=6`, `missing=109`) and metadata-only Track E validity evidence; M002 then consumed those surfaces and resolved baseline-track blocking through integrated Track A/B/C/D1 modeling outputs.
- `data/curated/` already contains the shared curated inputs needed for Track A/B/D planning, including `review_fact.parquet`, `review_fact_track_b.parquet`, `review.parquet`, `business.parquet`, `user.parquet`, `checkin.parquet`, and `snapshot_metadata.json`.
- M004 S01 is complete: a runnable Next.js showcase shell now exists under `showcase/`, driven by canonical intake artifacts at `outputs/showcase/intake/{manifest.json,validation_report.json}` with explicit homepage readiness and blocked diagnostics plus a deterministic `intake_unavailable` fallback state.
- M004 S03 is complete: canonical track drill-down artifacts (`outputs/showcase/story/tracks.json`, `tracks_validation_report.json`) now drive `/tracks` and `/tracks/[trackKey]`, with governance markers and evidence diagnostics (`surface_key`, `path`, `reason`, `requirement_key`) parity-checked by `scripts/showcase_smoke_check.py` across homepage, executive, and track routes.
- M004 S04 is complete: report and deck deliverables (`outputs/showcase/deliverables/showcase_report.md`, `showcase_deck.md`) are now generated from the same canonical story/track contracts as the site, and `scripts/check_showcase_parity.py` emits machine-readable drift diagnostics at `outputs/showcase/deliverables/parity_report.json` for section order, evidence keys, pointer fields, requirement continuity, and governance markers.
- M004 is complete: the local showcase/report/deck system now closes with `python scripts/run_showcase_demo_gate.py --config configs/showcase.yaml --base-url http://127.0.0.1:3000 --output outputs/showcase/verification/demo_gate_report.json`, a one-command fail-closed integrated gate across build/parity/frontend/smoke/governance phases that emits authoritative diagnostics in `outputs/showcase/verification/demo_gate_report.json`.
- M002 baseline modeling is complete: Track A, Track B, Track C, and Track D1 each have reproducible baseline runtimes plus standardized artifact bundles under `outputs/modeling/track_*/`.
- Track A is the default M003 fairness-audit target, with Track D retained as secondary evidence and D2 remaining optional/non-blocking.
- M003 S01 is complete: `python -m src.modeling.track_a.audit_intake` regenerates a canonical upstream intake bundle at `outputs/modeling/track_a/audit_intake/` with contract-validated `scored_intake.parquet`, readiness/status manifest metadata, and failure-phase diagnostics.
- M003 S02 is complete: `python -m src.modeling.track_e.fairness_audit` now consumes S01 intake and writes a canonical fairness bundle at `outputs/modeling/track_e/fairness_audit/` (`subgroup_metrics.parquet`, `disparity_summary.parquet`, `manifest.json`, `validation_report.json`) with `ready_for_mitigation`/`blocked_upstream` semantics and handoff-contract coverage for S03/S04.
- M003 S03 is complete: `python -m src.modeling.track_e.mitigation_experiment` now writes canonical mitigation artifacts at `outputs/modeling/track_e/mitigation_experiment/` (`pre_post_delta.parquet`, `manifest.json`, `validation_report.json`) with explicit `ready_for_closeout`/`blocked_upstream`/`blocked_insufficient_signal` semantics and exact `baseline_anchor`/`split_context` continuity for S05 handoff.
- M003 S04 is complete: `python -m src.modeling.track_a.stronger_comparator` now writes canonical comparator artifacts at `outputs/modeling/track_a/stronger_comparator/` (`materiality_table.parquet`, `manifest.json`, `validation_report.json`) with deterministic `ready_for_closeout`/`blocked_upstream` semantics, strict gate-boolean schema checks, fairness-aware adoption decisions, and handoff continuity coverage for S05.
- M003 S05 is complete: `python -m src.modeling.m003_closeout_gate` now reruns S01→S04 and emits canonical closeout artifacts at `outputs/modeling/m003_closeout/` (`stage_status_table.parquet`, `manifest.json`, `validation_report.json`, `closeout_summary.md`) with explicit `compute_escalation_decision` semantics (`local_sufficient`/`overflow_required`) and fail-closed readiness truth.
- M003 S06 and S07 are complete: fairness sufficiency fallback semantics (`signal_sufficiency`) now feed a sparse-ready mitigation path that emits non-empty `pre_post_delta.parquet`, and canonical closeout reruns now resolve `outputs/modeling/m003_closeout/manifest.json` to `ready_for_handoff` with `stage_rollup.readiness_block_stage_ids=[]` and explicit escalation decision vocabulary.
- Milestone closeout verification was rerun after S07 with `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest ...test_m003_mitigation_contract.py ...test_m003_track_e_mitigation_experiment.py ...test_m003_mitigation_handoff_contract.py ...test_m003_milestone_closeout_gate.py ...test_m003_closeout_handoff_contract.py -q` (19 passed), and the roadmap slice checklist now shows S01–S07 all checked.
- Deep photo/image modeling is not part of the current implemented pipeline and is being kept as future work after the core modeling path.

## Architecture / Key Patterns

- **CLI-first Python pipeline:** `python scripts/run_pipeline.py` and `python scripts/pipeline_dispatcher.py` orchestrate the existing brownfield workflow.
- **Config-driven data flow:** shared and per-track settings live in `configs/`; source code should not hardcode paths.
- **Curated data backbone:** `data/curated/` is the handoff surface between ingestion/curation and downstream analytical work.
- **Aggregate-safe outputs:** shared artifacts live in `outputs/` and must avoid raw review text in tables, logs, figures, reports, and later website exports.
- **Track-specific evaluation rules:** Track A uses strict as-of temporal rules, Track B is a snapshot ranking task, Track D separates D1 and D2 cold-start flows, and Track E is an audit layer rather than a standalone predictor.
- **Website delivery pattern:** the future local-hosted website should read exported JSON/CSV/PNG artifacts rather than query Parquet or DuckDB live.
- **Narrative pattern:** the project is organized around the trust-marketplace story — prediction, surfacing, onboarding, monitoring, and accountability — rather than five disconnected analyses.

## Capability Contract

See `.gsd/REQUIREMENTS.md` for the explicit capability contract, requirement status, and coverage mapping.

## Milestone Sequence

- [x] M001-4q3lxl: EDA completion, evidence packaging, and planning handoff — Complete. The repo now has verified five-track EDA summaries, an aggregate-safe export bundle, agent-ready planning lanes, trust narrative / intern workflow docs, and a passing integrated local handoff verification surface for M002 kickoff.
- [x] M002-c1uww6: Baseline modeling by track — Complete. Track A/B/C/D1 baselines are integrated under the shared modeling contract, with R005–R008 validated and Track A set as the default M003 audit intake.
- [x] M003-rdpeu4: Fairness audit and stronger modeling passes — Complete. S01–S07 now rerun canonically to handoff-ready truth, with mitigation `ready_for_closeout`, closeout `ready_for_handoff`, empty readiness-block rollup, and explicit conditional compute-escalation evidence for M004 consumption.
- [x] M004-fjc2zy: Local showcase, report, and presentation system — Complete. S01–S05 delivered the intake-locked shell, executive and track flows, report/deck parity generation, and an integrated fail-closed local demo gate with governance/no-live-query enforcement.
- [ ] M005-i0a235: Future multimodal extensions — Explore photo/image multimodal work beyond the core semester path if the core milestones are already secure.
