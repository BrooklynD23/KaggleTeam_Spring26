---
id: T01
parent: S05
milestone: M004-fjc2zy
key_files:
  - scripts/showcase_smoke_check.py
  - tests/test_showcase_smoke_check.py
  - docs/showcase_local_runbook.md
key_decisions:
  - Use explicit readiness-state classification (`ready`/`unreachable`/`http_error`/`timeout`) to make smoke startup failures actionable and machine-parseable in logs.
  - Use process-group-scoped lifecycle management for auto-started `npm --prefix showcase run dev` so cleanup is deterministic for repeated local smoke executions.
duration: ""
verification_result: mixed
completed_at: 2026-03-25T05:21:56.541Z
blocker_discovered: false
---

# T01: Hardened showcase smoke startup/cleanup semantics with explicit readiness error classes and regression tests.

**Hardened showcase smoke startup/cleanup semantics with explicit readiness error classes and regression tests.**

## What Happened

Implemented lifecycle hardening in `scripts/showcase_smoke_check.py` by introducing process-group-aware server startup/teardown (`start_new_session` + group SIGTERM/SIGKILL on POSIX), ensuring auto-started Next.js descendants are cleaned deterministically across repeated runs. Refactored readiness behavior to classify failures into explicit states (`unreachable`, `http_error`, `timeout`) via `ReadinessResult` and `classify_readiness_failure`, then surfaced distinct startup messages in CLI output (`showcase startup unreachable`, `showcase startup HTTP error`, `showcase startup timeout`) instead of collapsing into the old generic readiness wording. Preserved existing homepage/executive/tracks parity assertion logic and route checks unchanged. Added new regression test file `tests/test_showcase_smoke_check.py` covering: (1) process-group startup configuration, (2) process-group cleanup escalation semantics, (3) HTTP readiness classification, and (4) main-path messaging to ensure HTTP failures are not reported as “did not become ready.” Updated `docs/showcase_local_runbook.md` with a troubleshooting subsection documenting the hardened readiness classes and deterministic process-tree cleanup behavior.

## Verification

Task-level verification passed: `python -m pytest tests/test_showcase_smoke_check.py -q` and `python scripts/showcase_smoke_check.py ... --auto-start-showcase` both returned exit code 0. Slice-level verification was executed as required for this intermediate task: contract pytest suite passed, showcase frontend test/build passed, while demo-gate-specific checks failed because `tests/test_showcase_demo_gate.py` and `scripts/run_showcase_demo_gate.py` are not present yet in this worktree (expected for this stage). Observability impact verified directly via smoke CLI output now emitting labeled startup failure classes and still providing deterministic PASS/FAIL parity lines.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest tests/test_showcase_smoke_check.py -q` | 0 | ✅ pass | 199ms |
| 2 | `python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --base-url http://127.0.0.1:3000 --auto-start-showcase` | 0 | ✅ pass | 268ms |
| 3 | `python -m pytest tests/test_showcase_smoke_check.py tests/test_showcase_demo_gate.py -q` | 4 | ❌ fail | 149ms |
| 4 | `python -m pytest tests/test_showcase_intake_contract.py tests/test_showcase_story_contract.py tests/test_showcase_track_contract.py tests/test_showcase_report_contract.py tests/test_showcase_deck_contract.py tests/test_showcase_parity_contract.py -q` | 0 | ✅ pass | 925ms |
| 5 | `npm --prefix showcase run test -- --run` | 0 | ✅ pass | 2191ms |
| 6 | `npm --prefix showcase run build` | 0 | ✅ pass | 17698ms |
| 7 | `python scripts/run_showcase_demo_gate.py --config configs/showcase.yaml --base-url http://127.0.0.1:3000 --output outputs/showcase/verification/demo_gate_report.json` | 2 | ❌ fail | 16ms |
| 8 | `test -f outputs/showcase/verification/demo_gate_report.json` | 1 | ❌ fail | 1ms |


## Deviations

`tests/test_showcase_smoke_check.py` did not exist in the worktree; created it from scratch to satisfy the task plan regression scope.

## Known Issues

Slice-level demo gate checks currently fail because `tests/test_showcase_demo_gate.py` and `scripts/run_showcase_demo_gate.py` are not present yet, and therefore `outputs/showcase/verification/demo_gate_report.json` is not generated in this task.

## Files Created/Modified

- `scripts/showcase_smoke_check.py`
- `tests/test_showcase_smoke_check.py`
- `docs/showcase_local_runbook.md`
