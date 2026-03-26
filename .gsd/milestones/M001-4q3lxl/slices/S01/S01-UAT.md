# UAT — S01: All-track EDA artifact census and gap closure

## UAT Goal
Confirm that the repo exposes a truthful, dispatcher-derived all-track EDA completion surface, that final Track A–E summary markdowns exist, and that partial-repo fallbacks are explicit rather than silent.

## Preconditions
- Run from the repo root of this worktree.
- Python commands must resolve in the shell used for verification.
- The current stripped worktree is allowed to be missing most intermediate EDA stage outputs.
- Expected files under test:
  - `scripts/report_eda_completeness.py`
  - `outputs/tables/track_a_s8_eda_summary.md`
  - `outputs/tables/track_b_s8_eda_summary.md`
  - `outputs/tables/track_c_s9_eda_summary.md`
  - `outputs/tables/track_d_s9_eda_summary.md`
  - `outputs/tables/track_e_s9_eda_summary.md`
  - `outputs/tables/eda_artifact_census.md`
  - `outputs/tables/eda_artifact_census.csv`
  - `outputs/tables/eda_command_checklist.md`

## Test Case 1 — Regression suite for the S01 contract
**Purpose:** Prove the dispatcher contract, repaired summary writers, and reporter are covered by tests.

### Steps
1. Run:
   ```bash
   python -m pytest tests/test_pipeline_dispatcher_all_tracks.py tests/test_track_a_summary_report.py tests/test_track_b_summary_report.py tests/test_track_d_summary_report.py tests/test_eda_artifact_census_report.py
   ```

### Expected Outcomes
1. Pytest exits with code `0`.
2. All tests pass.
3. Failures would indicate drift in at least one of these areas:
   - dispatcher-derived Track A–E terminal summary contract
   - Track A/B/D partial-repo fallback summary behavior
   - census/checklist reporter output semantics

## Test Case 2 — Materialize the completeness artifacts
**Purpose:** Confirm the main S01 command works end-to-end in the current worktree.

### Steps
1. Run:
   ```bash
   python scripts/report_eda_completeness.py
   ```
2. Verify the output files exist:
   ```bash
   test -f outputs/tables/track_a_s8_eda_summary.md
   test -f outputs/tables/track_b_s8_eda_summary.md
   test -f outputs/tables/track_c_s9_eda_summary.md
   test -f outputs/tables/track_d_s9_eda_summary.md
   test -f outputs/tables/track_e_s9_eda_summary.md
   test -f outputs/tables/eda_artifact_census.md
   test -f outputs/tables/eda_artifact_census.csv
   test -f outputs/tables/eda_command_checklist.md
   ```

### Expected Outcomes
1. The reporter exits with code `0`.
2. All eight file existence checks pass.
3. The command prints the three reporter output paths and a repaired-summary summary line.

## Test Case 3 — Census status vocabulary and live completeness truth
**Purpose:** Confirm the census exposes honest status labels instead of implying full completion.

### Steps
1. Run:
   ```bash
   rg -n "existing|missing|repaired" outputs/tables/eda_artifact_census.md
   ```
2. Open `outputs/tables/eda_artifact_census.md`.
3. Review the status totals and per-artifact rows.

### Expected Outcomes
1. `rg` finds the three status labels in the census markdown.
2. The census includes rows for Track A–E summary stages.
3. The current stripped worktree truth is visible: final summary artifacts exist, while many intermediate stage artifacts are still marked `missing`.
4. The report does **not** imply that missing upstream parquet/PNG outputs were regenerated.

## Test Case 4 — Canonical command checklist and Track D blocker visibility
**Purpose:** Confirm downstream users can see the real brownfield launcher order and Track D dependency.

### Steps
1. Run:
   ```bash
   rg -n "python scripts/run_pipeline.py --approach track_d|track_a_s5_candidate_splits.parquet" outputs/tables/eda_command_checklist.md
   ```
2. Open `outputs/tables/eda_command_checklist.md`.
3. Review the ordering of Track A, B, C, D, and E.

### Expected Outcomes
1. The checklist shows canonical commands in Track A → Track B → Track C → Track D → Track E order.
2. Track D includes an explicit note that it is blocked until `outputs/tables/track_a_s5_candidate_splits.parquet` exists.
3. The checklist tells the operator to run Track A through Stage 5 before Track D.

## Test Case 5 — Track D fallback summary is explicit about missing upstream inputs
**Purpose:** Confirm Track D summary regeneration is honest when Track A Stage 5 is absent.

### Steps
1. Run:
   ```bash
   rg -n "missing upstream inputs|track_a_s5_candidate_splits.parquet|Run Track A through Stage 5" outputs/tables/track_d_s9_eda_summary.md outputs/tables/eda_command_checklist.md
   ```
2. Open `outputs/tables/track_d_s9_eda_summary.md`.

### Expected Outcomes
1. The Track D summary contains a `Missing Upstream Inputs` section.
2. The summary explicitly names `track_a_s5_candidate_splits.parquet`.
3. The summary tells the operator to run Track A through Stage 5 before Track D.
4. The summary states that placeholder dates were **not** used as evidence of materialized splits.

## Test Case 6 — Track B summary degrades safely when snapshot metadata is unavailable
**Purpose:** Confirm Track B summary regeneration no longer hard-fails when snapshot metadata is missing.

### Steps
1. Open `outputs/tables/track_b_s8_eda_summary.md`.
2. Review the metadata header and fallback section.

### Expected Outcomes
1. The summary file exists and is readable.
2. If snapshot metadata is unavailable in the worktree used to generate the file, the summary shows:
   - `Snapshot reference date: missing`
   - `Dataset release tag: missing`
   - a `Metadata Fallback` section explaining that `data/curated/snapshot_metadata.json` was missing or unreadable
3. The summary does not crash generation or silently fabricate snapshot metadata.

## Edge Case Checks

### Edge Case A — Steady-state rerun should stay honest
**Steps**
1. Re-run:
   ```bash
   python scripts/report_eda_completeness.py
   ```
2. Open `outputs/tables/eda_artifact_census.md`.

**Expected Outcomes**
1. Existing final summaries remain marked `existing` on rerun.
2. Missing upstream artifacts remain `missing`.
3. The reporter does not relabel already-present summaries as `repaired` on every invocation.

### Edge Case B — No raw review text should appear in the S01 handoff artifacts
**Steps**
1. Review the generated markdown outputs listed in the Preconditions section.
2. Cross-check that they only contain aggregate-safe summaries, artifact-status language, dependency notes, and recommendations.

**Expected Outcomes**
1. No raw review text snippets appear in the generated handoff artifacts.
2. The outputs are suitable for downstream planning/export work without violating repo governance rules.

## UAT Pass Criteria
- All six core test cases pass.
- Both edge case checks pass.
- The current worktree exposes a complete five-track final-summary handoff surface plus truthful census/checklist reporting for downstream slices.
