# S04 UAT — Trust narrative and intern explainer workflow

**Milestone:** M001-4q3lxl  
**Slice:** S04  
**Status:** Completed with contract-level verification

## Purpose

Confirm the showcase planning lane exposes a real, honest, and discoverable content contract for the trust narrative and the intern explainer workflow, while preserving the repo’s internal aggregate-safe export boundary.

## Preconditions

- Export bundle exists under `outputs/exports/eda/`.
- Canonical showcase planning docs exist under `.gsd/feature-plans/showcase-system/`.
- The repo uses the S04 docs below as the content contract:
  - `.gsd/feature-plans/showcase-system/TRUST_NARRATIVE.md`
  - `.gsd/feature-plans/showcase-system/INTERN_EXPLAINER_WORKFLOW.md`

## Automated Contract Checks

Run:

```bash
python -m pytest tests/test_trust_narrative_workflow.py -q
```

**Expected:** pass.

This verifies:

- both S04-owned docs exist
- the trust narrative contains the five trust functions
- the docs cite export-grounded evidence and retain `internal` + `aggregate-safe` language
- the canonical feature/sprint/phase docs link back to the S04 docs
- Track D blocker truth and Track E metadata-only validity evidence remain visible through the export manifests

## Human Review Checklist

### 1. Discoverability from the canonical showcase lane

Open these files:

- `.gsd/feature-plans/showcase-system/FEATURE_PLAN.md`
- `.gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/SPRINT.md`
- `.gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/phases/PHASE-01-export-driven-experience-map.md`

Check:

- [ ] Each points to `TRUST_NARRATIVE.md`.
- [ ] Each points to `INTERN_EXPLAINER_WORKFLOW.md`.
- [ ] Each preserves the local-hosted/internal export-driven boundary.
- [ ] None implies live `.parquet` or DuckDB reads for the future showcase.

### 2. Trust narrative honesty

Open `.gsd/feature-plans/showcase-system/TRUST_NARRATIVE.md`.

Check:

- [ ] The story spine is prediction → surfacing → monitoring → onboarding → accountability.
- [ ] The narrative maps those functions to Tracks A-E explicitly.
- [ ] The doc cites `outputs/exports/eda/manifest.json` and `outputs/exports/eda/EXPORT_CONTRACT.md`.
- [ ] It preserves the current-state truth `existing=6` and `missing=109`.
- [ ] It names the Track D blocker path `outputs/tables/track_a_s5_candidate_splits.parquet`.
- [ ] It does not overstate Track E evidence beyond metadata-only validity summaries.

### 3. Intern explainer workflow usefulness

Open `.gsd/feature-plans/showcase-system/INTERN_EXPLAINER_WORKFLOW.md`.

Check:

- [ ] It says when to invoke the explainer-style agent.
- [ ] It names the read-first inputs.
- [ ] It defines outputs, not just general goals.
- [ ] It requires glossary/plain-language explanation patterns.
- [ ] It preserves the no-raw-review-text rule.
- [ ] It references `CoWork Planning/yelp_project/docs_agent/AGENTS.md` and `CoWork Planning/yelp_project/docs/intern/README.md` as prior art.

### 4. Governance boundary

Inspect:

- `outputs/exports/eda/manifest.json`
- `outputs/exports/eda/tracks/track_d/manifest.json`
- `outputs/exports/eda/tracks/track_e/manifest.json`

Check:

- [ ] Root manifest `scope` is `internal`.
- [ ] Root manifest `safety_boundary` is `aggregate-safe`.
- [ ] Track D still surfaces the blocker through `blocked_by`.
- [ ] Track E still surfaces validity through `metadata_summaries` with `export_mode: metadata_only`.

## Failure Signals

Treat S04 as regressed if any of these occur:

- `tests/test_trust_narrative_workflow.py` fails
- canonical showcase docs stop linking to the S04 docs
- the trust narrative loses one of the five trust functions or stops citing export truth
- the explainer workflow no longer defines invocation triggers, inputs, outputs, and guardrails
- the planning docs imply live parquet/DuckDB reads or otherwise violate the export-driven boundary
- any S04 planning doc introduces raw review text or public-hosting assumptions

## Result

**Pass criteria:** all automated checks pass and the human checklist confirms the S04 docs are discoverable, export-grounded, intern-usable, and governance-safe.
