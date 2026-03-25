# UAT — S03: Agent-ready planning architecture

## UAT Goal
Confirm that the repo exposes a stable `.gsd/feature-plans/` execution surface with seven canonical lanes, that each lane contains an agent-ready feature plan plus first sprint/phase docs, and that the planning architecture preserves the real repo/evidence/blocker boundaries needed for downstream implementation.

## Preconditions
- Run from the repo root of this worktree.
- S01 and S02 surfaces already exist, especially:
  - `outputs/exports/eda/manifest.json`
  - `outputs/exports/eda/EXPORT_CONTRACT.md`
  - `outputs/tables/eda_command_checklist.md`
- The `.gsd/feature-plans/` tree has been populated by S03.
- The worktree may still be missing many upstream modeling/runtime surfaces; that is expected and part of what the planning docs must describe honestly.

## Test Case 1 — Regression suite for the planning architecture
**Purpose:** Prove the seven-lane planning contract is enforced mechanically.

### Steps
1. Run:
   ```bash
   python -m pytest tests/test_feature_plan_architecture.py
   ```

### Expected Outcomes
1. Pytest exits with code `0`.
2. All 7 tests pass.
3. The suite proves at least these behaviors:
   - only the seven canonical feature slugs exist under `.gsd/feature-plans/`
   - the root README documents the required layout and cross-link rules
   - every lane cites repo paths, export evidence, and milestone drafts
   - lane-specific guardrails remain present for Track A, B, D, E, showcase, and multimodal special cases

## Test Case 2 — Exact architecture inventory is complete
**Purpose:** Confirm the repo contains the full required surface, not partial or placeholder planning.

### Steps
1. Run:
   ```bash
   python - <<'PY'
   from pathlib import Path
   root = Path('.gsd/feature-plans')
   feature_plans = sorted(root.glob('*/FEATURE_PLAN.md'))
   sprints = sorted(root.glob('*/sprints/*/SPRINT.md'))
   phases = sorted(root.glob('*/sprints/*/phases/*.md'))
   assert len(feature_plans) == 7, [p.as_posix() for p in feature_plans]
   assert len(sprints) == 7, [p.as_posix() for p in sprints]
   assert len(phases) == 7, [p.as_posix() for p in phases]
   print('counts_ok', len(feature_plans), len(sprints), len(phases))
   PY
   ```
2. Run the per-slug inventory diagnostic:
   ```bash
   python - <<'PY'
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
   PY
   ```

### Expected Outcomes
1. The count check prints `counts_ok 7 7 7`.
2. The inventory output lists all seven canonical slugs.
3. Each slug reports:
   - `feature_plan: true`
   - one sprint doc
   - one phase doc
4. No extra root-level planning slugs are required for slice completion.

## Test Case 3 — Root README defines the canonical planning contract
**Purpose:** Confirm future agents have one authoritative human-readable architecture surface.

### Steps
1. Open `.gsd/feature-plans/README.md`.
2. Review these sections:
   - `Canonical Feature Slugs`
   - `Required Layout`
   - `Final Architecture Index`
   - `Cross-Feature Dependency Map`
   - `Planning Boundaries`
   - `S03 vs. S04 Boundary`
   - `Authoring Rule for Downstream Agents`

### Expected Outcomes
1. The README lists exactly these seven slugs:
   - `track-a-prediction`
   - `track-b-surfacing`
   - `track-c-monitoring`
   - `track-d-onboarding`
   - `track-e-accountability`
   - `showcase-system`
   - `multimodal-experiments`
2. The required layout explicitly includes `FEATURE_PLAN.md`, `SPRINT.md`, and `PHASE-01-<slug>.md`.
3. The README points future work to:
   - `outputs/exports/eda/manifest.json`
   - `outputs/exports/eda/EXPORT_CONTRACT.md`
   - milestone draft paths under `.gsd/milestones/`
4. The README explicitly says future targets must be labeled as future.
5. The README reserves S04-owned narrative/intern writing instead of filling it in early.

## Test Case 4 — Track A and Track B plans preserve their modeling framing
**Purpose:** Confirm the two earliest modeling lanes encode the right constraints for M002 executors.

### Steps
1. Open:
   - `.gsd/feature-plans/track-a-prediction/FEATURE_PLAN.md`
   - `.gsd/feature-plans/track-b-surfacing/FEATURE_PLAN.md`
2. In Track A, review:
   - `Planning Guardrails`
   - `Current Evidence Inputs`
   - `Future Target Folders (Future)`
   - `Blockers to Carry Forward`
3. In Track B, review the same sections.
4. Open the first sprint/phase docs for each lane and inspect the `Commands`, `Verification`, and `Exit Criteria` sections.

### Expected Outcomes
1. Track A explicitly preserves **as-of** / **temporal** framing and ties work to `data/curated/review_fact.parquet`.
2. Track A explicitly rejects snapshot-only feature leakage, including banned business/user lifetime fields.
3. Track B explicitly preserves **snapshot-only** / **age-controlled** usefulness ranking framing.
4. Track B explicitly rejects vote-growth or temporal trend framing.
5. Both lanes cite current export manifests, `outputs/tables/eda_command_checklist.md`, and `.gsd/milestones/M002-c1uww6/M002-c1uww6-CONTEXT-DRAFT.md`.
6. Both lanes include concrete future target folders labeled as future, not as existing code.

## Test Case 5 — Track C and Track D plans preserve monitoring and blocker truth
**Purpose:** Confirm S03 did not flatten fragile framing differences across lanes.

### Steps
1. Open:
   - `.gsd/feature-plans/track-c-monitoring/FEATURE_PLAN.md`
   - `.gsd/feature-plans/track-d-onboarding/FEATURE_PLAN.md`
2. In Track C, inspect the mission, guardrails, and first sprint/phase docs.
3. In Track D, inspect the mission, guardrails, and first sprint/phase docs.
4. Search Track D docs for the split dependency:
   ```bash
   rg -n "track_a_s5_candidate_splits.parquet|blocked_by|currently missing locally" .gsd/feature-plans/track-d-onboarding
   ```

### Expected Outcomes
1. Track C is framed as **drift** / **monitoring**, not forecasting.
2. Track C cites current Track C runtime seams such as `drift_detection.py`.
3. Track D keeps `outputs/tables/track_a_s5_candidate_splits.parquet` visible in the feature plan and first phase doc.
4. Track D explicitly says the file is currently missing locally and that the lane is blocked until the upstream artifact is real.
5. Track D preserves D1/D2 cold-start framing and as-of feature constraints.

## Test Case 6 — Track E and showcase-system preserve cross-slice boundaries
**Purpose:** Confirm S03 grounded later lanes without absorbing S04 content or inventing app/runtime surfaces.

### Steps
1. Open:
   - `.gsd/feature-plans/track-e-accountability/FEATURE_PLAN.md`
   - `.gsd/feature-plans/showcase-system/FEATURE_PLAN.md`
2. In Track E, inspect mission, guardrails, and blockers.
3. In showcase-system, inspect mission, guardrails, current gaps, and first implementation checklist.
4. Search the showcase docs for reserved S04 references:
   ```bash
   rg -n "docs_agent/AGENTS.md|docs/intern/README.md|trust-marketplace narrative|DuckDB|parquet" .gsd/feature-plans/showcase-system
   ```

### Expected Outcomes
1. Track E explicitly says it audits a real upstream Track A or Track D model and is **not** a standalone predictor.
2. Track E keeps the first gate on choosing an upstream audit target before fairness-mitigation execution.
3. Showcase-system explicitly treats `outputs/exports/eda/` as the consumption boundary.
4. Showcase-system explicitly says not to query `.parquet` files or DuckDB live.
5. Showcase-system cites `CoWork Planning/yelp_project/docs_agent/AGENTS.md` and `CoWork Planning/yelp_project/docs/intern/README.md` as reserved prior-art references rather than drafting S04 content.
6. Showcase-system does not imply that a website scaffold already exists in the repo.

## Test Case 7 — Multimodal lane stays optional and scope-gated
**Purpose:** Confirm optional future work is planned without displacing the semester-critical path.

### Steps
1. Open `.gsd/feature-plans/multimodal-experiments/FEATURE_PLAN.md`.
2. Review:
   - mission
   - milestone crosswalk
   - planning guardrails
   - current state and gaps
   - first sprint checklist
3. Open:
   - `.gsd/feature-plans/multimodal-experiments/sprints/SPRINT-01-scope-gate/SPRINT.md`
   - `.gsd/feature-plans/multimodal-experiments/sprints/SPRINT-01-scope-gate/phases/PHASE-01-expand-or-stop-decision.md`
4. Search the multimodal lane for gate language:
   ```bash
   rg -n "non-critical-path|expand-or-stop|no current multimodal training path exists in the repo|local GPU|Colab Pro|HPC" .gsd/feature-plans/multimodal-experiments
   ```

### Expected Outcomes
1. The lane is explicitly labeled **non-critical-path**.
2. The first sprint ends in an **expand-or-stop** decision.
3. The docs explicitly say no current multimodal training path exists in the repo.
4. The lane stays tied to `.gsd/milestones/M005-i0a235/M005-i0a235-CONTEXT-DRAFT.md` and downstream context from the export/showcase surfaces.
5. The docs mention compute-accounting paths such as local GPU, Colab Pro, and HPC only as feasibility inputs, not as default required setup.

## Test Case 8 — Phase docs are genuinely agent-executable
**Purpose:** Confirm S03 created usable execution docs rather than descriptive placeholders.

### Steps
1. Run:
   ```bash
   find .gsd/feature-plans -path '*/phases/*.md' | sort
   ```
2. Open each returned phase doc.
3. Confirm each phase doc contains these sections:
   - `## Current Evidence Inputs`
   - `## Commands`
   - `## Verification`
   - `## Exit Criteria`
   - `Future Target Folders (Future)`
4. Spot-check one command per lane against the doc text.

### Expected Outcomes
1. Exactly 7 phase docs are listed.
2. Every phase doc includes the required execution sections.
3. Each doc contains real commands tied to the lane's repo seams.
4. None of the phase docs are empty shells or generic templates.

## Edge Case Checks

### Edge Case A — Planning drift should be diagnosable, not mysterious
**Steps**
1. If the regression suite fails, rerun the per-slug inventory diagnostic from Test Case 2.
2. Compare the failing slug's file presence to the README contract.
3. Inspect the lane docs for missing guardrail language such as `Future Target Folders (Future)` or dropped blocker/milestone references.

**Expected Outcomes**
1. The inventory output makes it clear whether the problem is:
   - missing docs
   - wrong slug/layout
   - dropped required language/cross-links
2. A future agent can repair the lane without inventing a new structure.

### Edge Case B — Reserved S04 surfaces stay reserved
**Steps**
1. Inspect `.gsd/feature-plans/README.md` and `showcase-system/FEATURE_PLAN.md`.
2. Confirm they point to prior-art docs for intern/trust narrative work rather than trying to author the full workflow.

**Expected Outcomes**
1. S03 planning remains architecture-only.
2. S04 still has a clear, unclaimed content boundary to fill.

## UAT Pass Criteria
- All 8 core test cases pass.
- Both edge case checks pass.
- The worktree exposes a stable, inspectable `.gsd/feature-plans/` architecture that downstream agents can use without re-inventing naming, structure, evidence inputs, or blocker truth.
