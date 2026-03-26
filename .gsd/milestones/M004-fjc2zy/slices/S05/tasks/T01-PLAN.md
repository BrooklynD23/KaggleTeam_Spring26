---
estimated_steps: 5
estimated_files: 3
skills_used:
  - verification-loop
  - e2e-testing
  - react-best-practices
---

# T01: Harden showcase smoke lifecycle and readiness error semantics

**Slice:** S05 — Integrated local demo hardening and governance gate
**Milestone:** M004-fjc2zy

## Description

Stabilize runtime smoke verification so S05 integrated gating is deterministic across repeated local runs and produces actionable failure diagnostics instead of ambiguous startup errors.

## Steps

1. Refactor `scripts/showcase_smoke_check.py` auto-start lifecycle to spawn/terminate in a process-group-aware way so descendants from `npm --prefix showcase run dev` are reliably cleaned up.
2. Split readiness handling into explicit categories (unreachable host/port vs reachable HTTP error vs timeout) and emit distinct failure messages without changing existing parity-check assertions.
3. Add regression tests in `tests/test_showcase_smoke_check.py` for cleanup semantics and readiness classification behavior, including an HTTP error path that must not be reported as "did not become ready".
4. Keep existing homepage/executive/track parity checks intact while adapting tests/helpers only where needed for new lifecycle behavior.
5. Add runbook troubleshooting note in `docs/showcase_local_runbook.md` covering the hardened smoke semantics for repeated runs.

## Must-Haves

- [ ] Auto-started dev-server process tree is cleaned up deterministically after smoke execution.
- [ ] Smoke failure output distinguishes unreachable URL from reachable HTTP-failing server.
- [ ] Existing parity checks for homepage/executive/tracks remain intact and passing.

## Verification

- `python -m pytest tests/test_showcase_smoke_check.py -q`
- `python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --base-url http://127.0.0.1:3000 --auto-start-showcase`

## Observability Impact

- Signals added/changed: explicit readiness failure class and clearer startup/cleanup diagnostics in smoke command output.
- How a future agent inspects this: run `python scripts/showcase_smoke_check.py ...` and inspect labeled PASS/FAIL plus startup failure line.
- Failure state exposed: stale-server leakage and HTTP-status failures become explicitly visible instead of collapsing into generic startup timeout errors.

## Inputs

- `scripts/showcase_smoke_check.py` — existing runtime parity and auto-start logic.
- `scripts/check_showcase_parity.py` — parity output conventions to keep diagnostics style aligned.
- `showcase/app/executive/page.tsx` — executive route structure used by smoke assertions.
- `showcase/app/tracks/page.tsx` — tracks route structure used by smoke assertions.

## Expected Output

- `scripts/showcase_smoke_check.py` — hardened lifecycle cleanup and readiness classification logic.
- `tests/test_showcase_smoke_check.py` — regression tests for process cleanup and error semantics.
- `docs/showcase_local_runbook.md` — troubleshooting note for new smoke behavior.
