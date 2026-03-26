# S02: Export contract and evidence packaging

**Goal:** Turn the verified S01 EDA handoff into a standalone, aggregate-safe export bundle that downstream reporting, local website work, and later modeling handoff can consume without querying analytical storage live.
**Demo:** Running `python scripts/package_eda_exports.py` in this stripped worktree writes `outputs/exports/eda/` with truthful JSON, CSV, PNG, and markdown surfaces for Tracks A–E while preserving `existing`/`missing` status semantics and excluding unsafe raw artifacts.

## Active Requirement Coverage

- `R002` (owner): deliver a real JSON/CSV/PNG/MD export surface that downstream consumers can read directly from the repo.
- `R013` (owner): keep the package aggregate-safe, internally scoped, and free of raw review text plus raw-storage redistribution shortcuts.

## Decomposition Rationale

This slice is ordered contract-first because the main risk is drift: if executors start by copying files or drawing charts without a locked bundle schema, the website/report handoff will depend on improvised paths. T01 therefore creates the packager around a tmp-repo contract test and the dispatcher/S01 evidence surfaces, so later tasks extend one verified shape instead of inventing a second manifest.

The second risk is governance failure. In this stripped worktree it would be easy to "solve" packaging by copying `outputs/` wholesale, but that would violate `R013`, hide missing upstream artifacts, and make the bundle depend on stale local state. T02 is isolated around allowlisting, contract docs, and exclusion tests so the aggregate-safe boundary is explicit in code and in the generated contract.

PNG output is required by `R002`, but it is the least trustworthy place to start because the worktree lacks most analytical figures. T03 therefore generates packaging-level status visuals only after the JSON/CSV/MD bundle is stable, then closes the slice with the real CLI run and file-based verification that future agents can repeat locally.

## Must-Haves

- A standalone export packager derives bundle truth from `scripts.pipeline_dispatcher.get_eda_summary_contract()` plus S01 outputs (`outputs/tables/eda_artifact_census.csv`, `outputs/tables/eda_command_checklist.md`, and the five final summary markdowns) instead of maintaining a second hardcoded manifest.
- The bundle exposes downstream-safe JSON, CSV, PNG, and markdown surfaces under `outputs/exports/eda/`, including root manifests and per-track export folders.
- Governance rules are encoded in the implementation and contract docs: no raw review text, no blind `.parquet` / `.ndjson` / `.log` copies, and Track D's dependency on `outputs/tables/track_a_s5_candidate_splits.parquet` remains visible to downstream consumers.
- Regression coverage proves bundle layout, status semantics, forbidden-artifact exclusions, and the real CLI run against this stripped worktree.

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `python -m pytest tests/test_package_eda_exports.py`
- `python scripts/package_eda_exports.py && test -f outputs/exports/eda/manifest.json && test -f outputs/exports/eda/manifest.csv && test -f outputs/exports/eda/EXPORT_CONTRACT.md && test -f outputs/exports/eda/figures/eda_overview.png && for track in track_a track_b track_c track_d track_e; do test -f outputs/exports/eda/figures/${track}_status_card.png && test -f outputs/exports/eda/tracks/${track}/summary.md && test -f outputs/exports/eda/tracks/${track}/manifest.json && test -f outputs/exports/eda/tracks/${track}/artifacts.csv; done`
- `python scripts/package_eda_exports.py && python - <<'PY'
from pathlib import Path
root = Path('outputs/exports/eda')
forbidden = sorted(
    path.as_posix()
    for path in root.rglob('*')
    if path.is_file() and path.suffix in {'.parquet', '.ndjson', '.log'}
)
assert not forbidden, forbidden
contract = (root / 'EXPORT_CONTRACT.md').read_text(encoding='utf-8')
track_d_manifest = (root / 'tracks' / 'track_d' / 'manifest.json').read_text(encoding='utf-8')
assert 'aggregate-safe' in contract
assert 'internal' in contract
assert 'track_a_s5_candidate_splits.parquet' in track_d_manifest
PY`

## Observability / Diagnostics

- Runtime signals: root/per-track manifest status totals, per-track `blocked_by` notes, emitted file counts, and explicit missing-source statuses carried forward from the census
- Inspection surfaces: `python scripts/package_eda_exports.py`, `outputs/exports/eda/manifest.json`, `outputs/exports/eda/manifest.csv`, `outputs/exports/eda/EXPORT_CONTRACT.md`, and `outputs/exports/eda/tracks/*/manifest.json`
- Failure visibility: missing S01 inputs surface as path-specific failures, forbidden artifact types fail tests, and Track D blocker visibility is inspectable in exported manifests instead of hidden in markdown prose only
- Redaction constraints: exports must remain aggregate-safe, internally scoped, and free of raw review text plus raw storage artifacts

## Integration Closure

- Upstream surfaces consumed: `scripts/pipeline_dispatcher.py`, `scripts/report_eda_completeness.py`, `outputs/tables/eda_artifact_census.csv`, `outputs/tables/eda_command_checklist.md`, `outputs/tables/track_a_s8_eda_summary.md`, `outputs/tables/track_b_s8_eda_summary.md`, `outputs/tables/track_c_s9_eda_summary.md`, `outputs/tables/track_d_s9_eda_summary.md`, `outputs/tables/track_e_s9_eda_summary.md`
- New wiring introduced in this slice: `scripts/package_eda_exports.py` composes dispatcher metadata with the S01 evidence layer to materialize `outputs/exports/eda/` as the downstream handoff surface
- What remains before the milestone is truly usable end-to-end: S03 still needs agent-ready planning structure, S04 still needs the trust-marketplace narrative layer, and S05 still needs integrated local handoff verification

## Tasks

- [x] **T01: Build the contract-first export bundle generator and regression test** `est:1h 15m`
  - Why: The bundle shape must be locked to real dispatcher/S01 evidence before any packaging shortcuts or synthesized visuals are added.
  - Files: `scripts/package_eda_exports.py`, `tests/test_package_eda_exports.py`, `scripts/pipeline_dispatcher.py`, `scripts/report_eda_completeness.py`, `outputs/tables/eda_artifact_census.csv`, `outputs/tables/eda_command_checklist.md`
  - Do: Add a tmp-path regression test that creates a minimal S01-style repo root, then implement `generate_export_bundle(repo_root=...)` so it reads the dispatcher contract plus census/checklist inputs, copies the final summary markdowns verbatim, and writes root/per-track JSON/CSV/MD manifests under `outputs/exports/eda/` without depending on curated parquet.
  - Verify: `python -m pytest tests/test_package_eda_exports.py`
  - Done when: one focused pytest file proves the packager can build truthful root and per-track JSON/CSV/MD outputs from S01 artifacts alone, with Track D blocker metadata preserved in the exported manifests.
- [x] **T02: Enforce governance-safe packaging rules and publish the export contract** `est:1h`
  - Why: `R013` can fail even if the bundle exists, so the package needs explicit allowlisting, exclusion tests, and contract text that future slices can rely on.
  - Files: `scripts/package_eda_exports.py`, `tests/test_package_eda_exports.py`, `outputs/tables/track_d_s9_eda_summary.md`, `outputs/logs/track_e_s9_validity_scan.log`, `outputs/exports/eda/EXPORT_CONTRACT.md`
  - Do: Extend the packager with allowlisted artifact selection and forbidden-type exclusion rules, generate `EXPORT_CONTRACT.md` describing the bundle layout and governance boundary, and expand tests so `.parquet`, `.ndjson`, copied `.log`, and raw-text leakage regressions fail loudly while missing upstream artifacts stay marked `missing`.
  - Verify: `python -m pytest tests/test_package_eda_exports.py`
  - Done when: the generated contract names the aggregate-safe/internal-only boundary and tests prove the bundle cannot silently start redistributing raw storage artifacts or blind log copies.
- [x] **T03: Add synthesized PNG evidence visuals and close the CLI handoff** `est:1h`
  - Why: `R002` requires a PNG surface, and the slice is only complete once the real stripped worktree can generate the full bundle end-to-end.
  - Files: `scripts/package_eda_exports.py`, `tests/test_package_eda_exports.py`, `outputs/exports/eda/manifest.json`, `outputs/exports/eda/figures/eda_overview.png`, `outputs/exports/eda/figures/track_d_status_card.png`, `outputs/exports/eda/tracks/track_d/manifest.json`
  - Do: Add census-derived packaging visuals (`eda_overview.png` plus one per-track status card), finish the CLI entrypoint and emitted-path logging, and run the real worktree export flow so the bundle contains stable JSON/CSV/PNG/MD artifacts ready for downstream slices.
  - Verify: `python -m pytest tests/test_package_eda_exports.py && python scripts/package_eda_exports.py && test -f outputs/exports/eda/figures/eda_overview.png`
  - Done when: running `python scripts/package_eda_exports.py` in this worktree produces the full export bundle and the slice verification checks pass without forbidden artifacts appearing in `outputs/exports/eda/`.

## Files Likely Touched

- `scripts/package_eda_exports.py`
- `tests/test_package_eda_exports.py`
- `outputs/exports/eda/EXPORT_CONTRACT.md`
- `outputs/exports/eda/manifest.json`
- `outputs/exports/eda/figures/eda_overview.png`
