---
estimated_steps: 5
estimated_files: 4
skills_used:
  - coding-standards
  - backend-patterns
  - verification-loop
---

# T01: Define intake contract and generate blocked-aware showcase diagnostics

**Slice:** S01 — Intake-locked showcase shell with visible readiness and blocked states
**Milestone:** M004-fjc2zy

## Description

Create the canonical S01 intake contract that checks expected M001–M003 evidence surfaces and emits deterministic readiness diagnostics. This task closes the highest-risk boundary first: proving intake truth in this worktree before UI story flow work begins.

## Steps

1. Add showcase intake configuration in `configs/showcase.yaml` with required and optional artifact paths plus governance/internal markers.
2. Implement a shared validator module in `src/showcase/intake_contract.py` that resolves paths, computes `ready|missing` status, and emits stable reason codes for blocked required inputs.
3. Implement `scripts/build_showcase_intake.py` to load config, run validation, and write `manifest.json` + `validation_report.json` under a caller-provided output directory.
4. Ensure generated diagnostics include enough context for downstream UI rendering (surface key, path, required flag, status, reason, timestamp).
5. Add regression tests in `tests/test_showcase_intake_contract.py` for both ready and missing-path branches.

## Must-Haves

- [ ] `scripts/build_showcase_intake.py` writes both `manifest.json` and `validation_report.json` to `outputs/showcase/intake/`.
- [ ] Missing required artifacts are represented as blocked diagnostics with deterministic reason codes.
- [ ] Optional artifacts are reported without blocking overall intake readiness.
- [ ] Pytest coverage fails loudly if contract keys, status vocabulary, or reason-code shape drifts.

## Verification

- `python -m pytest tests/test_showcase_intake_contract.py -q`
- `python scripts/build_showcase_intake.py --config configs/showcase.yaml --output outputs/showcase/intake && test -f outputs/showcase/intake/manifest.json && test -f outputs/showcase/intake/validation_report.json`

## Observability Impact

- Signals added/changed: intake `status`, per-surface readiness statuses, and blocked reason codes in generated JSON artifacts.
- How a future agent inspects this: rerun `python scripts/build_showcase_intake.py --config configs/showcase.yaml --output outputs/showcase/intake` and inspect `outputs/showcase/intake/*.json`.
- Failure state exposed: missing required artifact paths are explicitly listed with reason codes instead of implicit failure.

## Inputs

- `configs/base.yaml` — existing repo config conventions and path patterns to mirror
- `.gsd/milestones/M004-fjc2zy/M004-fjc2zy-ROADMAP.md` — S01 intake-locked contract expectations and blocked-state scope
- `.gsd/REQUIREMENTS.md` — active requirement boundaries relevant to S01 support coverage
- `scripts/pipeline_dispatcher.py` — contract-driven path/style reference used by current pipeline code

## Expected Output

- `configs/showcase.yaml` — canonical showcase intake surface contract
- `src/showcase/intake_contract.py` — intake validation and diagnostics logic
- `scripts/build_showcase_intake.py` — CLI generator for intake manifest and validation report
- `tests/test_showcase_intake_contract.py` — regression tests for ready/missing contract behavior
