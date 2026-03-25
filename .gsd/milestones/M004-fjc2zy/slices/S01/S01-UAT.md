# S01: Intake-locked showcase shell with visible readiness and blocked states — UAT

**Milestone:** M004-fjc2zy
**Written:** 2026-03-25T03:50:01.369Z

# S01: Intake-locked showcase shell with visible readiness and blocked states — UAT

**Milestone:** M004-fjc2zy  
**Written:** 2026-03-24

## UAT Type

- UAT mode: mixed (artifact-driven + live-runtime)
- Why this mode is sufficient: S01 value is the contract between generated intake artifacts and visible homepage diagnostics; we must prove both artifact generation and runtime rendering/smoke behavior.

## Preconditions

1. Worktree is at `M004-fjc2zy` slice S01 completion state.
2. Python interpreter with pytest available (recommended: `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python`).
3. Node dependencies installed under `showcase/`.
4. Port 3000 is free for local dev server.

## Smoke Test

1. Build intake artifacts:
   - `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python scripts/build_showcase_intake.py --config configs/showcase.yaml --output outputs/showcase/intake`
2. Start app:
   - `npm --prefix showcase run dev`
3. In a second terminal, run:
   - `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --base-url http://127.0.0.1:3000`
4. **Expected:** Smoke script prints PASS checks for heading/status/counts/blocked rows and exits 0.

## Test Cases

### 1. Intake contract emits deterministic blocked diagnostics in fresh worktree

1. Run `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_showcase_intake_contract.py -q`.
2. Run `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_showcase_intake_contract.py -q -k missing`.
3. Run intake build command and open `outputs/showcase/intake/manifest.json`.
4. **Expected:** Tests pass; manifest status is `blocked` in this worktree; blocked entries include required missing surfaces with reason `REQUIRED_ARTIFACT_MISSING` and requirement keys.

### 2. Homepage renders readiness summary + blocked required surface rows

1. Start `npm --prefix showcase run dev`.
2. Load `http://127.0.0.1:3000`.
3. Confirm visible sections: readiness heading, status chip, counts, blocked section.
4. Verify blocked rows display `surface_key`, `path`, `reason`, and `requirement_key` text values.
5. **Expected:** Homepage shows explicit blocked diagnostics instead of empty placeholders; required missing artifact paths are human-readable and machine-parseable.

### 3. Frontend contract/build stability

1. Run `npm --prefix showcase run test -- --run`.
2. Run `npm --prefix showcase run build`.
3. **Expected:** Vitest suite passes (including readiness/homepage tests) and production build succeeds.

## Edge Cases

### Intake manifest unavailable at runtime

1. Temporarily move or rename `outputs/showcase/intake/manifest.json`.
2. Load homepage (or run homepage tests that mock unavailable load).
3. **Expected:** Shell still renders with deterministic fallback state (`intake_unavailable` / `INTAKE_MANIFEST_UNAVAILABLE`) and visible fallback note; app does not crash.

### Optional surfaces missing while required surfaces drive blocked list

1. Build intake in the current fresh worktree.
2. Inspect `manifest.json` and `validation_report.json`.
3. **Expected:** Optional missing surfaces are counted in missing totals but do not create required-block list entries; required missing surfaces remain in blocked diagnostics.

## Failure Signals

- Smoke script exits non-zero or reports missing expected status/count/blocked text.
- Homepage renders but omits blocked section or required blocked rows.
- Intake manifest/validation artifacts are not generated or are missing summary/blocked keys.
- Build/test failures in `showcase` or intake contract pytest suite.

## Requirements Proved By This UAT

- R011 — Proves a real local-hosted Next.js showcase shell exists and can be started/tested/built with intake-driven diagnostics visible.
- R013 (continuity support) — Proves governance/internal-only diagnostic framing is surfaced through intake artifacts and homepage status rendering.
- R022 (continuity support) — Proves missing M003 closeout surfaces are explicitly diagnosed as blocked, preserving closeout evidence visibility instead of silent failure.

## Not Proven By This UAT

- Full executive trust-story flow content and section transitions (owned by S02).
- Track drill-down pages/evidence pointer UX (owned by S03).
- Report/deck generation parity with website narrative/evidence map (owned by S04/S05).
- End-to-end milestone hardening/parity/no-live-query governance gate (owned by S05).

## Notes for Tester

- In this worktree snapshot, blocked state is expected because many upstream M001/M003 artifacts are intentionally absent.
- Use the project virtualenv interpreter path above if system `python` lacks pytest.
- Keep local server running during smoke check; the script validates rendered HTML against the same manifest used by runtime.
