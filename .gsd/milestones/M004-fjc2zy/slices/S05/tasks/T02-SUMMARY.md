---
id: T02
parent: S05
milestone: M004-fjc2zy
key_files:
  - src/showcase/demo_gate.py
  - scripts/run_showcase_demo_gate.py
  - tests/test_showcase_demo_gate.py
  - docs/showcase_local_runbook.md
  - outputs/showcase/verification/demo_gate_report.json
key_decisions:
  - Added a dedicated `governance_boundary` phase to centralize governance marker enforcement and no-live-query boundary checks with structured violation payloads.
  - Kept gate execution fail-closed at phase granularity while preserving per-command evidence within each phase for triage speed.
duration: ""
verification_result: passed
completed_at: 2026-03-25T05:28:30.761Z
blocker_discovered: false
---

# T02: Implemented a fail-closed one-command showcase demo gate with phase-level reporting and governance/no-live-query enforcement.

**Implemented a fail-closed one-command showcase demo gate with phase-level reporting and governance/no-live-query enforcement.**

## What Happened

Implemented `src/showcase/demo_gate.py` as the integrated orchestration layer for S05 with deterministic phase order (`build_artifacts`, `parity`, `frontend_test`, `frontend_build`, `runtime_smoke`, `governance_boundary`), per-command metadata capture, and fail-closed behavior on the first non-passing phase. Added `scripts/run_showcase_demo_gate.py` CLI to run the gate with `--config`, `--base-url`, and `--output`, print phase outcomes, and always persist a machine-readable report. Implemented governance boundary assertions that (1) enforce canonical governance markers (`internal_only=true`, `aggregate_safe=true`, `raw_review_text_allowed=false`) across config, story/tracks artifacts, and report/deck markers, (2) fail on any files under `showcase/app/api/**`, and (3) scan `showcase/app` + `showcase/lib` for disallowed live-query/runtime query patterns with file/line snippets in structured violations. Added `tests/test_showcase_demo_gate.py` to cover report schema emission, canonical ordering, fail-closed semantics, and representative governance/no-live-query violations. Updated `docs/showcase_local_runbook.md` so the integrated gate command is the primary local demo flow and retained the prior phase-by-phase path as fallback debugging guidance. Executed the integrated command successfully to produce `outputs/showcase/verification/demo_gate_report.json` with phase status and diagnostics.

## Verification

Ran targeted and slice-level verification. All required Python tests passed (demo gate and full showcase contract suite), frontend Vitest suite passed, frontend production build passed, integrated gate command passed all six phases, and report artifact existence check passed. Verified observability requirement by inspecting `outputs/showcase/verification/demo_gate_report.json` for phase ordering, per-phase command/result metadata, and governance boundary signals.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest tests/test_showcase_demo_gate.py -q` | 0 | ✅ pass | 246ms |
| 2 | `python -m pytest tests/test_showcase_smoke_check.py tests/test_showcase_demo_gate.py -q` | 0 | ✅ pass | 235ms |
| 3 | `python -m pytest tests/test_showcase_intake_contract.py tests/test_showcase_story_contract.py tests/test_showcase_track_contract.py tests/test_showcase_report_contract.py tests/test_showcase_deck_contract.py tests/test_showcase_parity_contract.py -q` | 0 | ✅ pass | 898ms |
| 4 | `npm --prefix showcase run test -- --run` | 0 | ✅ pass | 1911ms |
| 5 | `npm --prefix showcase run build` | 0 | ✅ pass | 17348ms |
| 6 | `python scripts/run_showcase_demo_gate.py --config configs/showcase.yaml --base-url http://127.0.0.1:3000 --output outputs/showcase/verification/demo_gate_report.json` | 0 | ✅ pass | 19890ms |
| 7 | `test -f outputs/showcase/verification/demo_gate_report.json` | 0 | ✅ pass | 0ms |


## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `src/showcase/demo_gate.py`
- `scripts/run_showcase_demo_gate.py`
- `tests/test_showcase_demo_gate.py`
- `docs/showcase_local_runbook.md`
- `outputs/showcase/verification/demo_gate_report.json`
