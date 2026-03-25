---
id: T02
parent: S01
milestone: M001-4q3lxl
provides:
  - Partial-repo-safe Track A, B, and D summary regeneration with explicit missing-artifact markdown notes
  - Regression coverage for Track A/B/D fallback wording and Track D's Track A Stage 5 blocker visibility
key_files:
  - src/eda/track_a/summary_report.py
  - src/eda/track_b/common.py
  - src/eda/track_b/summary_report.py
  - src/eda/track_d/summary_report.py
  - tests/test_track_a_summary_report.py
  - tests/test_track_b_summary_report.py
  - tests/test_track_d_summary_report.py
key_decisions:
  - Keep Track B metadata fallback permissive only for summary regeneration by calling `load_snapshot_metadata(..., allow_missing=True)` from the summary path while preserving strict default behavior for upstream stage builders.
patterns_established:
  - Treat `load_candidate_splits(..., source="config")` as a placeholder fallback, not as evidence that Track A Stage 5 materialized.
observability_surfaces:
  - outputs/tables/track_a_s8_eda_summary.md
  - outputs/tables/track_b_s8_eda_summary.md
  - outputs/tables/track_d_s9_eda_summary.md
  - .gsd/KNOWLEDGE.md
duration: 30m
verification_result: passed
completed_at: 2026-03-21T21:59:05-07:00
blocker_discovered: false
---

# T02: Harden Track A, B, and D summary writers for partial-repo regeneration

**Hardened Track A/B/D summary regeneration so partial repos emit truthful fallback markdown instead of crashing.**

## What Happened

I started by mirroring the Track C/E graceful-degradation test style into new Track A, Track B, and Track D regression files, then ran them against the live repo shape to expose the real gaps.

For Track B, I fixed `src/eda/track_b/common.py` so configured paths resolve from the worktree root instead of the caller's current directory, and I added an `allow_missing=True` metadata fallback mode that returns explicit placeholder values plus a human-readable note when `snapshot_metadata.json` is absent, unreadable, or invalid. In `src/eda/track_b/summary_report.py`, I added a `## Metadata Fallback` section, introduced a callable `run(config)` entrypoint, and made the summary writer use the permissive metadata path so Stage 8 can still emit truthful markdown in a stripped repo.

For Track A, I tightened `src/eda/track_a/summary_report.py` so Stage 4 attribute-completeness artifacts are no longer silently omitted from the summary. I also fixed the Stage 5 wording bug: config-placeholder split dates coming back from `load_candidate_splits()` are now treated as fallback defaults, not as if `track_a_s5_candidate_splits.parquet` actually exists.

For Track D, I updated `src/eda/track_d/summary_report.py` to add a `run(config)` entrypoint and a `## Missing Upstream Inputs` section. The summary path now probes the real Track A Stage 5 dependency via `load_track_a_splits()`, catches the blocking runtime message, and writes that blocker into the markdown instead of failing silently or omitting the dependency.

I also recorded the non-obvious Track A split-source gotcha in `.gsd/KNOWLEDGE.md` so T03 can reuse the rule without rediscovering it.

## Verification

I ran the focused T02 pytest target after the code changes and confirmed the new Track A/B/D regression suite passes. I also ran the inline Track B builder assertion from the task plan to confirm that placeholder metadata still produces explicit missing language and the expected Stage 1 missing-artifact note.

To verify the observability impact directly, I generated Track A, Track B, and Track D summaries into a temporary workspace and asserted on the emitted markdown text itself: Track A now reports missing Stage 4 and Stage 5 inputs truthfully, Track B now emits a metadata fallback section when `snapshot_metadata.json` is absent, and Track D now surfaces the `track_a_s5_candidate_splits.parquet` blocker plus the "Run Track A through Stage 5" guidance.

I also ran the slice-level S01 verification commands. The T02-owned portions are now green, but the slice-wide reporter checks still fail as expected because `tests/test_eda_artifact_census_report.py` and `scripts/report_eda_completeness.py` are not in scope until T03.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `./.venv-local/bin/python -m pytest tests/test_track_a_summary_report.py tests/test_track_b_summary_report.py tests/test_track_d_summary_report.py` | 0 | ✅ pass | 0.72s |
| 2 | `./.venv-local/bin/python - <<'PY' ... build_summary_markdown(...) ... PY` | 0 | ✅ pass | 0.46s |
| 3 | `./.venv-local/bin/python - <<'PY' ... run_a/run_b/run_d temporary observability check ... PY` | 0 | ✅ pass | 0.62s |
| 4 | `./.venv-local/bin/python -m pytest tests/test_pipeline_dispatcher_all_tracks.py tests/test_track_a_summary_report.py tests/test_track_b_summary_report.py tests/test_track_d_summary_report.py tests/test_eda_artifact_census_report.py` | 4 | ❌ fail | 0.19s |
| 5 | `./.venv-local/bin/python scripts/report_eda_completeness.py && test -f outputs/tables/track_a_s8_eda_summary.md && test -f outputs/tables/track_b_s8_eda_summary.md && test -f outputs/tables/track_c_s9_eda_summary.md && test -f outputs/tables/track_d_s9_eda_summary.md && test -f outputs/tables/track_e_s9_eda_summary.md && test -f outputs/tables/eda_artifact_census.md && test -f outputs/tables/eda_artifact_census.csv && test -f outputs/tables/eda_command_checklist.md` | 2 | ❌ fail | 0.03s |
| 6 | `./.venv-local/bin/python scripts/report_eda_completeness.py && rg -n "existing|missing|repaired" outputs/tables/eda_artifact_census.md && rg -n "python scripts/run_pipeline.py --approach track_d|track_a_s5_candidate_splits.parquet" outputs/tables/eda_command_checklist.md` | 2 | ❌ fail | 0.02s |
| 7 | `./.venv-local/bin/python scripts/report_eda_completeness.py && rg -n "missing upstream inputs|track_a_s5_candidate_splits.parquet|Run Track A through Stage 5" outputs/tables/track_d_s9_eda_summary.md outputs/tables/eda_command_checklist.md` | 2 | ❌ fail | 0.02s |

## Diagnostics

After regeneration, inspect `outputs/tables/track_a_s8_eda_summary.md` for the new Stage 4 missing-artifact note and the corrected Stage 5 config-fallback wording. Inspect `outputs/tables/track_b_s8_eda_summary.md` for the `## Metadata Fallback` section when `data/curated/snapshot_metadata.json` is absent. Inspect `outputs/tables/track_d_s9_eda_summary.md` for the `## Missing Upstream Inputs` section naming `track_a_s5_candidate_splits.parquet` and the explicit "Run Track A through Stage 5" guidance. The reusable split-source gotcha is recorded in `.gsd/KNOWLEDGE.md`.

## Deviations

None.

## Known Issues

Slice-level S01 completeness verification is still incomplete because `tests/test_eda_artifact_census_report.py` and `scripts/report_eda_completeness.py` do not exist yet; those failures are expected until T03 lands.

## Files Created/Modified

- `src/eda/track_a/summary_report.py` — added Stage 4 visibility and corrected Stage 5 config-fallback vs materialized-artifact wording.
- `src/eda/track_b/common.py` — anchored relative path resolution to the worktree root and added permissive snapshot-metadata fallback handling for summary regeneration.
- `src/eda/track_b/summary_report.py` — added metadata fallback rendering and a `run(config)` entrypoint that survives missing `snapshot_metadata.json`.
- `src/eda/track_d/summary_report.py` — added a `run(config)` entrypoint plus explicit Track A Stage 5 blocker reporting in the summary markdown.
- `tests/test_track_a_summary_report.py` — added Track A regression coverage for missing Stage 4 and truthful Stage 5 fallback language.
- `tests/test_track_b_summary_report.py` — added Track B regression coverage for absolute path resolution, metadata fallback wording, and missing-artifact-safe summary generation.
- `tests/test_track_d_summary_report.py` — added Track D regression coverage for the missing-upstream-inputs section and Track A Stage 5 blocker visibility.
- `.gsd/KNOWLEDGE.md` — recorded the Track A split-source placeholder gotcha for downstream S01 work.
- `.gsd/milestones/M001-4q3lxl/slices/S01/S01-PLAN.md` — marked T02 complete.
