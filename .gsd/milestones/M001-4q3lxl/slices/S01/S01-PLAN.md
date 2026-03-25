# S01: All-track EDA artifact census and gap closure

**Goal:** Prove, from live repo state, which Track A–E final EDA artifacts exist, which are missing, and which can be repaired into a complete summary set without inventing a second manifest.
**Demo:** Running `python scripts/report_eda_completeness.py` in this worktree creates dispatcher-derived completeness artifacts plus final Track A–E summary markdowns that explicitly report missing upstream inputs instead of silently assuming the repo is complete.

## Must-Haves

- A dispatcher-derived completeness/reporting layer emits a live census and command checklist for Tracks A–E without hardcoding a duplicate artifact manifest.
- Track A, Track B, and Track D final summary generation works in partial repos; Track B no longer hard-fails when `data/curated/snapshot_metadata.json` is absent.
- Regression tests cover the all-track terminal summary contract, the repaired Track A/B/D summary writers, and the new census/reporting entrypoint.
- S01 materializes presentation-ready final summary markdowns for `outputs/tables/track_a_s8_eda_summary.md`, `outputs/tables/track_b_s8_eda_summary.md`, `outputs/tables/track_c_s9_eda_summary.md`, `outputs/tables/track_d_s9_eda_summary.md`, and `outputs/tables/track_e_s9_eda_summary.md` in the current worktree.

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `python -m pytest tests/test_pipeline_dispatcher_all_tracks.py tests/test_track_a_summary_report.py tests/test_track_b_summary_report.py tests/test_track_d_summary_report.py tests/test_eda_artifact_census_report.py`
- `python scripts/report_eda_completeness.py && test -f outputs/tables/track_a_s8_eda_summary.md && test -f outputs/tables/track_b_s8_eda_summary.md && test -f outputs/tables/track_c_s9_eda_summary.md && test -f outputs/tables/track_d_s9_eda_summary.md && test -f outputs/tables/track_e_s9_eda_summary.md && test -f outputs/tables/eda_artifact_census.md && test -f outputs/tables/eda_artifact_census.csv && test -f outputs/tables/eda_command_checklist.md`
- `python scripts/report_eda_completeness.py && rg -n "existing|missing|repaired" outputs/tables/eda_artifact_census.md && rg -n "python scripts/run_pipeline.py --approach track_d|track_a_s5_candidate_splits.parquet" outputs/tables/eda_command_checklist.md`
- `python scripts/report_eda_completeness.py && rg -n "missing upstream inputs|track_a_s5_candidate_splits.parquet|Run Track A through Stage 5" outputs/tables/track_d_s9_eda_summary.md outputs/tables/eda_command_checklist.md`

## Observability / Diagnostics

- Runtime signals: completeness status per approach/stage/artifact (`existing`, `missing`, `repaired`) plus summary-level fallback notes for absent upstream data
- Inspection surfaces: `python scripts/report_eda_completeness.py`, `outputs/tables/eda_artifact_census.md`, `outputs/tables/eda_artifact_census.csv`, `outputs/tables/eda_command_checklist.md`, and `outputs/tables/track_*_eda_summary.md`
- Failure visibility: missing artifact paths, blocked dependency notes (especially Track D on `track_a_s5_candidate_splits.parquet`), and summary sections that name which upstream stage outputs were unavailable
- Redaction constraints: no raw review text and no disallowed demographic/raw-text columns may appear in generated markdown, CSV, or logs

## Integration Closure

- Upstream surfaces consumed: `scripts/pipeline_dispatcher.py`, `scripts/run_pipeline.py`, `src/eda/track_a/summary_report.py`, `src/eda/track_b/common.py`, `src/eda/track_b/summary_report.py`, `src/eda/track_c/summary_report.py`, `src/eda/track_d/common.py`, `src/eda/track_d/summary_report.py`, `src/eda/track_e/summary_report.py`
- New wiring introduced in this slice: `scripts/report_eda_completeness.py` composes dispatcher contract data with per-track summary writers to emit the census, checklist, and repaired final summary outputs
- What remains before the milestone is truly usable end-to-end: S02 still needs export packaging, S03 still needs planning structure, and S04/S05 still need narrative + final integrated handoff verification

## Tasks

- [x] **T01: Expose the all-track EDA completion contract from the dispatcher** `est:45m`
  - Why: S01 needs one authoritative, code-level contract for final summary stages, required outputs, and canonical launcher commands before any census or repair logic can be trusted.
  - Files: `scripts/pipeline_dispatcher.py`, `scripts/run_pipeline.py`, `tests/test_pipeline_dispatcher_all_tracks.py`, `tests/test_run_pipeline_launcher.py`
  - Do: Add a reusable dispatcher helper that surfaces per-approach summary stages, required final summary outputs, and canonical `python scripts/run_pipeline.py --approach ...` commands directly from existing approach constants and `PIPELINES`; add regression tests for Tracks A–E summary endpoints and for the command checklist ordering/dependency notes, especially Track D's dependency on Track A Stage 5 output.
  - Verify: `python -m pytest tests/test_pipeline_dispatcher_all_tracks.py tests/test_run_pipeline_launcher.py`
  - Done when: the reporter can import one dispatcher-derived contract helper, and regression tests fail if a track loses its final summary stage, expected summary markdown, or canonical launcher command.
- [x] **T02: Harden Track A, B, and D summary writers for partial-repo regeneration** `est:1h`
  - Why: The slice demo requires final markdown summaries even in this stripped worktree, and Track B currently fails outright when snapshot metadata is missing.
  - Files: `src/eda/track_a/summary_report.py`, `src/eda/track_b/common.py`, `src/eda/track_b/summary_report.py`, `src/eda/track_d/summary_report.py`, `tests/test_track_a_summary_report.py`, `tests/test_track_b_summary_report.py`, `tests/test_track_d_summary_report.py`
  - Do: Make Track A/B/D summary generation explicitly tolerate absent upstream parquet/JSON inputs; fix Track B path/metadata handling so it can emit a truthful fallback summary when `snapshot_metadata.json` is missing; add regression tests in the established Track C/E style that assert missing-artifact notes, safe fallback metadata text, and no raw-text leakage in summary output.
  - Verify: `python -m pytest tests/test_track_a_summary_report.py tests/test_track_b_summary_report.py tests/test_track_d_summary_report.py`
  - Done when: Track A/B/D summary entrypoints can write final markdown into temporary output dirs without crashing on missing upstream artifacts, and Track B degrades to explicit missing-metadata language instead of raising `FileNotFoundError`.
- [x] **T03: Compose the all-track census, repair, and checklist reporting entrypoint** `est:1h 15m`
  - Why: This closes the slice by turning the dispatcher contract and repaired summary writers into a real handoff surface that downstream slices can trust.
  - Files: `scripts/report_eda_completeness.py`, `scripts/pipeline_dispatcher.py`, `src/eda/track_a/summary_report.py`, `src/eda/track_b/summary_report.py`, `src/eda/track_c/summary_report.py`, `src/eda/track_d/summary_report.py`, `src/eda/track_e/summary_report.py`, `tests/test_eda_artifact_census_report.py`
  - Do: Implement a thin reporter that imports the dispatcher contract, inspects live filesystem state, optionally repairs or re-emits missing final summary markdowns via the per-track summary modules, and writes a completeness matrix plus canonical command checklist under `outputs/tables/`; keep the output aggregate-safe, distinguish `existing` vs `missing` vs `repaired`, and surface Track D's Track-A dependency in the checklist/report.
  - Verify: `python -m pytest tests/test_eda_artifact_census_report.py && python scripts/report_eda_completeness.py && test -f outputs/tables/eda_artifact_census.md && test -f outputs/tables/eda_artifact_census.csv && test -f outputs/tables/eda_command_checklist.md`
  - Done when: one command generates the census/checklist artifacts plus the five final summary markdowns, and the generated report truthfully reflects the current stripped worktree rather than implying that upstream data exists.

## Files Likely Touched

- `scripts/pipeline_dispatcher.py`
- `scripts/run_pipeline.py`
- `scripts/report_eda_completeness.py`
- `src/eda/track_a/summary_report.py`
- `src/eda/track_b/common.py`
- `src/eda/track_b/summary_report.py`
- `src/eda/track_d/summary_report.py`
- `tests/test_pipeline_dispatcher_all_tracks.py`
- `tests/test_track_a_summary_report.py`
- `tests/test_track_b_summary_report.py`
- `tests/test_track_d_summary_report.py`
- `tests/test_eda_artifact_census_report.py`
