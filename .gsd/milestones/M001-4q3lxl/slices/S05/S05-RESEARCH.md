# S05 — Research

**Date:** 2026-03-22

## Summary

S05 is an **integration slice**, not a new architecture slice. It supports the already-validated milestone requirements **R001**, **R002**, **R003**, and **R013** by proving the four completed surfaces still agree in one local pass:

- S01 summary/census/checklist outputs
- S02 export bundle outputs
- S03 feature-plan architecture
- S04 trust narrative + intern explainer workflow

There is also one important cleanup gap: **`R004` is still marked active in `.gsd/REQUIREMENTS.md` even though the S04 docs and regression test now exist and pass.** In addition, **`.gsd/milestones/M001-4q3lxl/slices/S04/S04-SUMMARY.md` and `S04-UAT.md` are still doctor-created placeholders.** If S05 is meant to make the milestone truly handoff-ready, those placeholders are now part of the integration surface and should be treated as real drift, not ignored.

The good news: the repo already has almost all the verification machinery needed. I confirmed the main slice-level checks pass right now:

- `python -m pytest tests/test_package_eda_exports.py tests/test_feature_plan_architecture.py tests/test_trust_narrative_workflow.py -q` → **14 passed**
- `python scripts/report_eda_completeness.py` → steady-state `existing=6 missing=109 repaired=0`
- `python scripts/package_eda_exports.py` → steady-state `existing=6 missing=109 emitted_files=25 figures=6`, with Track D blocker and Track E metadata-only validity evidence preserved

Primary recommendation: **reuse the existing S01/S02/S03/S04 commands and tests, add one thin milestone-level pytest harness for cross-surface agreement, and treat placeholder slice artifacts / stale requirement status as part of the integrated handoff check.** This follows loaded skill guidance from:

- `coding-standards`: prefer DRY/KISS; do not invent a second verifier when existing scripts already materialize truth
- `test`: add a focused pytest file that matches repo convention instead of shell-only checking
- `verification-loop`: finish with explicit verification gates, not prose-only confidence
- `debug-like-expert`: verify actual emitted files and current manifest values; do not assume prior slice summaries are enough
- `article-writing`: lead milestone handoff docs with concrete observable state (`existing=6`, `missing=109`, Track D blocker, metadata-only Track E evidence)

## Recommendation

Implement S05 as a **thin milestone integration layer**, not as a new export/planning subsystem.

Recommended shape:

- add `tests/test_m001_handoff_verification.py`
- add `.gsd/milestones/M001-4q3lxl/slices/S05/S05-PLAN.md`
- add `.gsd/milestones/M001-4q3lxl/slices/S05/S05-UAT.md`
- later write `.gsd/milestones/M001-4q3lxl/slices/S05/S05-SUMMARY.md`
- repair `.gsd/milestones/M001-4q3lxl/slices/S04/S04-SUMMARY.md`
- repair `.gsd/milestones/M001-4q3lxl/slices/S04/S04-UAT.md`
- likely update `.gsd/REQUIREMENTS.md` so `R004` reflects the now-verified S04 surface

What S05 should prove:

1. **S01 still materializes honest table-layer handoff truth**
   - the five track summary markdowns exist
   - `outputs/tables/eda_artifact_census.csv` and `eda_command_checklist.md` exist
   - rerunning `scripts/report_eda_completeness.py` preserves steady-state honesty (`repaired=0` on this worktree is expected)

2. **S02 still materializes honest export-layer truth**
   - `outputs/exports/eda/manifest.json`, `manifest.csv`, `EXPORT_CONTRACT.md`, overview PNG, and per-track exports exist
   - root manifest still says `scope=internal`, `safety_boundary=aggregate-safe`
   - Track D `blocked_by` and Track E `metadata_only` validity evidence are still present
   - no forbidden `.parquet`, `.ndjson`, or copied `.log` files exist under the bundle

3. **S03/S04 still expose a usable planning + narrative handoff**
   - `.gsd/feature-plans/` still has the seven canonical lanes
   - showcase docs still point to `TRUST_NARRATIVE.md` and `INTERN_EXPLAINER_WORKFLOW.md`
   - the trust narrative still uses the five trust functions and current-state honesty
   - the intern workflow still preserves plain-language / glossary-first / no-raw-text guardrails

4. **Milestone completion artifacts are not fake-complete**
   - S04 placeholder summary/UAT should be replaced or explicitly fail the integrated verifier
   - `R004` should not remain stale if the dedicated S04 pytest contract is now passing

## Implementation Landscape

### Key Existing Verification Surfaces

- `scripts/report_eda_completeness.py`
  - canonical S01 regeneration/check command
  - writes `outputs/tables/eda_artifact_census.md`, `eda_artifact_census.csv`, `eda_command_checklist.md`
  - current steady-state output observed: `existing=6 missing=109 repaired=0`

- `scripts/package_eda_exports.py`
  - canonical S02 regeneration/check command
  - rebuilds `outputs/exports/eda/` from dispatcher contract + census/checklist/summary inputs
  - current steady-state output observed: `existing=6 missing=109 emitted_files=25 figures=6`
  - **important:** it deletes and recreates `outputs/exports/eda/` on each run; do not run it concurrently

- `tests/test_pipeline_dispatcher_all_tracks.py`
  - verifies dispatcher-owned summary contract and Track D blocker metadata

- `tests/test_eda_artifact_census_report.py`
  - verifies S01 completeness reporter behavior and checklist/blocker semantics

- `tests/test_package_eda_exports.py`
  - verifies S02 bundle generation, governance boundary, copied allowlist, PNG synthesis, and missing-input failures

- `tests/test_feature_plan_architecture.py`
  - verifies exact seven-lane planning architecture and showcase guardrails

- `tests/test_trust_narrative_workflow.py`
  - verifies S04 trust narrative/workflow docs plus showcase cross-links and export-boundary markers

### Current Honest Runtime State

I verified these current facts directly:

- `python scripts/report_eda_completeness.py`
  - all five summary markdowns already exist
  - rewrites the census/checklist
  - reports `existing=6 missing=109 repaired=0`

- `python scripts/package_eda_exports.py`
  - rewrites the bundle root
  - reports `emitted_files=25` and `figures=6`
  - keeps `outputs/tables/track_a_s5_candidate_splits.parquet` visible as the Track D blocker
  - keeps Track E validity evidence as metadata-only with summary `No findings detected.`

- `python -m pytest tests/test_package_eda_exports.py tests/test_feature_plan_architecture.py tests/test_trust_narrative_workflow.py -q`
  - passed with **14/14**

### Important Gaps S05 Should Not Miss

- `.gsd/milestones/M001-4q3lxl/slices/S04/S04-SUMMARY.md` is still a **doctor recovery placeholder**.
- `.gsd/milestones/M001-4q3lxl/slices/S04/S04-UAT.md` is still a **doctor recovery placeholder**.
- `.gsd/REQUIREMENTS.md` still lists **R004 as active**, even though `tests/test_trust_narrative_workflow.py` now passes and the canonical S04 docs exist.

These are not cosmetic issues if the milestone goal is “M002 can start without first rebuilding context.” A fresh agent reading milestone artifacts should not land on placeholder files or stale requirement state.

## Build Order

1. **Define the integrated contract first.**
   Create `S05-PLAN.md` and state the exact local verification pass: S01 CLI → S02 CLI → integrated pytest → milestone artifact cleanup checks.

2. **Add the thin milestone-level pytest harness.**
   `tests/test_m001_handoff_verification.py` should not re-test every slice in depth. It should only assert cross-surface agreement and milestone-handoff cleanliness.

3. **Repair stale milestone artifacts.**
   Replace the doctor placeholders in `S04-SUMMARY.md` and `S04-UAT.md` with real compressed artifacts derived from `T01-SUMMARY.md`, `T02-SUMMARY.md`, and the actual passing commands.

4. **Resolve requirement-state drift.**
   If S04 verification is rerun successfully during S05, update `R004` from active to validated with concrete proof.

5. **Run the integrated pass sequentially and capture outputs.**
   Reporter first, packager second, tests third. Do not parallelize packager invocations.

## Verification Approach

Recommended integrated sequence:

1. `python scripts/report_eda_completeness.py`
2. `python scripts/package_eda_exports.py`
3. `python -m pytest tests/test_pipeline_dispatcher_all_tracks.py tests/test_eda_artifact_census_report.py tests/test_feature_plan_architecture.py tests/test_trust_narrative_workflow.py tests/test_m001_handoff_verification.py -q`
4. `python - <<'PY'
from pathlib import Path
for path in [
    Path('.gsd/milestones/M001-4q3lxl/slices/S04/S04-SUMMARY.md'),
    Path('.gsd/milestones/M001-4q3lxl/slices/S04/S04-UAT.md'),
]:
    text = path.read_text(encoding='utf-8')
    assert 'Recovery placeholder' not in text
    assert 'doctor-created placeholder' not in text
print('milestone handoff docs are not placeholders')
PY`
5. Optional final integrity snippet:
   - read `outputs/exports/eda/manifest.json`
   - assert `status_totals == {'existing': 6, 'missing': 109}`
   - assert Track D blocker path exact match
   - assert Track E `export_mode == 'metadata_only'`

### What the New Milestone-Level Test Should Cover

`tests/test_m001_handoff_verification.py` should focus on agreement, not duplication:

- S01 outputs exist and their filenames match dispatcher contract
- S02 root manifest points to real exported files and keeps governance markers
- S03 showcase lane still points to S04 docs
- S04 narrative/workflow docs still match root manifest facts (`existing=6`, `missing=109`, Track D blocker, metadata-only Track E evidence)
- no S04 placeholder summary/UAT text remains
- optional: `R004` is no longer left active once integrated verification is complete

## Don’t Hand-Roll

| Problem | Existing Surface | Why Reuse It |
|---|---|---|
| S01 truth | `scripts/report_eda_completeness.py` + `tests/test_eda_artifact_census_report.py` | Already owns summary repair/census/checklist semantics. |
| S02 truth | `scripts/package_eda_exports.py` + `tests/test_package_eda_exports.py` | Already owns bundle/governance/PNG semantics. |
| S03 truth | `tests/test_feature_plan_architecture.py` | Already verifies the seven-lane architecture and showcase guardrails. |
| S04 truth | `tests/test_trust_narrative_workflow.py` | Already verifies the trust narrative/workflow contract and showcase cross-links. |
| Integrated proof | one thin new pytest file | Enough to catch cross-slice drift without inventing a second orchestration subsystem. |

I do **not** recommend adding a heavy new `scripts/verify_m001_handoff.py` unless the planner wants a one-command operator UX badly enough to justify another maintenance surface. The current repo already has the right scripts; S05 mainly needs composition plus milestone-artifact cleanup.

## Constraints

- S05 supports validated `R001`, `R002`, `R003`, and `R013`; it should not silently weaken any of their already-proven contracts.
- `R004` is the one still-active requirement adjacent to this work; S05 should at least account for its status drift if S04 proof is rerun.
- The packager is destructive to `outputs/exports/eda/`; do not run concurrent bundle builds.
- Stay inside aggregate-safe/internal-only boundaries everywhere.
- Use current observed values, not aspirational ones. On this worktree, steady-state truth is `existing=6`, `missing=109`, not a repaired or fully complete artifact set.

## Common Pitfalls

- **Expecting `repaired > 0` on steady-state reruns.** In this worktree, S01 currently reports `repaired=0`; that is correct after summaries already exist.
- **Parallelizing bundle verification.** `scripts/package_eda_exports.py` wipes the bundle root.
- **Re-testing every slice in full instead of checking agreement.** S05 should be thin and integrative.
- **Ignoring the S04 placeholder files because tests still pass.** They are part of the actual milestone handoff surface.
- **Leaving `R004` stale.** The requirement file should match the passing S04 contract if the integrated pass confirms it.

## Open Risks

- The stripped worktree still has many missing upstream analytical artifacts; S05 can only prove honest handoff, not magically remove those missing states.
- If planners choose not to repair the S04 placeholder artifacts, milestone completion may still feel incomplete even with green tests.
- If S05 over-rotates into new scripting instead of composition, it may create maintenance drift where none is needed.

## Skills Discovered

Installed skills already cover the core work:

- `test`
- `verification-loop`
- `coding-standards`
- `debug-like-expert`
- `article-writing`

No additional external skill search looked necessary for this slice because the work is repo-local Python/pytest/doc-integration rather than a new external technology.
