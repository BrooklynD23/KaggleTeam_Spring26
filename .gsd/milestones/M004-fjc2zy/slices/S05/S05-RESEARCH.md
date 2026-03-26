# S05 Research — Integrated local demo hardening and governance gate

## Summary
S05 is a **targeted integration/hardening slice**. S01–S04 already built the core product surfaces (homepage/executive/tracks, report, deck, parity checker), but there is still no single integrated gate proving end-to-end demo readiness with governance and no-live-query assertions in one command.

Current system is close to done:
- Artifact builders exist (`build_showcase_intake.py`, `build_showcase_story.py`, `build_showcase_tracks.py`, `build_showcase_report.py`, `build_showcase_deck.py`).
- Contract parity exists for report/deck (`scripts/check_showcase_parity.py`).
- Runtime parity exists for routes (`scripts/showcase_smoke_check.py`).
- Runbook exists (`docs/showcase_local_runbook.md`) but is multi-step and manual.

Main S05 gap: **integration gate + hardening reliability**, not new narrative/UI architecture.

## Requirement focus (active requirements this slice owns/supports)
- **Direct closure support:**
  - **R011**: one-command local demo verification path across app + artifacts.
  - **R012**: integrated continuity proof using existing parity + runtime checks.
  - **R013**: governance-safe markers and no-raw-text posture must be explicitly gated.
  - **R022**: blocked closeout diagnostics must remain visible in integrated checks.
- **Continuity support:**
  - **R009**/**R010**: fairness/comparator continuity rows remain required evidence in executive/track smoke assertions.

## Skill notes applied
- **verification-loop**: use explicit gated phases (build/tests/checks), not ad-hoc spot checks.
  - Applied to S05 structure: artifact build → parity gate → frontend tests/build → runtime smoke → governance/no-live-query assertions.
- **react-best-practices**:
  - `async-parallel`: keep existing parallel loader pattern (`Promise.all` on homepage) and avoid adding serial blocking logic for hardening.
  - `server-serialization`: no new runtime data channels; keep artifact payload contract as canonical source.
- **e2e-testing**: avoid brittle timeout-only verification; prefer deterministic condition checks (already aligned with data-testid parity checks in smoke script).

## Skill discovery (suggest)
Installed and directly relevant:
- `verification-loop`
- `react-best-practices`
- `e2e-testing`

Not installed but relevant if S05 adds deeper Next.js runtime hardening:
- `npx skills add wshobson/agents@nextjs-app-router-patterns` (highest installs in Next.js search)

Not installed but relevant if optional deck export hardening is added to gate:
- `npx skills add softaworks/agent-toolkit@marp-slide`

## Implementation landscape

### Existing gate components (already present)
- `scripts/build_showcase_intake.py`
- `scripts/build_showcase_story.py`
- `scripts/build_showcase_tracks.py`
- `scripts/build_showcase_report.py`
- `scripts/build_showcase_deck.py`
- `scripts/check_showcase_parity.py`
- `scripts/showcase_smoke_check.py`
- `docs/showcase_local_runbook.md`

### Existing contract truth surfaces
- `outputs/showcase/intake/manifest.json`
- `outputs/showcase/story/sections.json`
- `outputs/showcase/story/tracks.json`
- `outputs/showcase/deliverables/showcase_report.md`
- `outputs/showcase/deliverables/showcase_deck.md`
- `outputs/showcase/deliverables/parity_report.json`

### Existing verification coverage
- Python contract tests:
  - `tests/test_showcase_intake_contract.py`
  - `tests/test_showcase_story_contract.py`
  - `tests/test_showcase_track_contract.py`
  - `tests/test_showcase_report_contract.py`
  - `tests/test_showcase_deck_contract.py`
  - `tests/test_showcase_parity_contract.py`
- UI tests:
  - `showcase/tests/homepage-shell.test.tsx`
  - `showcase/tests/executive-flow.test.tsx`
  - `showcase/tests/track-flow.test.tsx`
  - `showcase/tests/load-*.test.ts`

## Key findings / fragility to harden
1. **No one-command integrated gate yet.**
   - Runbook is manual sequence only; S05 should codify this into one executable command/script.

2. **Smoke checker process cleanup is fragile (reproducible).**
   - `scripts/showcase_smoke_check.py` auto-starts `npm --prefix showcase run dev`.
   - On success, child Next.js process can remain running (port 3000 still occupied) because parent termination does not fully reap descendants.
   - This causes stale-server interference across repeated demo runs.

3. **Smoke checker treats HTTP 500 as unreachable.**
   - `fetch_page()` uses `urllib.request.urlopen`; HTTP 500 raises `HTTPError` (subclass of `URLError`), currently handled as connection failure.
   - Result: misleading `auto-start ... did not become ready` failures when a stale server is actually up but serving errors.

4. **No explicit no-live-query assertion gate exists.**
   - Runtime behavior is artifact-driven by convention and prior tests, but S05 needs an explicit machine check for anti-feature boundary (R032 continuity in M004 context).

5. **Governance is checked for marker parity, but not packaged as final integrated gate output.**
   - Markers are validated in parity + smoke, but S05 should emit a single integrated verification artifact/report for closeout.

## Natural seams for planner decomposition
1. **Integrated gate script seam (Python, new):**
   - Add a single orchestrator CLI (likely under `scripts/`) that runs full S05 sequence and exits non-zero on any failure.
   - Should write one machine-readable gate report JSON under `outputs/showcase/verification/`.

2. **Smoke hardening seam (`scripts/showcase_smoke_check.py`):**
   - Fix server lifecycle handling (process-group aware cleanup).
   - Distinguish unreachable vs reachable-500 cases for clearer failure semantics.

3. **No-live-query/governance assertion seam (new script or integrated module):**
   - Static/runtime assertions for showcase codepaths:
     - no DB/parquet/duckdb imports in showcase runtime files,
     - no API route backend (`showcase/app/api/**`) introduced,
     - governance markers remain internal/aggregate-safe/raw-review-text disallow.

4. **Test seam (new pytest coverage):**
   - Add tests for integrated gate behavior and smoke cleanup semantics.
   - Preserve current subprocess-style testing pattern used by existing showcase script tests.

5. **Runbook seam (`docs/showcase_local_runbook.md`):**
   - Add “single command” path first; keep detailed step-by-step as fallback/debug.

## What to prove first (execution order)
1. **Gate contract first:** define exact pass/fail classes for S05 integrated check output.
2. **Smoke lifecycle hardening second:** eliminate port/process flakiness so integrated gate is deterministic.
3. **No-live-query and governance assertions third:** add explicit boundary checks to integrated gate.
4. **Runbook + test wiring last:** document single command and verify full suite in clean local run.

## Verification plan (recommended)
```bash
# Contract + builder suites
python -m pytest tests/test_showcase_intake_contract.py tests/test_showcase_story_contract.py tests/test_showcase_track_contract.py tests/test_showcase_report_contract.py tests/test_showcase_deck_contract.py tests/test_showcase_parity_contract.py -q

# Frontend suite + production build
npm --prefix showcase run test -- --run
npm --prefix showcase run build

# Integrated gate (expected new S05 command/script)
python scripts/run_showcase_demo_gate.py --config configs/showcase.yaml --base-url http://127.0.0.1:3000

# If smoke still uses auto-start dev server, verify cleanup explicitly
ss -ltnp | rg ':3000' && echo 'unexpected lingering server' && exit 1 || true
```

## Recommendation
Treat S05 as a **deterministic operations-hardening slice**:
- introduce one integrated local demo gate command,
- harden smoke server lifecycle + error classification,
- add explicit no-live-query/governance assertions to that gate,
- emit one machine-readable verification artifact for milestone closeout.

This closes the remaining milestone risk without changing narrative/data contracts already stabilized in S01–S04.
