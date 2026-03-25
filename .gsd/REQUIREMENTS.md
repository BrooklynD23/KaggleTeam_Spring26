# Requirements

This file is the explicit capability and coverage contract for the project.

## Active

### R009 — Track E must audit at least one upstream model from Track A or Track D, quantify disparity, and apply one mitigation lever to show the fairness-versus-accuracy tradeoff.
- Class: quality-attribute
- Status: active
- Description: Track E must audit at least one upstream model from Track A or Track D, quantify disparity, and apply one mitigation lever to show the fairness-versus-accuracy tradeoff.
- Why it matters: The accountability layer of the trust story is strongest when the team can say “we built the model, then checked whether it works fairly.”
- Source: user
- Primary owning slice: M003-rdpeu4 (provisional)
- Supporting slices: M002-c1uww6 (provisional), M003-rdpeu4/S01, M003-rdpeu4/S02, M003-rdpeu4/S03, M003-rdpeu4/S05, M003-rdpeu4/S06, M003-rdpeu4/S07
- Validation: partially validated (M003-rdpeu4/S01+S02+S03+S05+S06+S07): upstream intake/fairness/mitigation/closeout contract suites and canonical reruns pass, including S07 sparse-ready mitigation/closeout gates via `python -m pytest tests/test_m003_mitigation_contract.py tests/test_m003_track_e_mitigation_experiment.py tests/test_m003_mitigation_handoff_contract.py tests/test_m003_milestone_closeout_gate.py tests/test_m003_closeout_handoff_contract.py -q`, `python -m src.modeling.track_e.mitigation_experiment --config configs/track_e.yaml --intake-dir outputs/modeling/track_a/audit_intake --fairness-dir outputs/modeling/track_e/fairness_audit --output-dir outputs/modeling/track_e/mitigation_experiment`, and artifact assertions confirming `status=ready_for_closeout`, `validation.status=pass`, non-empty `pre_post_delta.parquet`, and populated `lever_metadata.evaluation_diagnostics`.
- Notes: S06 removed empty-but-pass fairness outcomes by adding sufficiency diagnostics and fallback branch semantics (`primary_sufficient`/`fallback_sufficient`/`insufficient`) while preserving status vocabulary compatibility (`ready_for_mitigation`/`blocked_upstream`); S07 now advances mitigation to non-empty `ready_for_closeout` on canonical sparse replay with machine-readable sparse-path diagnostics, and closer rerun evidence confirms `pre_post_rows=8` with `evaluation_diagnostics.active_path=sparse_all_splits`.

### R010 — After baselines exist, the project should compare stronger or combined models only where they meaningfully improve answers to the framing questions.
- Class: differentiator
- Status: active
- Description: After baselines exist, the project should compare stronger or combined models only where they meaningfully improve answers to the framing questions.
- Why it matters: The team wants more than baseline-only work, but stronger models should serve the research questions rather than exist as a model zoo.
- Source: user
- Primary owning slice: M003-rdpeu4/S04
- Supporting slices: M003-rdpeu4/S01, M003-rdpeu4/S02, M003-rdpeu4/S05, M003-rdpeu4/S06, M003-rdpeu4/S07
- Validation: partially validated (M003-rdpeu4/S04+S05 with S06/S07 continuity support): comparator contract/runtime/handoff checks passed via `python -m pytest tests/test_m003_comparator_contract.py tests/test_m003_track_a_stronger_comparator.py tests/test_m003_comparator_handoff_contract.py -q`, canonical replay `python -m src.modeling.track_a.stronger_comparator --config configs/track_a.yaml --intake-dir outputs/modeling/track_a/audit_intake --fairness-dir outputs/modeling/track_e/fairness_audit --candidate-metrics tests/fixtures/m003_candidate_metrics.csv --output-dir outputs/modeling/track_a/stronger_comparator`, and S07 closeout replay checks confirming mitigation `ready_for_closeout` propagates to `ready_for_handoff` with `stage_rollup.readiness_block_stage_ids=[]`.
- Notes: S04 remains the comparator producer and S05 remains the integrated closeout consumer. S06 hardens prerequisite fairness readiness semantics, and S07 confirms the canonical mitigation-ready path clears closeout readiness blocks without changing comparator decision vocabulary.

### R022 — The project may operationalize Colab Pro or HPC workflows if local Windows + RTX 3080 execution is not enough for the final modeling pass.
- Class: operability
- Status: active
- Description: The project may operationalize Colab Pro or HPC workflows if local Windows + RTX 3080 execution is not enough for the final modeling pass.
- Why it matters: The team has backup compute, but does not want the setup burden unless it materially helps the final report.
- Source: user
- Primary owning slice: M003-rdpeu4/S05
- Supporting slices: M003-rdpeu4/S07, M004-fjc2zy (provisional)
- Validation: partially validated (M003-rdpeu4/S05+S07): closeout contract/runtime/handoff checks and canonical replay emit deterministic `compute_escalation_decision` vocabulary (`local_sufficient`/`overflow_required`) with explicit runtime-capacity trigger evidence and fairness-scarcity non-trigger evidence via `python -m pytest tests/test_m003_closeout_contract.py tests/test_m003_milestone_closeout_gate.py tests/test_m003_closeout_handoff_contract.py -q`, `python -m src.modeling.m003_closeout_gate --track-a-config configs/track_a.yaml --track-e-config configs/track_e.yaml --predictions outputs/modeling/track_a/predictions_test.parquet --metrics outputs/modeling/track_a/metrics.csv --candidate-metrics tests/fixtures/m003_candidate_metrics.csv --output-dir outputs/modeling/m003_closeout`, and S07 assertions that closeout remains `ready_for_handoff` with `stage_rollup.readiness_block_stage_ids=[]`.
- Notes: M004-fjc2zy/S05 added explicit continuity assertions for blocked closeout diagnostics in smoke + integrated gate outputs (`demo_gate_report.json`), but requirement ownership and primary validation remain in M003 closeout workflows.

## Validated

### R001 — Tracks A, B, C, D, and E must all have complete, verified, presentation-ready EDA summaries and supporting evidence artifacts.
- Class: core-capability
- Status: validated
- Description: Tracks A, B, C, D, and E must all have complete, verified, presentation-ready EDA summaries and supporting evidence artifacts.
- Why it matters: Baseline modeling and final storytelling will be weak if the analytical foundation is partial, inconsistent, or missing a track.
- Source: user
- Primary owning slice: M001-4q3lxl/S01
- Supporting slices: M001-4q3lxl/S05
- Validation: Validated by S01 after `python -m pytest tests/test_pipeline_dispatcher_all_tracks.py tests/test_track_a_summary_report.py tests/test_track_b_summary_report.py tests/test_track_d_summary_report.py tests/test_eda_artifact_census_report.py` passed and repeated `python scripts/report_eda_completeness.py` runs materialized/confirmed `outputs/tables/track_a_s8_eda_summary.md`, `track_b_s8_eda_summary.md`, `track_c_s9_eda_summary.md`, `track_d_s9_eda_summary.md`, `track_e_s9_eda_summary.md`, `eda_artifact_census.md`, `eda_artifact_census.csv`, and `eda_command_checklist.md`.
- Notes: S01 verified the final EDA summary handoff surface for all five tracks and made partial-repo fallback behavior explicit; S05 will still perform integrated milestone-level handoff verification.

### R002 — The repo must produce JSON, CSV, PNG, and markdown outputs that are robust enough for the report flow and the later local-hosted website to consume without querying analytical storage live.
- Class: integration
- Status: validated
- Description: The repo must produce JSON, CSV, PNG, and markdown outputs that are robust enough for the report flow and the later local-hosted website to consume without querying analytical storage live.
- Why it matters: The final report, presentation, and website all depend on reliable export surfaces rather than brittle ad hoc handoffs.
- Source: inferred
- Primary owning slice: M001-4q3lxl/S02
- Supporting slices: M001-4q3lxl/S05
- Validation: Validated in M001-4q3lxl/S02 by passing `python -m pytest /home/brooklynd23/.gsd/projects/2ccfe7e768a0/worktrees/M001-4q3lxl/tests/test_package_eda_exports.py` and the real CLI bundle checks for `python scripts/package_eda_exports.py`, proving `outputs/exports/eda/` materializes JSON, CSV, PNG, and markdown export surfaces for Tracks A-E without querying analytical storage live.
- Notes: Root bundle now exposes manifest.json, manifest.csv, EXPORT_CONTRACT.md, eda_command_checklist.md, eda_overview.png, and per-track summary/manifest/artifacts/status-card surfaces under outputs/exports/eda/.

### R003 — The planning layer must include distinct feature-plan folders and sprint/phase breakdowns detailed enough for downstream implementation agents to execute without re-inventing scope.
- Class: operability
- Status: validated
- Description: The planning layer must include distinct feature-plan folders and sprint/phase breakdowns detailed enough for downstream implementation agents to execute without re-inventing scope.
- Why it matters: The project is on a four-week clock and depends on multi-agent execution speed; vague planning will slow the team down.
- Source: user
- Primary owning slice: M001-4q3lxl/S03
- Supporting slices: M001-4q3lxl/S05
- Validation: Validated in M001-4q3lxl/S03 by passing `python -m pytest tests/test_feature_plan_architecture.py` plus the slice inventory checks for exactly seven canonical feature-plan lanes, seven sprint docs, and seven phase docs under `.gsd/feature-plans/`, with each lane grounded to real repo paths, export evidence, milestone drafts, blocker truth, and explicit future-target labeling.
- Notes: S03 established the long-lived `.gsd/feature-plans/` execution surface and the drift harness that fails if canonical slugs, required doc surfaces, or critical planning guardrails change.

### R004 — The repo planning must explain when to invoke an explainer-style agent for interns, what it should cover, and why it exists.
- Class: admin/support
- Status: validated
- Description: The repo planning must explain when to invoke an explainer-style agent for interns, what it should cover, and why it exists.
- Why it matters: The team wants repeatable intern-facing explanations of process, not just implementation notes for experienced contributors.
- Source: user
- Primary owning slice: M001-4q3lxl/S04
- Supporting slices: M001-4q3lxl/S05
- Validation: Validated by the S04 contract handoff after `python -m pytest tests/test_trust_narrative_workflow.py -q` proved the dedicated trust narrative and intern explainer workflow docs exist, stay linked from the canonical showcase feature/sprint/phase docs, preserve the `internal` + `aggregate-safe` export boundary, and keep Track D blocker plus Track E metadata-only evidence honest; S05 then hardened the milestone handoff surface with `python -m pytest tests/test_trust_narrative_workflow.py tests/test_m001_handoff_verification.py -q` plus placeholder and requirement-state assertions on `.gsd/milestones/M001-4q3lxl/slices/S04/S04-SUMMARY.md`, `.gsd/milestones/M001-4q3lxl/slices/S04/S04-UAT.md`, and this requirement section.
- Notes: Existing prior art under `CoWork Planning/yelp_project/docs_agent/` and `CoWork Planning/yelp_project/docs/intern/` now feeds a repo-local, test-protected planning contract instead of remaining only background guidance.

### R005 — Track A must have a baseline future-star prediction model evaluated under the track's strict temporal rules.
- Class: core-capability
- Status: validated
- Description: Track A must have a baseline future-star prediction model evaluated under the track's strict temporal rules.
- Why it matters: The trust story's prediction layer breaks if quality prediction remains only at EDA level.
- Source: user
- Primary owning slice: M002-c1uww6/S06
- Supporting slices: none
- Validation: Validated by M002 S06 integrated gate: cross-track pytest suite plus Track A baseline CLI rerun and persisted artifacts under outputs/modeling/track_a/ (metrics.csv, config_snapshot.json, summary.md).
- Notes: Track A remains the default M003 fairness-audit target unless explicitly re-scoped.

### R006 — Track B must have a baseline usefulness-ranking model evaluated within the track's age-controlled snapshot framing.
- Class: core-capability
- Status: validated
- Description: Track B must have a baseline usefulness-ranking model evaluated within the track's age-controlled snapshot framing.
- Why it matters: The content-surfacing leg of the trust story depends on a real ranking baseline, not only label engineering and feasibility analysis.
- Source: user
- Primary owning slice: M002-c1uww6/S06
- Supporting slices: none
- Validation: Validated by M002 S06 integrated gate: cross-track pytest suite plus Track B baseline CLI rerun and persisted artifacts under outputs/modeling/track_b/ with grouped NDCG comparator ordering evidence.
- Notes: Snapshot-only ranking framing and grouped evaluation contract remain required for downstream work.

### R007 — Track C must deliver a baseline drift-detection or trend-characterization model such as linear sentiment trends by city/category over time rather than a heavyweight forecasting requirement.
- Class: core-capability
- Status: validated
- Description: Track C must deliver a baseline drift-detection or trend-characterization model such as linear sentiment trends by city/category over time rather than a heavyweight forecasting requirement.
- Why it matters: The platform-health layer should show early warning and characterization, not disappear behind over-ambitious forecasting scope.
- Source: user
- Primary owning slice: M002-c1uww6/S06
- Supporting slices: none
- Validation: Validated by M002 S06 integrated gate: cross-track pytest suite plus Track C baseline CLI rerun and persisted drift/monitoring artifacts under outputs/modeling/track_c.
- Notes: Track C remains monitoring/drift characterization scope; forecasting framing stays out of contract.

### R008 — Track D must deliver a cold-start recommendation baseline that is evaluated against explicit as-of popularity baselines for the D1 and/or D2 subtracks.
- Class: core-capability
- Status: validated
- Description: Track D must deliver a cold-start recommendation baseline that is evaluated against explicit as-of popularity baselines for the D1 and/or D2 subtracks.
- Why it matters: The onboarding layer of the trust story depends on proving that new businesses or users can be served better than the trivial baseline.
- Source: user
- Primary owning slice: M002-c1uww6/S06
- Supporting slices: none
- Validation: Validated by M002 S06 integrated gate: cross-track pytest suite plus Track D baseline CLI rerun and persisted artifacts under outputs/modeling/track_d/, with D1 comparator evidence and D2 optional/non-blocking status.
- Notes: D1 is the milestone-validated path; D2 remains optional unless future milestone contract changes explicitly.

### R011 — The project must include a local-hosted Next.js + Motion website that presents the work for team and department showcase use without relying on public cloud hosting.
- Class: launchability
- Status: validated
- Description: The project must include a local-hosted Next.js + Motion website that presents the work for team and department showcase use without relying on public cloud hosting.
- Why it matters: The final showcase is part of the semester deliverable, and the site must be robust enough to run locally from exported artifacts.
- Source: user
- Primary owning slice: M004-fjc2zy/S01
- Supporting slices: M001-4q3lxl (exports), M003-rdpeu4 (final evidence), M004-fjc2zy/S02, M004-fjc2zy/S03, M004-fjc2zy/S05
- Validation: Validated by M004-fjc2zy/S05 integrated gate proof: `python -m pytest tests/test_showcase_smoke_check.py tests/test_showcase_demo_gate.py -q`, `python -m pytest tests/test_showcase_intake_contract.py tests/test_showcase_story_contract.py tests/test_showcase_track_contract.py tests/test_showcase_report_contract.py tests/test_showcase_deck_contract.py tests/test_showcase_parity_contract.py -q`, `npm --prefix showcase run test -- --run`, `npm --prefix showcase run build`, and `python scripts/run_showcase_demo_gate.py --config configs/showcase.yaml --base-url http://127.0.0.1:3000 --output outputs/showcase/verification/demo_gate_report.json` (plus `test -f` assertion) all passed, proving local-hosted Next.js runtime and assembled verification path are launch-ready without live analytics queries.
- Notes: S05 closes launchability by adding deterministic one-command local demo gate with phase-level diagnostics and fail-closed behavior.

### R012 — The final written and presentation artifacts must tell a coherent business-oriented story: prediction, surfacing, onboarding, monitoring, and accountability.
- Class: launchability
- Status: validated
- Description: The final written and presentation artifacts must tell a coherent business-oriented story: prediction, surfacing, onboarding, monitoring, and accountability.
- Why it matters: Weak story is one of the user’s two stated failure modes.
- Source: user
- Primary owning slice: M004-fjc2zy/S04
- Supporting slices: M001-4q3lxl, M002-c1uww6, M003-rdpeu4/S02, M003-rdpeu4/S03, M003-rdpeu4/S04, M003-rdpeu4/S05, M003-rdpeu4/S06, M003-rdpeu4/S07, M004-fjc2zy/S02, M004-fjc2zy/S03, M004-fjc2zy/S05
- Validation: Validated by M004-fjc2zy/S05 continuity gate: parity contracts and integrated demo gate all passed, including `tests/test_showcase_report_contract.py`, `tests/test_showcase_deck_contract.py`, `tests/test_showcase_parity_contract.py`, and generated `outputs/showcase/deliverables/parity_report.json` with section_order/evidence_keys/pointer_fields/requirement_keys/governance_markers checks all passing; `run_showcase_demo_gate` enforces parity in end-to-end flow.
- Notes: S05 hardens S04 continuity into an operational fail-closed gate so website/report/deck stay synchronized under one canonical story/evidence contract.

### R013 — Shared artifacts must remain aggregate-safe, internally scoped, and free of raw review text or public-redistribution assumptions.
- Class: constraint
- Status: validated
- Description: Shared artifacts must remain aggregate-safe, internally scoped, and free of raw review text or public-redistribution assumptions.
- Why it matters: Governance failure would invalidate the deliverables no matter how strong the modeling looks.
- Source: research
- Primary owning slice: M001-4q3lxl/S02
- Supporting slices: M001-4q3lxl/S05, M004-fjc2zy (provisional)
- Validation: Validated in M001-4q3lxl/S02 by passing forbidden-artifact exclusion checks after `python scripts/package_eda_exports.py`, proving `outputs/exports/eda/` contains no `.parquet`, `.ndjson`, or copied `.log` files while EXPORT_CONTRACT.md and per-track manifests keep the aggregate-safe/internal-only governance boundary explicit.
- Notes: Packaging now rebuilds outputs/exports/eda from scratch each run, copies only allowlisted markdown sources, and carries Track E validity evidence forward as metadata-only summaries instead of raw log redistribution.

## Deferred

### R020 — After the core semester path is secure, the project may run one narrow true multimodal experiment using photo/image data.
- Class: differentiator
- Status: deferred
- Description: After the core semester path is secure, the project may run one narrow true multimodal experiment using photo/image data.
- Why it matters: The team wants to explore multimodal work, but not at the cost of the baseline semester deliverables.
- Source: user
- Primary owning slice: M005-i0a235 (provisional)
- Supporting slices: none
- Validation: unmapped
- Notes: This is future work, not part of the core deadline path.

### R021 — Only expand photo/image work beyond the first experiment if the first pass shows real value and the compute cost is justified.
- Class: differentiator
- Status: deferred
- Description: Only expand photo/image work beyond the first experiment if the first pass shows real value and the compute cost is justified.
- Why it matters: Multimodal scope can balloon quickly and must be earned by evidence.
- Source: inferred
- Primary owning slice: M005-i0a235 (provisional)
- Supporting slices: none
- Validation: unmapped
- Notes: This is future work, not assumed semester-critical work.

## Out of Scope

### R030 — The showcase site will not depend on AWS or other public cloud hosting.
- Class: constraint
- Status: out-of-scope
- Description: The showcase site will not depend on AWS or other public cloud hosting.
- Why it matters: This prevents wasted planning around infrastructure the team does not have budget or credits for.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: The site is local-hosted.

### R031 — The project will not publish raw Yelp data, row-level derived outputs, or a public showcase artifact.
- Class: anti-feature
- Status: out-of-scope
- Description: The project will not publish raw Yelp data, row-level derived outputs, or a public showcase artifact.
- Why it matters: This prevents governance drift and misreads of the deliverable scope.
- Source: research
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Internal academic use only.

### R032 — The future site should not become a live analytics product that queries Parquet, DuckDB, or a database at request time.
- Class: anti-feature
- Status: out-of-scope
- Description: The future site should not become a live analytics product that queries Parquet, DuckDB, or a database at request time.
- Why it matters: This keeps the website robust, local, and matched to the repo’s export-driven workflow.
- Source: inferred
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Use exported JSON/CSV/PNG artifacts instead.

### R033 — Track E will not be planned as an independent predictive task disconnected from upstream models.
- Class: constraint
- Status: out-of-scope
- Description: Track E will not be planned as an independent predictive task disconnected from upstream models.
- Why it matters: This prevents a misleading roadmap and keeps the fairness story tied to real model behavior.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Track E’s modeling role is audit + mitigation.

## Traceability

| ID | Class | Status | Primary owner | Supporting | Proof |
|---|---|---|---|---|---|
| R001 | core-capability | validated | M001-4q3lxl/S01 | M001-4q3lxl/S05 | Validated by S01 after `python -m pytest tests/test_pipeline_dispatcher_all_tracks.py tests/test_track_a_summary_report.py tests/test_track_b_summary_report.py tests/test_track_d_summary_report.py tests/test_eda_artifact_census_report.py` passed and repeated `python scripts/report_eda_completeness.py` runs materialized/confirmed `outputs/tables/track_a_s8_eda_summary.md`, `track_b_s8_eda_summary.md`, `track_c_s9_eda_summary.md`, `track_d_s9_eda_summary.md`, `track_e_s9_eda_summary.md`, `eda_artifact_census.md`, `eda_artifact_census.csv`, and `eda_command_checklist.md`. |
| R002 | integration | validated | M001-4q3lxl/S02 | M001-4q3lxl/S05 | Validated in M001-4q3lxl/S02 by passing `python -m pytest /home/brooklynd23/.gsd/projects/2ccfe7e768a0/worktrees/M001-4q3lxl/tests/test_package_eda_exports.py` and the real CLI bundle checks for `python scripts/package_eda_exports.py`, proving `outputs/exports/eda/` materializes JSON, CSV, PNG, and markdown export surfaces for Tracks A-E without querying analytical storage live. |
| R003 | operability | validated | M001-4q3lxl/S03 | M001-4q3lxl/S05 | Validated in M001-4q3lxl/S03 by passing `python -m pytest tests/test_feature_plan_architecture.py` plus the slice inventory checks for exactly seven canonical feature-plan lanes, seven sprint docs, and seven phase docs under `.gsd/feature-plans/`, with each lane grounded to real repo paths, export evidence, milestone drafts, blocker truth, and explicit future-target labeling. |
| R004 | admin/support | validated | M001-4q3lxl/S04 | M001-4q3lxl/S05 | Validated by the S04 contract handoff after `python -m pytest tests/test_trust_narrative_workflow.py -q` proved the dedicated trust narrative and intern explainer workflow docs exist, stay linked from the canonical showcase feature/sprint/phase docs, preserve the `internal` + `aggregate-safe` export boundary, and keep Track D blocker plus Track E metadata-only evidence honest; S05 then hardened the milestone handoff surface with `python -m pytest tests/test_trust_narrative_workflow.py tests/test_m001_handoff_verification.py -q` plus placeholder and requirement-state assertions on `.gsd/milestones/M001-4q3lxl/slices/S04/S04-SUMMARY.md`, `.gsd/milestones/M001-4q3lxl/slices/S04/S04-UAT.md`, and this requirement section. |
| R005 | core-capability | validated | M002-c1uww6/S06 | none | Validated by M002 S06 integrated gate: cross-track pytest suite plus Track A baseline CLI rerun and persisted artifacts under outputs/modeling/track_a/ (metrics.csv, config_snapshot.json, summary.md). |
| R006 | core-capability | validated | M002-c1uww6/S06 | none | Validated by M002 S06 integrated gate: cross-track pytest suite plus Track B baseline CLI rerun and persisted artifacts under outputs/modeling/track_b/ with grouped NDCG comparator ordering evidence. |
| R007 | core-capability | validated | M002-c1uww6/S06 | none | Validated by M002 S06 integrated gate: cross-track pytest suite plus Track C baseline CLI rerun and persisted drift/monitoring artifacts under outputs/modeling/track_c. |
| R008 | core-capability | validated | M002-c1uww6/S06 | none | Validated by M002 S06 integrated gate: cross-track pytest suite plus Track D baseline CLI rerun and persisted artifacts under outputs/modeling/track_d/, with D1 comparator evidence and D2 optional/non-blocking status. |
| R009 | quality-attribute | active | M003-rdpeu4 (provisional) | M002-c1uww6 (provisional), M003-rdpeu4/S01, M003-rdpeu4/S02, M003-rdpeu4/S03, M003-rdpeu4/S05, M003-rdpeu4/S06, M003-rdpeu4/S07 | partially validated (M003-rdpeu4/S01+S02+S03+S05+S06+S07): upstream intake/fairness/mitigation/closeout contract suites and canonical reruns pass, including S07 sparse-ready mitigation/closeout gates via `python -m pytest tests/test_m003_mitigation_contract.py tests/test_m003_track_e_mitigation_experiment.py tests/test_m003_mitigation_handoff_contract.py tests/test_m003_milestone_closeout_gate.py tests/test_m003_closeout_handoff_contract.py -q`, `python -m src.modeling.track_e.mitigation_experiment --config configs/track_e.yaml --intake-dir outputs/modeling/track_a/audit_intake --fairness-dir outputs/modeling/track_e/fairness_audit --output-dir outputs/modeling/track_e/mitigation_experiment`, and artifact assertions confirming `status=ready_for_closeout`, `validation.status=pass`, non-empty `pre_post_delta.parquet`, and populated `lever_metadata.evaluation_diagnostics`. |
| R010 | differentiator | active | M003-rdpeu4/S04 | M003-rdpeu4/S01, M003-rdpeu4/S02, M003-rdpeu4/S05, M003-rdpeu4/S06, M003-rdpeu4/S07 | partially validated (M003-rdpeu4/S04+S05 with S06/S07 continuity support): comparator contract/runtime/handoff checks passed via `python -m pytest tests/test_m003_comparator_contract.py tests/test_m003_track_a_stronger_comparator.py tests/test_m003_comparator_handoff_contract.py -q`, canonical replay `python -m src.modeling.track_a.stronger_comparator --config configs/track_a.yaml --intake-dir outputs/modeling/track_a/audit_intake --fairness-dir outputs/modeling/track_e/fairness_audit --candidate-metrics tests/fixtures/m003_candidate_metrics.csv --output-dir outputs/modeling/track_a/stronger_comparator`, and S07 closeout replay checks confirming mitigation `ready_for_closeout` propagates to `ready_for_handoff` with `stage_rollup.readiness_block_stage_ids=[]`. |
| R011 | launchability | validated | M004-fjc2zy/S01 | M001-4q3lxl (exports), M003-rdpeu4 (final evidence), M004-fjc2zy/S02, M004-fjc2zy/S03, M004-fjc2zy/S05 | Validated by M004-fjc2zy/S05 integrated gate proof: `python -m pytest tests/test_showcase_smoke_check.py tests/test_showcase_demo_gate.py -q`, `python -m pytest tests/test_showcase_intake_contract.py tests/test_showcase_story_contract.py tests/test_showcase_track_contract.py tests/test_showcase_report_contract.py tests/test_showcase_deck_contract.py tests/test_showcase_parity_contract.py -q`, `npm --prefix showcase run test -- --run`, `npm --prefix showcase run build`, and `python scripts/run_showcase_demo_gate.py --config configs/showcase.yaml --base-url http://127.0.0.1:3000 --output outputs/showcase/verification/demo_gate_report.json` (plus `test -f` assertion) all passed, proving local-hosted Next.js runtime and assembled verification path are launch-ready without live analytics queries. |
| R012 | launchability | validated | M004-fjc2zy/S04 | M001-4q3lxl, M002-c1uww6, M003-rdpeu4/S02, M003-rdpeu4/S03, M003-rdpeu4/S04, M003-rdpeu4/S05, M003-rdpeu4/S06, M003-rdpeu4/S07, M004-fjc2zy/S02, M004-fjc2zy/S03, M004-fjc2zy/S05 | Validated by M004-fjc2zy/S05 continuity gate: parity contracts and integrated demo gate all passed, including `tests/test_showcase_report_contract.py`, `tests/test_showcase_deck_contract.py`, `tests/test_showcase_parity_contract.py`, and generated `outputs/showcase/deliverables/parity_report.json` with section_order/evidence_keys/pointer_fields/requirement_keys/governance_markers checks all passing; `run_showcase_demo_gate` enforces parity in end-to-end flow. |
| R013 | constraint | validated | M001-4q3lxl/S02 | M001-4q3lxl/S05, M004-fjc2zy (provisional) | Validated in M001-4q3lxl/S02 by passing forbidden-artifact exclusion checks after `python scripts/package_eda_exports.py`, proving `outputs/exports/eda/` contains no `.parquet`, `.ndjson`, or copied `.log` files while EXPORT_CONTRACT.md and per-track manifests keep the aggregate-safe/internal-only governance boundary explicit. |
| R020 | differentiator | deferred | M005-i0a235 (provisional) | none | unmapped |
| R021 | differentiator | deferred | M005-i0a235 (provisional) | none | unmapped |
| R022 | operability | active | M003-rdpeu4/S05 | M003-rdpeu4/S07, M004-fjc2zy (provisional) | partially validated (M003-rdpeu4/S05+S07): closeout contract/runtime/handoff checks and canonical replay emit deterministic `compute_escalation_decision` vocabulary (`local_sufficient`/`overflow_required`) with explicit runtime-capacity trigger evidence and fairness-scarcity non-trigger evidence via `python -m pytest tests/test_m003_closeout_contract.py tests/test_m003_milestone_closeout_gate.py tests/test_m003_closeout_handoff_contract.py -q`, `python -m src.modeling.m003_closeout_gate --track-a-config configs/track_a.yaml --track-e-config configs/track_e.yaml --predictions outputs/modeling/track_a/predictions_test.parquet --metrics outputs/modeling/track_a/metrics.csv --candidate-metrics tests/fixtures/m003_candidate_metrics.csv --output-dir outputs/modeling/m003_closeout`, and S07 assertions that closeout remains `ready_for_handoff` with `stage_rollup.readiness_block_stage_ids=[]`. |
| R030 | constraint | out-of-scope | none | none | n/a |
| R031 | anti-feature | out-of-scope | none | none | n/a |
| R032 | anti-feature | out-of-scope | none | none | n/a |
| R033 | constraint | out-of-scope | none | none | n/a |

## Coverage Summary

- Active requirements: 3
- Mapped to slices: 3
- Validated: 11 (R001, R002, R003, R004, R005, R006, R007, R008, R011, R012, R013)
- Unmapped active requirements: 0
