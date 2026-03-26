---
estimated_steps: 4
estimated_files: 6
skills_used:
  - coding-standards
  - test
  - verification-loop
  - best-practices
---

# T03: Add synthesized PNG evidence visuals and close the CLI handoff

**Slice:** S02 — Export contract and evidence packaging
**Milestone:** M001-4q3lxl

## Description

Finish the bundle by adding the PNG surface required by `R002` and proving the real worktree can generate the full export handoff end-to-end. Because most analytical figures are absent in this stripped repo, the PNGs must be packaging-level evidence visuals derived from census counts and blocker status, not fabricated analytical results.

## Steps

1. Extend `scripts/package_eda_exports.py` to generate `outputs/exports/eda/figures/eda_overview.png` plus one `track_<x>_status_card.png` per track from census status counts, summary presence, and blocker metadata.
2. Keep the visuals explicitly packaging-oriented: label them as export/evidence status figures, not analytical findings, and use the same dispatcher/census truth source as the JSON/CSV/MD bundle.
3. Finish the CLI entrypoint so `python scripts/package_eda_exports.py` materializes the full bundle in the real worktree and logs or prints the key output paths/totals a future agent should inspect.
4. Re-run the focused pytest file and the slice-level CLI/file checks until JSON, CSV, PNG, and markdown surfaces all exist together under `outputs/exports/eda/`.

## Must-Haves

- [ ] The bundle emits one overview PNG and one per-track status-card PNG without depending on missing upstream analytical figures.
- [ ] The CLI succeeds in the current stripped worktree and writes the same export layout the tests assert in tmp repos.
- [ ] Final verification proves the repo now exposes JSON, CSV, PNG, and markdown export surfaces together, with Track D blocker visibility intact.

## Verification

- `python -m pytest tests/test_package_eda_exports.py`
- `python scripts/package_eda_exports.py && test -f outputs/exports/eda/figures/eda_overview.png && for track in track_a track_b track_c track_d track_e; do test -f outputs/exports/eda/figures/${track}_status_card.png; done`
- `python scripts/package_eda_exports.py && python - <<'PY'
from pathlib import Path
root = Path('outputs/exports/eda')
assert (root / 'manifest.json').is_file()
assert (root / 'manifest.csv').is_file()
assert (root / 'EXPORT_CONTRACT.md').is_file()
assert (root / 'figures' / 'eda_overview.png').is_file()
for track in ('track_a', 'track_b', 'track_c', 'track_d', 'track_e'):
    assert (root / 'tracks' / track / 'summary.md').is_file()
    assert (root / 'tracks' / track / 'manifest.json').is_file()
    assert (root / 'tracks' / track / 'artifacts.csv').is_file()
PY`

## Observability Impact

- Signals added/changed: the CLI now emits a complete bundle root with inspectable manifest totals and packaging-status PNGs derived from the same census source.
- How a future agent inspects this: run `python scripts/package_eda_exports.py`, then inspect `outputs/exports/eda/manifest.json`, `outputs/exports/eda/figures/eda_overview.png`, and `outputs/exports/eda/tracks/track_d/manifest.json`.
- Failure state exposed: missing source inputs, figure-generation failures, and layout drift are visible via failed file checks plus missing/blocker fields in the exported manifests.

## Inputs

- `scripts/package_eda_exports.py` — bundle generator and contract writers from T01/T02
- `tests/test_package_eda_exports.py` — regression suite to extend for PNG and CLI closure
- `outputs/exports/eda/EXPORT_CONTRACT.md` — generated contract that should now match the finished bundle layout
- `outputs/exports/eda/manifest.json` — root manifest that the CLI and PNG generation must keep in sync
- `outputs/exports/eda/tracks/track_d/manifest.json` — per-track manifest whose blocker visibility must survive the final integration step

## Expected Output

- `scripts/package_eda_exports.py` — finalized CLI and PNG-writing implementation
- `tests/test_package_eda_exports.py` — finalized regression coverage for PNG and CLI bundle generation
- `outputs/exports/eda/figures/eda_overview.png` — root packaging/evidence overview visual
- `outputs/exports/eda/figures/track_a_status_card.png` — representative per-track status figure
- `outputs/exports/eda/figures/track_d_status_card.png` — representative per-track figure preserving Track D blocker visibility
- `outputs/exports/eda/tracks/track_d/manifest.json` — final per-track manifest validated against the real CLI run
