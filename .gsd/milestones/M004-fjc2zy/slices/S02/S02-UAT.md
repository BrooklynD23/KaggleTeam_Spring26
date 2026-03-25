# S02: Executive trust-story flow from real exported artifacts — UAT

**Milestone:** M004-fjc2zy
**Written:** 2026-03-25T04:19:15.863Z

# S02: Executive trust-story flow from real exported artifacts — UAT

**Milestone:** M004-fjc2zy  
**Written:** 2026-03-24

## UAT Type

- UAT mode: mixed (artifact-driven + live-runtime)
- Why this mode is sufficient: S02 value depends on both generated story artifacts (`sections.json`) and real local Next.js rendering/parity diagnostics.

## Preconditions

1. Worktree: `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.gsd/worktrees/M004-fjc2zy`.
2. Intake manifest exists at `outputs/showcase/intake/manifest.json`.
3. Story artifacts generated:
   - `python scripts/build_showcase_story.py --config configs/showcase.yaml --intake outputs/showcase/intake/manifest.json --output outputs/showcase/story`
4. Showcase app dependencies installed.
5. Dev server running locally:
   - `npm --prefix showcase run dev -- --hostname 127.0.0.1 --port 3000`

## Smoke Test

Run:

`python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --base-url http://127.0.0.1:3000`

**Expected:** command exits 0 with PASS lines for homepage readiness diagnostics, executive heading/summary, governance markers, section ordering, and evidence-field parity.

## Test Cases

### 1. Story artifact contract generation stays canonical

1. Run `python -m pytest tests/test_showcase_story_contract.py -q`.
2. Generate story artifacts using build command above.
3. Inspect `outputs/showcase/story/sections.json` for section order:
   `prediction`, `surfacing`, `onboarding`, `monitoring`, `accountability`.
4. **Expected:** tests pass; `sections.json` and `validation_report.json` exist; each section includes requirement mapping and evidence rows with `surface_key`, `path`, `reason`, `requirement_key`.

### 2. Executive route renders generated artifact content with governance markers

1. Open `http://127.0.0.1:3000/executive` in browser.
2. Verify page shows executive heading and section status chips.
3. Verify governance card shows: internal-only scope, aggregate-safe = true, raw review text allowed = false.
4. **Expected:** UI values match story artifact content and governance markers are visible without fallback placeholders hiding blocked states.

### 3. Homepage shell preserves readiness diagnostics and executive-first flow

1. Open `http://127.0.0.1:3000/`.
2. Confirm readiness summary and blocked surfaces list are visible.
3. Follow executive navigation CTA/link to `/executive`.
4. **Expected:** homepage still reports intake blocked diagnostics from manifest; navigation lands on executive route with same contract-driven status semantics.

### 4. Reduced-motion behavior remains usable

1. Enable reduced-motion in browser/system settings (or emulate `prefers-reduced-motion`).
2. Reload `/executive`.
3. Traverse sections and evidence lists.
4. **Expected:** content remains fully readable/interactive; transitions degrade to no-motion-safe behavior (no reliance on animation for comprehension).

## Edge Cases

### Missing story artifact file

1. Temporarily move `outputs/showcase/story/sections.json` out of place.
2. Load `/executive`.
3. **Expected:** deterministic fallback content appears with explicit blocked diagnostics; app does not crash.

### Invalid story JSON

1. Replace `sections.json` with malformed JSON.
2. Reload `/executive`.
3. **Expected:** loader falls back to blocked diagnostic state (`STORY_READ_FAILURE` semantics) and keeps canonical section structure.

### Missing upstream evidence surfaces in intake

1. Use current partial worktree where many M001–M003 surfaces are absent.
2. Regenerate story + run smoke check.
3. **Expected:** sections/evidence remain visible as blocked with explicit `reason` and `requirement_key`; no silent success rendering.

## Failure Signals

- Smoke check exits non-zero.
- `/executive` missing one or more canonical section IDs.
- Governance markers absent or contradictory to contract.
- Evidence rows missing pointer fields (`surface_key`, `path`, `reason`, `requirement_key`).
- UI silently hides blocked surfaces instead of exposing diagnostics.

## Requirements Proved By This UAT

- R011 — local-hosted Next.js runtime now renders executive artifact-driven flow and passes live smoke verification.
- R012 — canonical business-story section ordering and claim-to-evidence mapping are generated and rendered consistently.
- R013 — governance boundary markers remain visible in executive UI and artifact surfaces.

## Not Proven By This UAT

- Full report/deck parity generation (S04).
- Track drill-down page depth and per-track UX paths (S03).
- Final integrated milestone hardening checks across website/report/deck (S05).

## Notes for Tester

- `showcase_smoke_check.py` requires the dev server to be running at `--base-url`; it does not auto-start Next.js.
- In this worktree snapshot, many upstream artifacts are intentionally missing; blocked diagnostics are expected PASS behavior, not a failure.
