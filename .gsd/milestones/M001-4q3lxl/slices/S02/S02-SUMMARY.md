# Slice Summary — S02: Export contract and evidence packaging

## Status
- Complete
- Proof level: integration
- Requirement impact: R002 validated, R013 validated

## Goal
Turn the S01 EDA handoff into a standalone, aggregate-safe export bundle that downstream reporting, the future local website, and later modeling handoff can consume directly from the repo without querying analytical storage live.

## What This Slice Delivered

### 1) A standalone export packager grounded in existing repo truth
- `scripts/package_eda_exports.py` now materializes `outputs/exports/eda/` from:
  - `scripts.pipeline_dispatcher.get_eda_summary_contract()`
  - `outputs/tables/eda_artifact_census.csv`
  - `outputs/tables/eda_command_checklist.md`
  - the five final track summary markdowns from S01
- The packager is contract-first rather than copy-first:
  - root and per-track manifests are synthesized from dispatcher/census truth
  - summary markdowns and the checklist are copied verbatim only from an explicit allowlist
  - no dependency on `data/curated/` or live analytical storage is introduced
- Root bundle outputs now include:
  - `outputs/exports/eda/manifest.json`
  - `outputs/exports/eda/manifest.csv`
  - `outputs/exports/eda/eda_command_checklist.md`
  - `outputs/exports/eda/EXPORT_CONTRACT.md`
  - `outputs/exports/eda/figures/eda_overview.png`
- Per-track export folders now include, for Tracks A–E:
  - `outputs/exports/eda/tracks/<track>/summary.md`
  - `outputs/exports/eda/tracks/<track>/manifest.json`
  - `outputs/exports/eda/tracks/<track>/artifacts.csv`
  - `outputs/exports/eda/figures/<track>_status_card.png`

### 2) A governance-safe packaging boundary that fails loudly
- `EXPORT_CONTRACT.md` documents the downstream contract as **aggregate-safe** and **internal**.
- The bundle forbids copied `.parquet`, `.ndjson`, and `.log` artifacts under `outputs/exports/eda/`.
- `scripts/package_eda_exports.py` wipes and rebuilds the bundle root on each run so stale unsafe files cannot survive later checks.
- The only verbatim copied sources are the aggregate-safe markdown allowlist:
  - `outputs/tables/eda_command_checklist.md`
  - `outputs/tables/track_a_s8_eda_summary.md`
  - `outputs/tables/track_b_s8_eda_summary.md`
  - `outputs/tables/track_c_s9_eda_summary.md`
  - `outputs/tables/track_d_s9_eda_summary.md`
  - `outputs/tables/track_e_s9_eda_summary.md`
- Track E validity evidence is carried forward as metadata only in manifests rather than by redistributing `outputs/logs/track_e_s9_validity_scan.log`.

### 3) Synthesized PNG evidence surfaces that stay truthful in a stripped worktree
- Because this worktree does not contain a full set of analytical figures, S02 generates packaging-level visuals instead of copying stale or missing analytical PNGs.
- `outputs/exports/eda/figures/eda_overview.png` summarizes overall status and governance context.
- Each track gets a synthesized status card PNG that exposes:
  - summary status
  - per-track status totals
  - blocker visibility where applicable
- This keeps the PNG surface reproducible, aggregate-safe, and aligned with the same contract/census truth used by JSON and CSV outputs.

### 4) Downstream-visible blocker and status semantics
- Track D still carries its dependency on `outputs/tables/track_a_s5_candidate_splits.parquet` through exported machine-readable metadata.
- Missing upstream artifacts remain `missing`; the exporter does not fabricate completeness.
- Steady-state reruns preserve truthful status semantics instead of collapsing everything into `existing`.

## What Verification Proved

### Automated verification run
1. `python -m pytest /home/brooklynd23/.gsd/projects/2ccfe7e768a0/worktrees/M001-4q3lxl/tests/test_package_eda_exports.py`
   - Result: **4 passed**
   - Note: in this auto-mode harness, the slice test needed the absolute worktree path because the relative path could resolve against the `/mnt/c/...` repo mirror and report the test as missing.
2. `python scripts/package_eda_exports.py && test -f ...`
   - Result: passed
   - Proved the real worktree CLI run writes the expected root and per-track JSON/CSV/PNG/MD surfaces.
3. `python scripts/package_eda_exports.py && python - <<'PY' ... PY`
   - Result: passed
   - Proved the bundle contains no `.parquet`, `.ndjson`, or `.log` files and that the contract/Track D blocker strings remain visible.

### Observability surfaces confirmed
The slice plan's observability surfaces work and are useful in practice:
- `python scripts/package_eda_exports.py` logs root status totals, emitted file counts, Track E validity summary, and per-track blocker/status-card pointers.
- `outputs/exports/eda/manifest.json` exposes root counts, governance metadata, bundle pointers, and per-track export references.
- `outputs/exports/eda/EXPORT_CONTRACT.md` documents the packaging and governance contract in human-readable form.
- `outputs/exports/eda/tracks/track_d/manifest.json` keeps Track D's blocker visible in machine-readable form.
- `outputs/exports/eda/tracks/track_e/manifest.json` exposes metadata-only validity-log evidence.

### Observed steady-state bundle truth after verification
A clean verification run produced:
- root status totals: `existing=6`, `missing=109`
- emitted bundle files: `25`
- synthesized figures: `6`
- Track D `blocked_by`: `outputs/tables/track_a_s5_candidate_splits.parquet`
- Track E validity summary: `No findings detected.`

That result matters because the exporter stayed honest in this stripped worktree: it delivered a full downstream handoff bundle without pretending the missing upstream analytical artifacts were present.

## Key Output Behavior Established
- Export truth should come from dispatcher contract metadata plus the S01 census, not from scraping markdown or inventing a second manifest.
- Only allowlisted markdown inputs may be copied verbatim; every other bundle surface should be synthesized metadata or synthesized visuals.
- Governance enforcement must be structural, not advisory: stale unsafe files are removed on rebuild and forbidden suffixes are rejected.
- Packaging PNGs should visualize bundle status and blockers, not attempt to smuggle or substitute missing analytical figures.
- Track D's blocker belongs in exported machine-readable metadata, not only in prose.

## Decisions and Useful Context Captured
- D013: derive export bundle metadata from `get_eda_summary_contract()` plus `eda_artifact_census.csv`, and copy markdown verbatim without scraping markdown tables.
- D014: represent Track E validity-log evidence as metadata only; do not copy raw `.log` files into the bundle.
- D015: synthesize overview/status-card PNGs from contract and census truth rather than copying analytical figures.
- Knowledge retained for future agents:
  - `scripts/package_eda_exports.py` intentionally wipes `outputs/exports/eda/` on each run.
  - Do not run multiple packager invocations concurrently against the same worktree.
  - In this auto-mode harness, the S02 pytest command may need the absolute worktree test path.

## Requirement Updates
- `R002` moved from **active** to **validated** because S02 proved the repo can materialize JSON, CSV, PNG, and markdown export surfaces under `outputs/exports/eda/` for Tracks A–E.
- `R013` moved from **active** to **validated** because S02 proved the bundle remains aggregate-safe, internal-only, and free of raw review text plus copied `.parquet`, `.ndjson`, and `.log` artifacts.

## What Next Slices Should Know

### For S03 (agent-ready planning architecture)
- Treat `outputs/exports/eda/` as the stable evidence handoff surface when planning downstream implementation work.
- Planning docs should reference the root and per-track manifests rather than assuming broader stage materialization.
- Keep Track D's dependency visible in plans; downstream work should not treat Track D as fully unblocked.

### For S04 (trust narrative and intern explainer workflow)
- The narrative layer can now point to one packaging contract instead of five separate output conventions.
- Use the root manifest, per-track manifests, and synthesized PNGs as the aggregate-safe story surface for the trust-marketplace framing.
- The contract already distinguishes what is safe to share internally versus what must remain out of the bundle.

### For S05 (integrated local handoff verification)
- Reuse the three verification classes from this slice:
  - packager regression suite
  - real CLI bundle build
  - forbidden-artifact inspection
- Verify against the actual exported surfaces, not just the source `outputs/tables/` files.
- Avoid concurrent bundle rebuilds during integrated verification because the packager clears the bundle root on each run.

## Residual Risks
- The export bundle is now complete and truthful, but most underlying analytical stage artifacts are still absent in this stripped worktree.
- Track D remains visibly blocked on `outputs/tables/track_a_s5_candidate_splits.parquet`.
- Later slices still need to connect this export surface to planning structure, trust narrative, and full milestone-level integrated verification.
