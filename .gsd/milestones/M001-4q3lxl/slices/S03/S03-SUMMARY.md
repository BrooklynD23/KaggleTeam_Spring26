# Slice Summary — S03: Agent-ready planning architecture

## Status
- Complete
- Proof level: contract
- Requirement impact: R003 validated

## Goal
Establish a long-lived `.gsd/feature-plans/` execution surface that maps future work to real repo seams, current export evidence, and milestone drafts so downstream implementation agents can start from stable plans instead of re-scoping the repo from scratch.

## What This Slice Delivered

### 1) A canonical root contract for agent-ready feature planning
- `.gsd/feature-plans/README.md` now defines the single approved planning surface for post-M001 work.
- The root contract locks:
  - the seven canonical slugs
  - the required `FEATURE_PLAN.md` / `SPRINT.md` / `PHASE-*.md` layout
  - the rule that every lane must cite real repo paths, `outputs/exports/eda/` evidence, and milestone drafts
  - the rule that future targets must be labeled explicitly as future
  - the S03/S04 boundary that reserves, rather than prewrites, trust-narrative and intern-explainer content
- The README also includes a cross-feature dependency map so later agents can read the architecture in order instead of treating all lanes as equally ready.

### 2) Seven canonical feature-plan lanes tied to real repo seams
S03 populated one repo-grounded feature lane for each required execution surface:

1. `track-a-prediction`
   - preserves strict as-of / temporal framing
   - grounds future modeling to `data/curated/review_fact.parquet`
   - keeps banned snapshot-only fields visible as guardrails
2. `track-b-surfacing`
   - preserves snapshot-only usefulness ranking framing
   - keeps age-controlled grouping and `snapshot_metadata.json` visible
   - rejects vote-growth or trend-prediction drift
3. `track-c-monitoring`
   - keeps the lane framed as drift/monitoring rather than forecasting
   - points to current `src/eda/track_c/` seams and drift detection surfaces
4. `track-d-onboarding`
   - keeps D1/D2 cold-start framing explicit
   - carries forward `outputs/tables/track_a_s5_candidate_splits.parquet` as a real upstream blocker rather than implying readiness
5. `track-e-accountability`
   - treats Track E as an upstream-model fairness/audit lane, not a standalone predictor
   - forces future work to choose a real Track A or Track D audit target before claiming execution readiness
6. `showcase-system`
   - grounds the later local-hosted showcase to `outputs/exports/eda/`
   - keeps the website/report lane export-driven rather than live-query-driven
   - reserves S04-owned trust/intern surfaces via prior-art references only
7. `multimodal-experiments`
   - defines multimodal work as optional, non-critical-path future scope
   - ends the first sprint in an explicit expand-or-stop gate tied to M005

Each lane now contains:
- `FEATURE_PLAN.md`
- one first sprint under `sprints/SPRINT-01-*/SPRINT.md`
- one first phase doc under `sprints/*/phases/PHASE-01-*.md`

### 3) Agent-executable sprint and phase surfaces
The first sprint/phase docs do more than name future work. They make each lane executable by including:
- current evidence inputs
- concrete repo paths
- relevant launcher/module commands
- verification sections
- exit criteria
- blockers to carry forward
- future target folders labeled as future rather than implied current code

That pattern gives downstream agents a consistent starting shape regardless of lane while still preserving lane-specific constraints.

### 4) A mechanical drift harness for the full planning architecture
- `tests/test_feature_plan_architecture.py` now verifies the whole seven-lane architecture.
- The regression suite checks more than folder counts. It asserts:
  - exact canonical slug inventory
  - required doc counts and naming pattern
  - root README contract language
  - repo-path, export-evidence, and milestone references in every lane
  - lane-specific guardrails such as:
    - Track A temporal/as-of language
    - Track B snapshot-only and age-controlled language
    - Track D blocker truth for `track_a_s5_candidate_splits.parquet`
    - Track E upstream-model and fairness-versus-accuracy framing
    - showcase export-boundary / no live analytical storage rule
    - multimodal non-critical-path and expand-or-stop language
- S03 also kept the per-slug inventory diagnostic in the slice plan so incomplete planning surfaces fail with an inspectable missing-lane map instead of only a count mismatch.

## What Verification Proved

### Automated verification run
1. `python -m pytest tests/test_feature_plan_architecture.py`
   - Result: **7 passed**
2. `python - <<'PY' ... assert len(feature_plans) == 7 ... PY`
   - Result: passed
   - Proved the exact expected counts for feature plans, sprint docs, and phase docs.
3. `python - <<'PY' ... print(json.dumps(status, indent=2, sort_keys=True)) ... PY`
   - Result: passed
   - Proved each canonical slug exposes the expected `FEATURE_PLAN.md`, sprint doc, and phase doc surface.
4. `find .gsd/feature-plans -path '*/phases/*.md' | sort`
   - Result: passed
   - Confirmed the seven phase docs exist at the expected paths.

### Observability surfaces confirmed
The slice plan's observability surfaces are working and useful:
- `.gsd/feature-plans/README.md` is the root status surface for slug inventory, dependency order, and boundary rules.
- `tests/test_feature_plan_architecture.py` is the mechanical drift harness for the architecture.
- The per-slug inventory command from `S03-PLAN.md` prints which lane surfaces are present, making partial failures easy to inspect.

### Observed architecture truth after verification
The verified planning surface now contains:
- 7 canonical feature-plan folders
- 7 `FEATURE_PLAN.md` files
- 7 sprint docs
- 7 phase docs
- one locked root contract tying all seven lanes back to repo seams, export evidence, and milestone drafts

That matters because S03 did not just create placeholders. It created a durable execution architecture that downstream agents can read consistently across modeling, audit, showcase, and optional multimodal lanes.

## Key Output Behavior Established
- Planning architecture should be centralized under `.gsd/feature-plans/`, not split across ad hoc folders or milestone-only notes.
- Feature plans must stay honest about current repo state by carrying forward missing artifacts and upstream dependencies as blockers instead of implying readiness.
- Every lane should pair current evidence surfaces with clearly labeled future target folders.
- The planning layer should reserve S04 narrative/intern surfaces rather than absorbing that content early.
- Planning regressions should fail on missing guardrail language and missing cross-links, not only on missing files.

## Decisions and Useful Context Captured
- D016: use `.gsd/feature-plans/` with seven canonical slugs and a fixed `FEATURE_PLAN.md` / sprint / phase layout as the long-lived execution surface.
- D017: feature-plan lanes must ground to current export manifests/checklists and carry forward blockers explicitly instead of implying implementation readiness.
- Existing decisions reinforced by this slice:
  - D002: the later showcase should consume exported artifacts instead of querying analytical storage live.
  - D004: Track E is an audit layer on a real upstream model, not a standalone predictor.
  - D005: multimodal work remains future, narrow, and non-critical-path.
- Knowledge retained for future agents: the S03 drift harness asserts required language such as `Future Target Folders (Future)` plus repo/evidence/milestone/blocker references; if it fails, use the per-slug inventory command before rewriting structure blindly.

## Requirement Updates
- `R003` moved from **active** to **validated** because S03 proved the repo now has distinct, canonical feature-plan folders with sprint/phase breakdowns detailed enough for downstream agents to execute against real repo paths, export evidence, milestone drafts, and blocker truth.

## What Next Slices Should Know

### For S04 (trust narrative and intern explainer workflow)
- The planning architecture is ready; S04 should write into the reserved narrative/explainer surfaces without inventing a new planning structure.
- Use the existing feature lanes as the execution scaffolding for narrative mapping rather than duplicating lane descriptions elsewhere.
- Keep prior-art references under `CoWork Planning/yelp_project/docs_agent/AGENTS.md` and `CoWork Planning/yelp_project/docs/intern/README.md` as the starting point for intern-facing workflow authoring.

### For S05 (integrated local handoff verification)
- Reuse `tests/test_feature_plan_architecture.py` plus the per-slug inventory command as the planning verification layer.
- Verify the planning surfaces together with the S01/S02 evidence layers rather than independently.
- Keep Track D's blocker, Track E's upstream-model gate, and the showcase export boundary visible during integrated handoff checks.

### For M002 / M003 / M004 / M005 executors
- Start from the lane-specific `FEATURE_PLAN.md`, then the first `SPRINT.md`, then the first phase doc.
- Do not remove the `Future Target Folders (Future)` section when promoting a lane; replace future placeholders only when real implementation surfaces are created.
- Preserve the lane framing: temporal for A, snapshot-only for B, drift for C, cold-start plus Track A Stage 5 dependency for D, upstream audit for E, export-driven local showcase for the showcase lane, and scope-gated optional work for multimodal.

## Residual Risks
- S03 built the planning architecture, but S04 still needs to author the trust-marketplace narrative and intern-explainer workflow.
- S05 still needs to verify the planning layer together with the evidence and narrative layers in one integrated pass.
- The architecture intentionally preserves real blockers rather than hiding them, especially Track D's missing candidate-split artifact and Track E's missing upstream audited model surface.
- There is still no implemented modeling or website runtime surface in the repo; S03 only established the execution plans that later slices will follow.
