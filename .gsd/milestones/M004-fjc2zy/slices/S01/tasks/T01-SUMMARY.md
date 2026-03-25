---
id: T01
parent: S01
milestone: M004-fjc2zy
provides:
  - Canonical showcase intake contract config for M001–M003 evidence surfaces with required/optional semantics and governance markers.
  - Deterministic intake validator + CLI that emits blocked-aware `manifest.json` and `validation_report.json` for downstream UI/runtime consumption.
  - Regression coverage for ready and missing branches, including reason-code shape and output-key drift protection.
key_files:
  - configs/showcase.yaml
  - src/showcase/intake_contract.py
  - scripts/build_showcase_intake.py
  - tests/test_showcase_intake_contract.py
  - .gsd/milestones/M004-fjc2zy/slices/S01/S01-PLAN.md
key_decisions:
  - Use config-driven surface declarations with two deterministic reason codes (`REQUIRED_ARTIFACT_MISSING`, `OPTIONAL_ARTIFACT_MISSING`) and intake-level `ready|blocked` rollup semantics.
patterns_established:
  - Contract-first intake pattern: YAML surface contract -> shared validator module -> CLI artifact emitter -> regression tests for ready/missing drift.
observability_surfaces:
  - python scripts/build_showcase_intake.py --config configs/showcase.yaml --output outputs/showcase/intake
  - outputs/showcase/intake/manifest.json
  - outputs/showcase/intake/validation_report.json
duration: 1h 10m
verification_result: partial
completed_at: 2026-03-24
blocker_discovered: false
---

# T01: Define intake contract and generate blocked-aware showcase diagnostics

**Added a canonical showcase intake contract + generator that emits deterministic blocked diagnostics and machine-readable readiness artifacts.**

## What Happened

I first applied the pre-flight observability fix by adding an explicit missing-path verification command (`pytest -k missing`) to `S01-PLAN.md`.

I then implemented the T01 deliverables:
- Added `configs/showcase.yaml` with required and optional M001/M003 intake surfaces plus governance/internal markers.
- Created `src/showcase/intake_contract.py` with deterministic status vocabulary (`ready|missing` per surface, `ready|blocked` intake rollup), stable reason codes, and generated timestamp propagation into each diagnostic row.
- Created `scripts/build_showcase_intake.py` CLI to load the contract and write both `manifest.json` and `validation_report.json` under caller-provided output directories.
- Added `tests/test_showcase_intake_contract.py` covering ready and missing branches, deterministic reason-code shape, and output file/key stability.

I also hardened the CLI script import path so direct script execution resolves `src.*` reliably.

## Verification

I ran task-level checks and the full slice verification list. T01 checks pass; downstream slice checks that depend on T02/T03 currently fail as expected because the Next.js shell and smoke script are not implemented yet.

I also directly inspected `outputs/showcase/intake/{manifest.json,validation_report.json}` and confirmed:
- intake `status` is emitted
- each surface has `required`, `status`, `reason`, `path`, and `generated_at`
- blocked required surfaces include explicit `requirement_key` + reason code
- optional missing surfaces are reported without adding to blocked list

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_showcase_intake_contract.py -q` | 0 | ✅ pass | 2.29s |
| 2 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_showcase_intake_contract.py -q -k missing` | 0 | ✅ pass | 2.14s |
| 3 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python scripts/build_showcase_intake.py --config configs/showcase.yaml --output outputs/showcase/intake && test -f outputs/showcase/intake/manifest.json && test -f outputs/showcase/intake/validation_report.json` | 0 | ✅ pass | 0.35s |
| 4 | `npm --prefix showcase run test -- --run` | 254 | ❌ fail | 0.11s |
| 5 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --base-url http://127.0.0.1:3000` | 2 | ❌ fail | 0.05s |
| 6 | `npm --prefix showcase run build` | 254 | ❌ fail | 0.10s |

## Diagnostics

Use these inspection surfaces:
1. Rebuild intake bundle:
   - `python scripts/build_showcase_intake.py --config configs/showcase.yaml --output outputs/showcase/intake`
2. Inspect machine-readable readiness:
   - `outputs/showcase/intake/manifest.json` (`status`, `summary`, per-surface diagnostics, blocked list)
   - `outputs/showcase/intake/validation_report.json` (`status`, `intake_status`, `reason_codes`, blocked diagnostics)

Current generated diagnostics correctly show explicit blocked required surfaces in this fresh worktree.

## Deviations

- None.

## Known Issues

- `showcase/` app scaffold does not exist yet (T02), so `npm --prefix showcase run test -- --run` and `npm --prefix showcase run build` fail with missing `showcase/package.json`.
- `scripts/showcase_smoke_check.py` does not exist yet (T03), so the slice smoke command fails.

## Files Created/Modified

- `configs/showcase.yaml` — Added canonical intake surface contract with required/optional artifacts and governance markers.
- `src/showcase/intake_contract.py` — Added contract loader/validator and deterministic blocked-aware diagnostic generation.
- `src/showcase/__init__.py` — Exported intake contract constants and builder API.
- `scripts/build_showcase_intake.py` — Added CLI generator for `manifest.json` and `validation_report.json`.
- `tests/test_showcase_intake_contract.py` — Added regression coverage for ready/missing branches and output-contract drift checks.
- `.gsd/milestones/M004-fjc2zy/slices/S01/S01-PLAN.md` — Added missing-path verification command and marked T01 complete.
