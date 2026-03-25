# S01 — Research

**Date:** 2026-03-21

## Summary

S01 owns **R001** directly. The repo already has stage contracts for all five tracks in `scripts/pipeline_dispatcher.py` and final summary generators in `src/eda/track_a/summary_report.py` through `src/eda/track_e/summary_report.py`. The main brownfield problem is not missing code paths; it is implemented-vs-materialized drift. In this worktree there is no `data/` directory and no `outputs/` directory at all, so any honest census run now will classify every declared artifact as missing even though the generators and dispatcher contracts exist.

Primary recommendation: build S01 around a repo-level census/reporting layer that uses `scripts/pipeline_dispatcher.py` as the single source of truth for expected artifacts, then harden the per-track summary generators so they can emit final markdowns or explicit missing-data summaries without assuming a fully materialized repo. This follows the `debug-like-expert` rule to **VERIFY, DON'T ASSUME** and the `verification-loop` rule that completion needs observable **BEFORE / AFTER / EVIDENCE**, not “the module exists.” Track C and Track E already show the strongest pattern: both can summarize partial state, and Track E also emits a validity log.

## Recommendation

Implement one repo-level census/completeness matrix first; do not hand-maintain a second manifest. Reuse `dispatcher.PIPELINES`, `stage_outputs_exist()`, and `assess_pipeline()` rather than duplicating filenames in a new markdown or test fixture. Then close the real fragility gaps in summary generation:

- **Track B is the most brittle** because `load_snapshot_metadata()` hard-fails when `data/curated/snapshot_metadata.json` is absent.
- **Tracks A, B, and D have no dedicated summary-report regression tests.**
- **Track E’s “summary + validity log” pattern** is the best model for a verified S01 output.

Natural implementation seam: add one new repo-level reporting module/script, likely under `scripts/` or `src/common/`, that imports the dispatcher contract and emits:
1. a completeness matrix (`expected` vs `present` vs `missing` per track/stage),
2. a canonical command checklist tied to `python scripts/run_pipeline.py --approach ...`,
3. optionally a repaired summary generation pass for missing `track_*_eda_summary.md` artifacts.

Keep report rendering outside the already-large dispatcher file, but derive all artifact expectations from it. This matches the `coding-standards` KISS/DRY guidance: centralize truth, keep orchestration thin.

## Implementation Landscape

### Key Files

- `scripts/pipeline_dispatcher.py` — authoritative contract for all approaches, stage IDs, and required output artifacts; exposes `PIPELINES`, `stage_outputs_exist()`, and `assess_pipeline()` that S01 should reuse instead of duplicating filenames.
- `scripts/run_pipeline.py` — canonical human-facing launcher; S01’s verified command checklist should reference this file, not direct dispatcher internals.
- `src/eda/track_a/summary_report.py` — Track A final summary writer; already tolerates many missing stage artifacts via fallback text but currently has no dedicated regression test.
- `src/eda/track_b/common.py` — Track B path + snapshot metadata loading; `load_snapshot_metadata()` is a hard dependency that can block summary generation in partial repos.
- `src/eda/track_b/summary_report.py` — Track B final summary writer; good narrative structure, but it depends on snapshot metadata and has no summary-specific tests.
- `src/eda/track_c/summary_report.py` — strongest existing “graceful degradation” pattern: summary writes artifact status, key findings, and a soft text-leak scan even when some upstream artifacts are missing.
- `src/eda/track_d/common.py` — encodes Track D’s dependency on Track A Stage 5 splits via `load_track_a_splits()`; important for the verified command/file checklist because Track D cannot be treated as independently runnable.
- `src/eda/track_d/summary_report.py` — Track D final summary writer; already resilient to missing parquet files but lacks dedicated tests.
- `src/eda/track_e/common.py` — aggregate-safety helpers (`BANNED_TEXT_COLUMNS`, `FORBIDDEN_DEMOGRAPHIC_COLUMNS`, `list_track_e_artifacts()`); useful if the census report must stay governance-safe.
- `src/eda/track_e/summary_report.py` — best existing model for S01 verification because it writes both `track_e_s9_eda_summary.md` and `outputs/logs/track_e_s9_validity_scan.log`.
- `tests/test_pipeline_dispatcher_tracks_cd.py` — existing contract-test pattern for dispatcher outputs/stage registration; extend or mirror this style for all-track census coverage.
- `tests/test_run_pipeline_launcher.py` — existing launcher contract tests; keeps S01’s command checklist grounded in the canonical entrypoint.
- `tests/test_track_c_summary_report.py` — example of a lightweight summary rendering test that does not need the full dataset.
- `tests/test_track_e_summary_report.py` — example of summary + validity-scan regression coverage; best pattern to clone for A/B/D and any new census artifact test.

### Build Order

1. **Prove the brownfield state from the filesystem first.**
   - Current worktree lacks both `data/` and `outputs/`, so start by building a census that compares `dispatcher.PIPELINES[*].required_outputs` against actual files.
   - This retires the implemented-vs-materialized ambiguity immediately and follows the `debug-like-expert` guidance to verify observed state before proposing repairs.

2. **Make final-summary generation deterministic under partial artifact availability.**
   - Hardest gap is Track B’s snapshot metadata dependency; planner should inspect whether to add fallback metadata text or a stub “snapshot metadata missing” section so the final markdown can still be written.
   - Add tests for A/B/D summary rendering using the existing C/E test style before refactoring (`tdd-workflow` / `test` guidance: protect behavior with focused tests first).

3. **Add the S01 completeness artifact(s).**
   - Emit a single matrix/report that says which artifacts already existed, which were missing, and which were repaired/materialized.
   - This report should also encode the verified command checklist (`shared`, then Track A/B/C, Track D after Track A Stage 5, then Track E).

4. **Only then wire any orchestration convenience.**
   - If S01 needs a one-shot command, keep it thin and reuse the reporter + existing summary modules.
   - Do not bury new reporting logic inside the dispatcher if a standalone script/module can consume the same contract more cleanly.

### Verification Approach

- **Contract tests**
  - Add/extend tests that assert every approach in `dispatcher.PIPELINES` has a terminal `summary_report` stage and an expected `track_*_eda_summary.md` required output.
  - Add summary rendering tests for Track A, Track B, and Track D using temporary parquet/markdown fixtures, following `tests/test_track_c_summary_report.py` and `tests/test_track_e_summary_report.py`.

- **Filesystem checks**
  - Verify the census report correctly marks the current worktree as missing `data/` and `outputs/` artifacts.
  - Verify repaired outputs land in `outputs/tables/track_a_s8_eda_summary.md`, `outputs/tables/track_b_s8_eda_summary.md`, `outputs/tables/track_c_s9_eda_summary.md`, `outputs/tables/track_d_s9_eda_summary.md`, and `outputs/tables/track_e_s9_eda_summary.md`.

- **Command checklist verification**
  - Canonical commands are `python scripts/run_pipeline.py --approach shared`, then `track_a`, `track_b`, `track_c`, `track_d`, `track_e`.
  - Track D must be guarded by the presence of `outputs/tables/track_a_s5_candidate_splits.parquet`; the dispatcher already enforces this.

- **Observable evidence**
  - Follow the `verification-loop` standard: capture `BEFORE` (missing artifacts / no outputs), `AFTER` (summary + matrix files present), and `EVIDENCE` (tests + file existence + report contents).

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Expected artifact manifest | `scripts/pipeline_dispatcher.py` → `PIPELINES` + `required_outputs` | It is already the repo’s single source of truth for completion and rerun logic; duplicating it in a new manifest will drift. |
| Track-level safety scans | `src/eda/track_c/common.py` `scan_track_c_text_leaks()` and `src/eda/track_e/summary_report.py` `run_validity_scan()` | These already encode the no-raw-text / no-demographic-inference constraints; reuse patterns instead of inventing ad hoc checks. |

## Constraints

- S01 owns **R001** directly: all five tracks need verified, presentation-ready EDA summaries.
- Current worktree has **no `data/` directory and no `outputs/` directory**, so any live census now will read as “all artifacts missing” unless the slice also materializes files.
- Track D is not independently runnable; it requires `outputs/tables/track_a_s5_candidate_splits.parquet`.
- Track B summary currently requires `data/curated/snapshot_metadata.json` and will fail if it is absent.
- No raw review text can appear in any new census, summary, log, or matrix artifact.
- `scripts/run_pipeline.py` is the canonical entrypoint; direct interactive use of `scripts/pipeline_dispatcher.py` should not be the basis of user-facing instructions. Note: its legacy `choose_approach()` helper still prints only shared + Tracks A–D, which is another reason not to rely on it for checklist UX.

## Common Pitfalls

- **Manifest drift** — If S01 copies artifact names into a separate hardcoded list, it will diverge from `dispatcher.PIPELINES`. Derive from the dispatcher contract instead.
- **Assuming code == completion** — Summary modules exist for all five tracks, but this worktree has no materialized outputs. Base the census on live files, not source presence.
- **Brittle summary repair for Track B** — `load_snapshot_metadata()` raises on missing `snapshot_metadata.json`; if unresolved, Track B becomes the only summary that cannot be regenerated in a partial repo.
- **Under-testing summary writers** — Only Track C and Track E currently have dedicated summary tests. Repairs to A/B/D without matching tests will be easy to regress.

## Open Risks

- If the milestone expects an “already existed vs repaired” matrix from a data-bearing repo state, this stripped worktree may be insufficient by itself because it currently proves only “missing now,” not historical existence.
- Track B’s relative-path handling in `src/eda/track_b/common.py` is less robust than Tracks C/D/E because it does not resolve relative paths against `PROJECT_ROOT`.
- If the planner chooses to modify the dispatcher directly instead of adding a thin reporting layer, S01 may create more orchestration complexity inside an already very large file.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| DuckDB | `silvainfm/claude-skills@duckdb` | available |
| Python data pipelines | `jorgealves/agent_skills@python-data-pipeline-designer` | available |
| Parquet / data engineering | `majesticlabs-dev/majestic-marketplace@parquet-coder` | available |
