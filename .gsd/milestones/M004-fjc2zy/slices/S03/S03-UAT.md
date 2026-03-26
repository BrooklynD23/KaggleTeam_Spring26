# S03: Track drill-down experience with canonical evidence pointers — UAT

**Milestone:** M004-fjc2zy
**Written:** 2026-03-25T04:48:22.024Z

## UAT Type

- UAT mode: mixed (artifact-driven + live-runtime)
- Why this mode is sufficient: S03’s contract is only complete when generated artifacts and rendered drill-down routes agree under local runtime conditions.

## Preconditions

1. Repository is at the S03 closeout state.
2. Install deps: `pip install -r requirements.txt` and `npm --prefix showcase install` (if node_modules absent).
3. Generate canonical artifacts:
   - `python scripts/build_showcase_intake.py --config configs/showcase.yaml --output outputs/showcase/intake`
   - `python scripts/build_showcase_story.py --config configs/showcase.yaml --intake outputs/showcase/intake/manifest.json --output outputs/showcase/story`
   - `python scripts/build_showcase_tracks.py --config configs/showcase.yaml --intake outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --output outputs/showcase/story`

## Smoke Test

Run:
`python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --base-url http://127.0.0.1:3000`

**Expected:** command exits 0 and prints PASS lines for homepage, executive, tracks index/detail, governance markers, evidence-field parity, and blocked M003 continuity rows.

## Test Cases

### 1. Canonical track artifact contract generation

1. Run `python -m pytest tests/test_showcase_track_contract.py -q`.
2. Run `python scripts/build_showcase_tracks.py --config configs/showcase.yaml --intake outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --output outputs/showcase/story`.
3. Open `outputs/showcase/story/tracks.json`.
4. **Expected:** tracks appear in fixed order `track_a`→`track_e`; each track has evidence rows with `surface_key`, `path`, `reason`, `requirement_key`; blocked rows are preserved (not omitted).

### 2. Tracks runtime rendering from canonical artifact

1. Run `npm --prefix showcase run test -- --run`.
2. Run `npm --prefix showcase run build`.
3. Start local app (`npm --prefix showcase run dev -- --hostname 127.0.0.1 --port 3000`) or rely on smoke auto-start.
4. Visit `/tracks` then `/tracks/track_a` and `/tracks/track_e`.
5. **Expected:** index and detail pages render governance markers and evidence diagnostics from `tracks.json`; blocked M003 surfaces remain explicitly visible.

### 3. Artifact-to-UI parity and route drift detection

1. Re-run smoke command with `--tracks`.
2. Inspect PASS labels for: `tracks.index.*`, `tracks.detail.*`, and `tracks.detail.blocked_m003.*` checks.
3. **Expected:** no FAIL labels; links `/tracks` and `/tracks/{trackKey}` resolve; evidence-row fields match artifact payload values.

## Edge Cases

### Base URL not pre-started

1. Ensure no server is listening on `127.0.0.1:3000`.
2. Run smoke command with default options.
3. **Expected:** smoke checker auto-starts local showcase dev server, completes parity checks, and exits 0.

### Missing required upstream M003 surfaces

1. Use current blocked-intake baseline (missing M003 artifacts).
2. Open `/tracks/track_e` and run smoke.
3. **Expected:** required blocked rows remain visible with `reason=REQUIRED_ARTIFACT_MISSING` and requirement keys (R009/R010/R022 continuity evidence).

## Failure Signals

- Smoke exits non-zero or prints FAIL labels for track route/evidence checks.
- `/tracks` index renders but per-track pages are missing expected evidence fields.
- Governance markers (`scope`, `internal_only`, `aggregate_safe`, `raw_review_text_allowed`) are missing or mismatch artifact values.
- Canonical order drifts from `track_a`→`track_e`.

## Requirements Proved By This UAT

- R011 — Local-hosted showcase now includes working track drill-down routes backed by static/generated artifacts with parity-verified runtime behavior.
- R012 (partial) — Narrative/evidence continuity extends into track drill-down evidence pointers using the canonical contract.

## Not Proven By This UAT

- Final report/deck parity generation (S04).
- Full integrated demo governance hardening and milestone-wide closure gates (S05).

## Notes for Tester

- Blocked diagnostics in this worktree are expected because upstream M003 surfaces are intentionally absent; blocked visibility is part of pass criteria.
- If smoke cannot reach base URL initially, default behavior now attempts auto-start; use `--no-auto-start-showcase` only when you want strict pre-start enforcement.
