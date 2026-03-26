# M001-4q3lxl — Research

**Date:** 2026-03-21

## Summary

S02 owns the active requirements `R002` and `R013`, so the slice has to do two things at once: define a downstream-friendly export contract and keep that package governance-safe. The current worktree is a stripped brownfield handoff surface, not a fully materialized analytics repo: `outputs/tables/track_*_eda_summary.md`, `outputs/tables/eda_artifact_census.{md,csv}`, `outputs/tables/eda_command_checklist.md`, and `outputs/logs/track_e_s9_validity_scan.log` exist, but the worktree has no `data/` directory and almost every upstream stage parquet/PNG in the census is still `missing`.

That means the export layer cannot depend on curated parquet or pretend the missing analytical artifacts exist. The safest approach is a standalone post-EDA packaging command, modeled on `scripts/report_eda_completeness.py`, that derives truth from `scripts.pipeline_dispatcher.get_eda_summary_contract()` plus the live census/checklist outputs and writes a separate `outputs/exports/...` bundle of JSON/CSV/PNG/MD artifacts. This aligns with the loaded `coding-standards` skill (`KISS`, `DRY`, `YAGNI`) and the `verification-loop` rule that validation must prove observable written outputs instead of treating a zero exit code as success.

## Recommendation

Implement S02 as **one standalone packaging/reporting utility** rather than a new dispatcher stage. Recommended shape: `scripts/package_eda_exports.py` with a `generate_export_bundle(repo_root=...)` entrypoint and small writer helpers, following the same pattern as `scripts/report_eda_completeness.py`. Keep the source of truth dispatcher-derived and census-derived; do **not** scrape summary markdown for truth and do **not** create a second hardcoded export manifest.

The bundle should be honest-first and outputs-only:
- copy/package the five final summary markdowns and the S01 census/checklist artifacts as the canonical evidence layer
- emit machine-readable JSON/CSV manifests per track from dispatcher + census rows
- generate packaging-level PNGs from the census itself (repo overview + simple per-track status cards) so the repo exposes a robust PNG surface even when analytical figures are absent in the stripped worktree
- exclude raw parquet and avoid blindly copying logs; include only explicitly allowlisted text artifacts or summarized log findings

This also matches the loaded `test` / `tdd-workflow` guidance: copy the existing pytest style, use `tmp_path` contract tests, and verify exported file contents directly instead of relying on manual spot checks.

## Implementation Landscape

### Key Files

- `scripts/report_eda_completeness.py` — best implementation template for S02. It already uses an injectable `repo_root`, dataclasses, dispatcher-derived contract loading, and explicit writers for `.md`/`.csv` outputs.
- `scripts/pipeline_dispatcher.py` — authoritative contract for approaches, stage order, required outputs, canonical launcher commands, and `TRACK_D_SPLIT_DEPENDENCY`. `get_eda_summary_contract()` should remain the packaging source of truth.
- `outputs/tables/eda_artifact_census.csv` — primary machine-readable input for packaging. It already captures the honest `existing` / `missing` / `repaired` semantics established in S01.
- `outputs/tables/eda_command_checklist.md` — canonical launcher order and Track D blocker note that the export contract should preserve verbatim or summarize into JSON.
- `outputs/tables/track_a_s8_eda_summary.md` through `outputs/tables/track_e_s9_eda_summary.md` — canonical per-track markdown evidence to copy into the export bundle. Treat them as evidence artifacts, not as the truth source for artifact existence.
- `src/curate/build_sample.py` — existing JSON manifest-writing pattern worth copying for export manifests (`manifest` dict + deterministic keys + simple stdlib JSON write).
- `tests/test_build_sample.py` — example of the repo’s manifest-oriented `tmp_path` testing style.
- `tests/test_eda_artifact_census_report.py` — direct test pattern for a script-level reporter that writes outputs into a temporary repo root and asserts on file existence + semantic content.
- `src/eda/track_b/common.py` — contains `TEXT_ARTIFACT_SUFFIXES`, useful if S02 needs an explicit allowlist for text artifacts in the package.
- `src/eda/track_c/common.py` and `src/eda/track_e/summary_report.py` — existing governance checks and placeholder-figure patterns. Reuse the ideas, but avoid depending on track-specific modules unless the helper is promoted to a neutral utility.
- `src/eda/track_e/common.py` / `src/eda/track_e/summary_report.py` — important pitfall: the current Track E summary manually appends `track_e_s9_validity_scan.log` after iterating `list_track_e_artifacts(paths)`, so the markdown artifact index can duplicate entries. Do not parse summary markdown artifact tables to infer the package contents.
- `configs/base.yaml` — optional touchpoint if the planner wants a configurable `exports_dir`; otherwise keep S02 simpler with a script-local default output root under `outputs/exports/`.

### Build Order

1. **Define the export bundle schema first** — settle the output root and file layout before writing code. The planner should lock a small, explicit contract such as:
   - `outputs/exports/eda/EXPORT_CONTRACT.md`
   - `outputs/exports/eda/manifest.json`
   - `outputs/exports/eda/manifest.csv`
   - `outputs/exports/eda/figures/eda_overview.png`
   - `outputs/exports/eda/figures/track_<x>_status_card.png`
   - `outputs/exports/eda/tracks/<track>/summary.md`
   - `outputs/exports/eda/tracks/<track>/manifest.json`
   - `outputs/exports/eda/tracks/<track>/artifacts.csv`

2. **Prove the bundle can be generated from the stripped worktree** — use only dispatcher metadata + existing S01 outputs. This is the critical step because the worktree has no `data/` directory and almost no materialized stage artifacts.

3. **Write JSON/CSV/MD surfaces before PNGs** — the contract and machine-readable manifests are the real downstream dependency. Once those are stable, add the PNG status visuals as synthesized packaging artifacts from census counts.

4. **Add explicit governance filtering** — keep the exporter on an allowlist of artifact types/paths instead of copying whole directories. This is where `R013` is enforced.

5. **Only after the above, add the CLI wrapper and README/contract text** — the docs should describe the actual package shape, not a speculative one.

### Verification Approach

- Add a dedicated contract test file, likely `tests/test_package_eda_exports.py`, following the same `tmp_path` pattern as `tests/test_eda_artifact_census_report.py`.
- Verify the new script against a synthetic repo root containing:
  - five summary markdowns
  - `eda_artifact_census.csv`
  - `eda_command_checklist.md`
  - a mix of `existing` and `missing` rows
- Assert that the export bundle writes all promised JSON/CSV/PNG/MD files and that:
  - missing upstream artifacts remain `missing` in exported manifests
  - Track D carries `outputs/tables/track_a_s5_candidate_splits.parquet` as a blocker
  - per-track markdown summaries are copied, not regenerated from guessed content
  - no raw parquet files are included in the package
  - artifact row counts in exported CSV/JSON match the census input
- Run the slice locally with:
  - `python -m pytest tests/test_eda_artifact_census_report.py tests/test_package_eda_exports.py`
  - `python scripts/report_eda_completeness.py`
  - `python scripts/package_eda_exports.py`
- Finish with observable file checks under `outputs/exports/eda/` instead of “command succeeded” reasoning, per the loaded `verification-loop` guidance.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Track/stage/source-of-truth contract | `scripts.pipeline_dispatcher.get_eda_summary_contract()` | S01 already established that downstream reporting should derive from the dispatcher, not a second manifest. |
| Reporter/packager structure | `scripts/report_eda_completeness.py` | It already demonstrates the repo’s preferred script-level pattern for dataclasses, repo-root injection, and deterministic writer helpers. |
| JSON manifest pattern | `src/curate/build_sample.py` | It is the clearest existing example of a small stdlib JSON manifest written for downstream consumers. |
| Script-level tmp repo testing | `tests/test_eda_artifact_census_report.py` | It shows how to test packaging/reporting utilities without touching real curated data. |

## Constraints

- The current worktree has **no `data/` directory**, so S02 must not require `data/curated/*.parquet` or rerun upstream EDA stages to produce the export bundle.
- `R013` still applies: no raw review text, no public-redistribution assumptions, and no blind directory copies of potentially unsafe artifacts.
- S01’s status semantics are binding: only artifacts regenerated in the current run are `repaired`; absent upstream evidence stays `missing`.
- Track D’s export surface must continue to show its dependency on `outputs/tables/track_a_s5_candidate_splits.parquet`.
- The export package should stay outside the dispatcher pipeline unless the team intentionally decides to make packaging part of the canonical run order.

## Common Pitfalls

- **Treating final summaries as proof that upstream evidence exists** — the summaries are handoff artifacts, not proof of full materialization. Build manifests from the census rows, not from summary presence alone.
- **Parsing markdown artifact tables as package truth** — Track E’s current summary can duplicate artifact lines, so markdown indexes are not a safe manifest source.
- **Accidentally fabricating analytical PNG evidence** — if S02 synthesizes PNGs from the census, label them as packaging/evidence-status visuals, not as analytical findings.
- **Copying whole `outputs/tables/` or `outputs/logs/` trees** — this breaks the aggregate-safe requirement and makes the package depend on whatever stale artifacts happen to be lying around.

## Open Risks

- The first S02 pass can make the repo website/report-ready at the **contract level**, but not at the “rich chart-data JSON” level unless the missing upstream parquets/figures are materialized in a later slice or later milestone.
- If the planner wants per-track JSON to contain parsed “key findings,” that will add brittle markdown parsing. The lower-risk contract is to ship markdown as markdown and keep JSON focused on paths, statuses, commands, blockers, and counts.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| DuckDB | `silvainfm/claude-skills@duckdb` | available via `npx skills add silvainfm/claude-skills@duckdb` |
| Pandas | `jeffallan/claude-skills@pandas-pro` | available via `npx skills add jeffallan/claude-skills@pandas-pro` |