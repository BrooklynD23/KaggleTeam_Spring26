# S03: Agent-ready planning architecture

**Goal:** Establish a long-lived `.gsd/feature-plans/` execution surface that maps future work to real repo seams, current export evidence, and milestone drafts so downstream agents can execute without re-inventing scope.
**Demo:** The repo contains `.gsd/feature-plans/README.md` plus seven canonical feature-plan folders (`track-a-prediction`, `track-b-surfacing`, `track-c-monitoring`, `track-d-onboarding`, `track-e-accountability`, `showcase-system`, `multimodal-experiments`), and each folder includes a repo-grounded `FEATURE_PLAN.md`, a `sprints/SPRINT-01-*/SPRINT.md`, and a phase doc that point to concrete inputs, commands, blockers, and milestone crosswalks.

## Active Requirement Coverage

- `R003` (owner): create distinct feature-plan folders with sprint/phase breakdowns detailed enough for downstream implementation agents to execute against real repo paths, current evidence exports, and future milestone boundaries.
- `R004` (supporting boundary only): reserve stable showcase/intern-planning surfaces by pointing to `CoWork Planning/yelp_project/docs_agent/AGENTS.md` and `CoWork Planning/yelp_project/docs/intern/README.md`, without absorbing S04's narrative-writing work into this slice.

## Decomposition Rationale

This slice is contract-first because the biggest planning risk is structural drift. If executors start drafting feature docs before the root convention and verification surface are locked, every later plan can pick a different naming scheme, cross-link style, or scope boundary. T01 therefore defines the canonical `.gsd/feature-plans/` contract and a pytest-backed structure checker before any feature content is written.

The next risk is re-scoping pressure inside the track work. The repo's real ownership seams are already split by Track A through Track E, and S01/S02 produced stable evidence surfaces and blocker truth that the plans must inherit. T02 through T04 therefore author paired feature plans around those natural seams so each task stays within one context window while still producing real, agent-consumable execution docs.

The final risk is overpromising future work that does not yet exist in code. T05 closes the slice with the optional multimodal lane and the full regression suite so the planning layer explicitly distinguishes live repo assets from future targets, keeps multimodal work off the critical path, and leaves S04 a stable place to write the trust narrative and intern-explainer workflow.

## Must-Haves

- `.gsd/feature-plans/README.md` defines the canonical feature-plan slugs, file/folder naming convention, required cross-links to milestone drafts and export evidence, and the rule that future target folders must be labeled as future rather than implied to exist.
- Seven feature-plan folders exist under `.gsd/feature-plans/`, each with a top-level `FEATURE_PLAN.md`, at least one sprint subfolder, and at least one phase doc containing concrete repo paths, evidence inputs, commands, verification, exit criteria, and blockers.
- Track-specific constraints remain visible in planning: Track A temporal/as-of rules, Track B snapshot-only framing, Track C drift/monitoring framing, Track D's dependency on `outputs/tables/track_a_s5_candidate_splits.parquet`, and Track E's upstream-model dependency.
- Showcase and multimodal plans are grounded in `outputs/exports/eda/` plus `M004`/`M005` drafts, while reserving S04-owned narrative/intern workflow surfaces instead of pretending the website or multimodal implementation already exists.
- `tests/test_feature_plan_architecture.py` proves the root index, required folders/files, and critical content references so empty shells or scope drift fail mechanically.

## Proof Level

- This slice proves: contract
- Real runtime required: no
- Human/UAT required: no

## Verification

- `python -m pytest tests/test_feature_plan_architecture.py`
- `python - <<'PY'
from pathlib import Path
root = Path('.gsd/feature-plans')
feature_plans = sorted(root.glob('*/FEATURE_PLAN.md'))
sprints = sorted(root.glob('*/sprints/*/SPRINT.md'))
phases = sorted(root.glob('*/sprints/*/phases/*.md'))
assert len(feature_plans) == 7, [p.as_posix() for p in feature_plans]
assert len(sprints) == 7, [p.as_posix() for p in sprints]
assert len(phases) == 7, [p.as_posix() for p in phases]
PY`
- `python - <<'PY'
from pathlib import Path
import json
root = Path('.gsd/feature-plans')
expected = [
    'track-a-prediction',
    'track-b-surfacing',
    'track-c-monitoring',
    'track-d-onboarding',
    'track-e-accountability',
    'showcase-system',
    'multimodal-experiments',
]
status = {
    slug: {
        'feature_plan': (root / slug / 'FEATURE_PLAN.md').exists(),
        'sprint_docs': sorted(
            path.relative_to(root).as_posix()
            for path in (root / slug).glob('sprints/*/SPRINT.md')
        ),
        'phase_docs': sorted(
            path.relative_to(root).as_posix()
            for path in (root / slug).glob('sprints/*/phases/*.md')
        ),
    }
    for slug in expected
}
print(json.dumps(status, indent=2, sort_keys=True))
PY`

## Observability / Diagnostics

- `.gsd/feature-plans/README.md` is the human-readable root status surface; future agents can inspect it first to confirm the canonical slug list, naming contract, and the evidence/milestone cross-link rule before authoring any feature plan content.
- `tests/test_feature_plan_architecture.py` is the mechanical drift harness; failures should identify whether the breakage is in the root index, slug inventory, naming convention, or later feature-specific content.
- The verification inventory command prints per-slug presence for `FEATURE_PLAN.md`, sprint docs, and phase docs so an incomplete slice fails with an inspectable missing-surface map instead of only a count mismatch.
- All planning docs must stay aggregate-safe: no raw review text, no copied analytical storage artifacts, and no claims that nonexistent runtime surfaces already exist.

## Integration Closure

- Upstream surfaces consumed: `outputs/exports/eda/manifest.json`, `outputs/exports/eda/EXPORT_CONTRACT.md`, `outputs/tables/eda_command_checklist.md`, `outputs/tables/track_a_s5_candidate_splits.parquet`, `src/eda/track_a/`, `src/eda/track_b/`, `src/eda/track_c/`, `src/eda/track_d/`, `src/eda/track_e/`, `.gsd/milestones/M002-c1uww6/M002-c1uww6-CONTEXT-DRAFT.md`, `.gsd/milestones/M003-rdpeu4/M003-rdpeu4-CONTEXT-DRAFT.md`, `.gsd/milestones/M004-fjc2zy/M004-fjc2zy-CONTEXT-DRAFT.md`, `.gsd/milestones/M005-i0a235/M005-i0a235-CONTEXT-DRAFT.md`
- New wiring introduced in this slice: `.gsd/feature-plans/README.md` becomes the root index for long-lived execution planning, each feature folder becomes an agent entry surface, and `tests/test_feature_plan_architecture.py` becomes the mechanical guardrail against planning drift.
- What remains before the milestone is truly usable end-to-end: S04 still needs to write the trust-marketplace narrative and intern-explainer workflow into the reserved surfaces, and S05 still needs to verify the evidence, planning, and narrative layers together.

## Tasks

- [x] **T01: Lock the feature-plan root contract and verification harness** `est:45m`
  - Why: Later feature plans will drift unless the root naming convention, boundary rules, and regression surface are defined first.
  - Files: `.gsd/feature-plans/README.md`, `tests/test_feature_plan_architecture.py`, `.gsd/milestones/M002-c1uww6/M002-c1uww6-CONTEXT-DRAFT.md`, `outputs/exports/eda/manifest.json`
  - Do: Create the root feature-plan index with the seven canonical slugs, required doc pattern, evidence/milestone cross-link rules, and S04 boundary notes; add the first pytest coverage for the root index and naming convention so later tasks extend one verified structure instead of inventing their own.
  - Verify: `python -m pytest tests/test_feature_plan_architecture.py -k "root_index"`
  - Done when: the repo has a stable `.gsd/feature-plans/README.md` contract and targeted root-index tests pass.
- [x] **T02: Author Track A and Track B execution plans** `est:1h 15m`
  - Why: Tracks A and B are the first downstream modeling lanes and need concrete, constraint-aware execution docs rooted in the current evidence bundle.
  - Files: `.gsd/feature-plans/track-a-prediction/FEATURE_PLAN.md`, `.gsd/feature-plans/track-a-prediction/sprints/SPRINT-01-baseline-modeling/SPRINT.md`, `.gsd/feature-plans/track-a-prediction/sprints/SPRINT-01-baseline-modeling/phases/PHASE-01-temporal-baseline-contract.md`, `.gsd/feature-plans/track-b-surfacing/FEATURE_PLAN.md`, `.gsd/feature-plans/track-b-surfacing/sprints/SPRINT-01-snapshot-ranking-baseline/SPRINT.md`, `.gsd/feature-plans/track-b-surfacing/sprints/SPRINT-01-snapshot-ranking-baseline/phases/PHASE-01-snapshot-baseline-contract.md`, `tests/test_feature_plan_architecture.py`
  - Do: Write Track A and Track B feature plans that cite the export manifests, launcher checklist, repo seams, and M002 draft; make Track A explicitly as-of/temporal and Track B explicitly snapshot-only; add one sprint folder and one phase doc per feature with commands, target files, blockers, and exit criteria; extend tests for both plans.
  - Verify: `python -m pytest tests/test_feature_plan_architecture.py -k "track_a or track_b"`
  - Done when: Track A and Track B each have agent-ready plan/sprint/phase docs and targeted pytest assertions pass.
- [x] **T03: Author Track C and Track D execution plans** `est:1h 15m`
  - Why: The monitoring and cold-start lanes have the most fragile framing constraints, especially Track D's dependency on Track A Stage 5.
  - Files: `.gsd/feature-plans/track-c-monitoring/FEATURE_PLAN.md`, `.gsd/feature-plans/track-c-monitoring/sprints/SPRINT-01-drift-baseline/SPRINT.md`, `.gsd/feature-plans/track-c-monitoring/sprints/SPRINT-01-drift-baseline/phases/PHASE-01-drift-signal-baseline.md`, `.gsd/feature-plans/track-d-onboarding/FEATURE_PLAN.md`, `.gsd/feature-plans/track-d-onboarding/sprints/SPRINT-01-cold-start-baseline/SPRINT.md`, `.gsd/feature-plans/track-d-onboarding/sprints/SPRINT-01-cold-start-baseline/phases/PHASE-01-candidate-split-gate.md`, `tests/test_feature_plan_architecture.py`
  - Do: Write Track C and Track D plans that preserve Track C's drift/monitoring framing and keep Track D visibly blocked on `outputs/tables/track_a_s5_candidate_splits.parquet`; distinguish current repo assets from future modeling targets; add sprint/phase docs with commands, verification, and blocker handling; extend tests for both plans.
  - Verify: `python -m pytest tests/test_feature_plan_architecture.py -k "track_c or track_d"`
  - Done when: Track C and Track D docs make their constraints executable for a fresh agent and the targeted pytest checks pass.
- [x] **T04: Author Track E and showcase-system execution plans** `est:1h 15m`
  - Why: The fairness/audit lane and the later local showcase need explicit handoff plans, but they must stay anchored to upstream models and export surfaces rather than invented app code.
  - Files: `.gsd/feature-plans/track-e-accountability/FEATURE_PLAN.md`, `.gsd/feature-plans/track-e-accountability/sprints/SPRINT-01-audit-target-selection/SPRINT.md`, `.gsd/feature-plans/track-e-accountability/sprints/SPRINT-01-audit-target-selection/phases/PHASE-01-upstream-model-gate.md`, `.gsd/feature-plans/showcase-system/FEATURE_PLAN.md`, `.gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/SPRINT.md`, `.gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/phases/PHASE-01-export-driven-experience-map.md`, `tests/test_feature_plan_architecture.py`
  - Do: Write Track E as an upstream-model fairness/audit lane tied to M003 rather than a standalone predictor, and write the showcase-system plan as an export-driven local experience tied to M004; reserve the trust-narrative and intern-explainer surfaces by citing existing prior-art docs without drafting S04 content; extend tests for both plans.
  - Verify: `python -m pytest tests/test_feature_plan_architecture.py -k "track_e or showcase"`
  - Done when: Track E and showcase-system each have repo-grounded plan/sprint/phase docs and the targeted pytest checks pass.
- [x] **T05: Add the multimodal lane and close full architecture verification** `est:1h`
  - Why: The final plan set must show optional future-work sequencing without letting multimodal exploration dilute the core semester path, and the full structure needs one mechanical closing proof.
  - Files: `.gsd/feature-plans/multimodal-experiments/FEATURE_PLAN.md`, `.gsd/feature-plans/multimodal-experiments/sprints/SPRINT-01-scope-gate/SPRINT.md`, `.gsd/feature-plans/multimodal-experiments/sprints/SPRINT-01-scope-gate/phases/PHASE-01-expand-or-stop-decision.md`, `.gsd/feature-plans/README.md`, `tests/test_feature_plan_architecture.py`
  - Do: Add the multimodal feature plan as a non-critical-path scope gate tied to M005, update the root README with the final cross-feature index and dependency map, expand the pytest file to assert all seven features plus the critical special-case references, and run the full architecture verification.
  - Verify: `python -m pytest tests/test_feature_plan_architecture.py`
  - Done when: the seventh feature plan exists, the root index reflects the full architecture, and the complete pytest file passes.

## Files Likely Touched

- `.gsd/feature-plans/README.md`
- `.gsd/feature-plans/track-a-prediction/FEATURE_PLAN.md`
- `.gsd/feature-plans/track-d-onboarding/FEATURE_PLAN.md`
- `.gsd/feature-plans/showcase-system/FEATURE_PLAN.md`
- `.gsd/feature-plans/multimodal-experiments/FEATURE_PLAN.md`
- `tests/test_feature_plan_architecture.py`
