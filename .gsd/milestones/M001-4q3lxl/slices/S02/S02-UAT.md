# UAT — S02: Export contract and evidence packaging

## UAT Goal
Confirm that the repo can generate a truthful, aggregate-safe EDA export bundle under `outputs/exports/eda/`, that the bundle exposes JSON/CSV/PNG/MD surfaces for Tracks A–E, and that governance rules prevent raw-storage artifact redistribution.

## Preconditions
- Run from the repo root of this worktree.
- Python and Pillow dependencies must resolve in the shell used for verification.
- S01 evidence inputs must already exist:
  - `outputs/tables/eda_artifact_census.csv`
  - `outputs/tables/eda_command_checklist.md`
  - `outputs/tables/track_a_s8_eda_summary.md`
  - `outputs/tables/track_b_s8_eda_summary.md`
  - `outputs/tables/track_c_s9_eda_summary.md`
  - `outputs/tables/track_d_s9_eda_summary.md`
  - `outputs/tables/track_e_s9_eda_summary.md`
- The current worktree may still be missing most intermediate EDA parquet/PNG outputs; that is expected.
- Because `scripts/package_eda_exports.py` deletes and recreates `outputs/exports/eda/` on each run, execute the CLI checks sequentially rather than in parallel.

## Test Case 1 — Regression suite for the export contract
**Purpose:** Prove the packager layout, governance boundary, and tmp-repo behavior are covered by automated tests.

### Steps
1. Run:
   ```bash
   python -m pytest tests/test_package_eda_exports.py
   ```
2. If the harness reports `file or directory not found` for the relative path even though the file exists, rerun with the absolute worktree path:
   ```bash
   python -m pytest /home/brooklynd23/.gsd/projects/2ccfe7e768a0/worktrees/M001-4q3lxl/tests/test_package_eda_exports.py
   ```

### Expected Outcomes
1. Pytest exits with code `0`.
2. All tests pass.
3. The suite proves at least these behaviors:
   - bundle generation depends on dispatcher metadata plus S01 evidence, not `data/curated/`
   - copied markdown sources are allowlisted
   - Track D blocker metadata survives into exports
   - Track E validity-log evidence is metadata-only
   - stale `.parquet` / `.log` leftovers are removed from the bundle root

## Test Case 2 — Materialize the real export bundle in this worktree
**Purpose:** Confirm the CLI works end-to-end against the current stripped worktree.

### Steps
1. Run:
   ```bash
   python scripts/package_eda_exports.py
   ```
2. Verify the root bundle files exist:
   ```bash
   test -f outputs/exports/eda/manifest.json
   test -f outputs/exports/eda/manifest.csv
   test -f outputs/exports/eda/EXPORT_CONTRACT.md
   test -f outputs/exports/eda/eda_command_checklist.md
   test -f outputs/exports/eda/figures/eda_overview.png
   ```
3. Verify the per-track bundle files exist:
   ```bash
   for track in track_a track_b track_c track_d track_e; do
     test -f outputs/exports/eda/figures/${track}_status_card.png
     test -f outputs/exports/eda/tracks/${track}/summary.md
     test -f outputs/exports/eda/tracks/${track}/manifest.json
     test -f outputs/exports/eda/tracks/${track}/artifacts.csv
   done
   ```

### Expected Outcomes
1. The CLI exits with code `0`.
2. All root file checks pass.
3. All per-track file checks pass.
4. The command prints useful inspection output including:
   - root status totals
   - emitted file counts
   - Track E validity summary
   - per-track `blocked_by` state and status-card path

## Test Case 3 — Root manifest exposes the full downstream contract
**Purpose:** Confirm downstream consumers can inspect one machine-readable root contract instead of guessing paths.

### Steps
1. Open `outputs/exports/eda/manifest.json`.
2. Review these fields:
   - `scope`
   - `safety_boundary`
   - `status_totals`
   - `source_inputs`
   - `governance`
   - `figures`
   - `tracks`

### Expected Outcomes
1. `scope` is `internal`.
2. `safety_boundary` is `aggregate-safe`.
3. The manifest points to:
   - `manifest.csv`
   - `EXPORT_CONTRACT.md`
   - `eda_overview.png`
   - one status-card PNG per track
4. The manifest includes all five tracks with per-track summary, manifest, artifacts CSV, status-card path, status totals, and blocker metadata.
5. Missing upstream artifacts remain visible as `missing`; the exporter does not collapse them into `existing`.

## Test Case 4 — Governance contract and allowlist are explicit
**Purpose:** Confirm the human-readable contract states the packaging boundary and allowed behavior.

### Steps
1. Open `outputs/exports/eda/EXPORT_CONTRACT.md`.
2. Review the sections:
   - Governance Boundary
   - Allowlisted Verbatim Copies
   - Bundle Layout
   - Status Semantics
   - Track D Blocker Rule
   - Metadata-Only Summaries

### Expected Outcomes
1. The contract explicitly says the bundle is `aggregate-safe` and `internal`.
2. The contract forbids copied `.parquet`, `.ndjson`, and `.log` artifacts.
3. The only verbatim copied sources listed are the six allowlisted markdown files.
4. The contract explains `existing`, `missing`, and `repaired` semantics.
5. The contract explicitly names `outputs/tables/track_a_s5_candidate_splits.parquet` as Track D's blocker.
6. The contract states that Track E validity-log evidence is represented as metadata only.

## Test Case 5 — Track D blocker is still visible to downstream consumers
**Purpose:** Confirm the export bundle preserves dependency visibility instead of hiding it in summary prose only.

### Steps
1. Open `outputs/exports/eda/tracks/track_d/manifest.json`.
2. Review:
   - `blocked_by`
   - `summary_status`
   - `status_totals`
   - final `summary_report` artifact row in `artifacts`
3. Open `outputs/exports/eda/tracks/track_d/artifacts.csv` and confirm the same summary row is present.

### Expected Outcomes
1. `blocked_by` contains `outputs/tables/track_a_s5_candidate_splits.parquet`.
2. `summary_status` truthfully reflects the upstream summary markdown status.
3. The summary-stage artifact row still contains the dependency note rather than hiding it.
4. Downstream consumers can detect the Track D blocker from machine-readable exports alone.

## Test Case 6 — Track E validity evidence is metadata-only
**Purpose:** Confirm the bundle preserves useful audit signal without copying raw log files.

### Steps
1. Open `outputs/exports/eda/tracks/track_e/manifest.json`.
2. Review the `metadata_summaries` array.
3. Confirm the source log path and summarized outcome are present.
4. Search the bundle for forbidden file types:
   ```bash
   find outputs/exports/eda -type f \( -name '*.parquet' -o -name '*.ndjson' -o -name '*.log' \)
   ```

### Expected Outcomes
1. `metadata_summaries` includes an entry for `outputs/logs/track_e_s9_validity_scan.log`.
2. The entry uses `export_mode: metadata_only`.
3. The summary currently reads `No findings detected.`
4. The `find` command returns no files.

## Test Case 7 — Synthesized PNG surfaces exist and are packaging-level evidence
**Purpose:** Confirm the required PNG surface is present without depending on missing analytical figures.

### Steps
1. Open these files in an image viewer:
   - `outputs/exports/eda/figures/eda_overview.png`
   - `outputs/exports/eda/figures/track_d_status_card.png`
   - `outputs/exports/eda/figures/track_e_status_card.png`
2. Visually review the titles, status counts, and blocker/summary messaging.
3. Cross-check the values against `manifest.json`, `track_d/manifest.json`, and `track_e/manifest.json`.

### Expected Outcomes
1. All three images are valid PNG files and load successfully.
2. The overview image reflects bundle-level packaging status rather than analytical chart content.
3. `track_d_status_card.png` visibly communicates Track D's blocker.
4. `track_e_status_card.png` aligns with Track E's exported status totals.
5. None of the images contain raw review text or copied analytical content.

## Test Case 8 — Rebuild behavior removes stale unsafe leftovers
**Purpose:** Confirm the packager cleans the bundle root instead of allowing stale unsafe files to survive.

### Steps
1. Create a temporary unsafe file in the bundle root:
   ```bash
   mkdir -p outputs/exports/eda
   printf 'unsafe' > outputs/exports/eda/stale.parquet
   ```
2. Re-run:
   ```bash
   python scripts/package_eda_exports.py
   ```
3. Check that the stale file is gone:
   ```bash
   test ! -f outputs/exports/eda/stale.parquet
   ```

### Expected Outcomes
1. The packager exits with code `0`.
2. The stale file is removed.
3. The rebuilt bundle still contains the expected root and per-track export files.

## Edge Case Checks

### Edge Case A — Steady-state rerun should stay truthful
**Steps**
1. Re-run:
   ```bash
   python scripts/package_eda_exports.py
   ```
2. Open `outputs/exports/eda/manifest.json`.
3. Review `status_totals` and each track's `summary_status`.

**Expected Outcomes**
1. The bundle rebuild succeeds cleanly.
2. Existing summary markdowns remain `existing` on a steady-state rerun.
3. Missing upstream artifacts remain `missing`.
4. The exporter does not fabricate repaired status on rerun.

### Edge Case B — Sequential execution only
**Steps**
1. Do not launch two `python scripts/package_eda_exports.py` commands at the same time.
2. If building the bundle as part of a larger verification workflow, serialize the package step before any dependent file checks.

**Expected Outcomes**
1. No transient `FileNotFoundError` occurs from two packager runs racing on the bundle root.
2. Dependent inspection commands always see one complete bundle state.

## UAT Pass Criteria
- All eight core test cases pass.
- Both edge case checks pass.
- The worktree exposes a stable `outputs/exports/eda/` bundle with truthful JSON/CSV/PNG/MD surfaces and explicit governance boundaries for downstream slices.
