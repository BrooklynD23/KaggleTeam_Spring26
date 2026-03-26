# S05: Integrated local demo hardening and governance gate — UAT

**Milestone:** M004-fjc2zy
**Written:** 2026-03-25T05:34:04.665Z

## UAT Type

- UAT mode: mixed (artifact-driven + live-runtime)
- Why this mode is sufficient: S05’s scope is operational assembly proof; correctness is demonstrated by deterministic command execution, machine-readable diagnostics, and runtime route parity/gov-boundary assertions.

## Preconditions

1. Worktree has Node/Python dependencies installed.
2. `configs/showcase.yaml` exists.
3. Local machine can bind `http://127.0.0.1:3000`.
4. From repo root, no manual server start is required (smoke can auto-start).

## Smoke Test

1. Run:
   `python scripts/run_showcase_demo_gate.py --config configs/showcase.yaml --base-url http://127.0.0.1:3000 --output outputs/showcase/verification/demo_gate_report.json`
2. **Expected:** CLI prints PASSED for `build_artifacts`, `parity`, `frontend_test`, `frontend_build`, `runtime_smoke`, `governance_boundary` and exits 0.
3. **Expected:** `outputs/showcase/verification/demo_gate_report.json` exists and has `gate_passed=true`.

## Test Cases

### 1. End-to-end integrated gate emits authoritative phase report

1. Execute the integrated gate command above.
2. Open `outputs/showcase/verification/demo_gate_report.json`.
3. Verify `phase_order` equals `build_artifacts -> parity -> frontend_test -> frontend_build -> runtime_smoke -> governance_boundary`.
4. Verify `summary.failed_phases == 0` and `summary.failing_phase_id == null`.
5. **Expected:** Report contains per-phase command metadata (command, exit_code, duration) for command-driven phases.

### 2. Narrative/report/deck continuity parity is enforced

1. Run:
   `python scripts/check_showcase_parity.py --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --report outputs/showcase/deliverables/showcase_report.md --deck outputs/showcase/deliverables/showcase_deck.md --output outputs/showcase/deliverables/parity_report.json`
2. Open `outputs/showcase/deliverables/parity_report.json`.
3. **Expected:** `parity_passed=true`, `summary.failed_checks=0`, and checks for `section_order`, `evidence_keys`, `pointer_fields`, `requirement_keys`, `governance_markers` are all passing.

### 3. Runtime smoke enforces route-level diagnostics and governance markers

1. Run:
   `python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --base-url http://127.0.0.1:3000`
2. Review stdout.
3. **Expected:** PASS lines include homepage readiness summary, executive governance markers, and track route/evidence pointer parity assertions with no FAIL rows.

## Edge Cases

### A. Unreachable base URL produces actionable readiness class

1. Run smoke with an unused port:
   `python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --base-url http://127.0.0.1:3999 --no-auto-start-showcase`
2. **Expected:** Non-zero exit and failure message explicitly classed as startup `unreachable` (not generic timeout text).

### B. Fail-closed gate semantics on phase failure

1. Intentionally break input to parity phase (example: point `--output` to unwritable location or provide malformed story/deck input in a controlled local test branch).
2. Run integrated gate.
3. **Expected:** Gate exits non-zero at first failing phase, records `summary.failing_phase_id`, and still writes `demo_gate_report.json` with failure payload.

## Failure Signals

- `showcase demo gate failed` CLI output with non-null `summary.failing_phase_id`.
- `governance_boundary` phase reports non-empty `api_route_files` or `live_query_violations > 0`.
- `parity_report.json` has `parity_passed=false` or non-empty failing check IDs.
- Smoke output contains FAIL rows for homepage/executive/tracks parity assertions.

## Requirements Proved By This UAT

- R011 — Demonstrates local-hosted showcase launchability via one-command integrated gate and passing frontend/runtime verifications.
- R012 — Demonstrates coherent cross-surface continuity by enforcing canonical parity checks between site/report/deck in gate flow.
- R013 (continuity support) — Demonstrates governance marker enforcement and no-live-query boundary checks in integrated gate output.

## Not Proven By This UAT

- Public cloud deployment behavior (out of scope).
- New modeling quality improvements for R009/R010 (this slice consumes continuity evidence; it does not re-run modeling research goals).

## Notes for Tester

- In stripped worktrees, blocked M003 evidence rows can be expected; gate pass criteria is continuity + governance correctness, not full upstream readiness.
- Use `outputs/showcase/verification/demo_gate_report.json` as the first-stop debugging artifact because it carries deterministic phase order and failure payloads.
