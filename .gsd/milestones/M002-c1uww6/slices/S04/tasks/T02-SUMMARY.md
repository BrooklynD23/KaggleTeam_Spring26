---
id: T02
parent: S04
milestone: M002-c1uww6
provides:
  - Track C helper regression coverage for deterministic ranking, monitoring-only summary framing, and config snapshot drift-key contract checks.
key_files:
  - tests/test_track_c_baseline_model.py
  - .gsd/milestones/M002-c1uww6/slices/S04/tasks/T02-PLAN.md
  - .gsd/milestones/M002-c1uww6/slices/S04/S04-PLAN.md
key_decisions:
  - Locked Track C monitoring framing with both required-phrase assertions and negative predictive-language assertions so summary contract drift fails loudly.
patterns_established:
  - Track C helper tests should validate both positive contract requirements (required phrases/keys) and negative framing guardrails (no predictive-model wording).
observability_surfaces:
  - python -m pytest tests/test_track_c_baseline_model.py
  - python -m pytest tests/test_track_c_baseline_model.py tests/test_track_c_common.py
  - tests/test_track_c_baseline_model.py::test_build_config_snapshot_includes_required_drift_keys
  - tests/test_track_c_baseline_model.py::test_build_summary_includes_monitoring_only_contract_phrases
duration: 45m
verification_result: passed
completed_at: 2026-03-23
blocker_discovered: false
---

# T02: Add Track C baseline helper regression tests

**Expanded Track C helper regression tests to lock monitoring-only summary/config contracts and deterministic ranking behavior.**

## What Happened

Updated `tests/test_track_c_baseline_model.py` to strengthen helper-level guardrails around S04 acceptance logic. The suite now asserts both required monitoring phrases and explicit exclusion of predictive-model framing in summary text, and adds direct config snapshot contract checks for `drift.slope_p_threshold` and `drift.rolling_window_months` plus expected artifact paths/row counts.

Also patched `.gsd/milestones/M002-c1uww6/slices/S04/tasks/T02-PLAN.md` with the missing `## Observability Impact` section called out in pre-flight.

Marked T02 complete in `.gsd/milestones/M002-c1uww6/slices/S04/S04-PLAN.md`.

## Verification

Verified the task-level suite and shared Track C helper suite, then executed the full S04 slice verification commands to confirm no regressions in runtime artifacts or diagnostics after the helper-test updates.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest tests/test_track_c_baseline_model.py` | 0 | ✅ pass | 0.95s |
| 2 | `python -m pytest tests/test_track_c_baseline_model.py tests/test_track_c_common.py` | 0 | ✅ pass | 1.02s |
| 3 | `python -m pytest tests/test_track_c_baseline_model.py tests/test_track_c_common.py tests/test_m002_modeling_contract.py` | 0 | ✅ pass | 1.04s |
| 4 | `python -m src.modeling.track_c.baseline --config configs/track_c.yaml && test -f outputs/modeling/track_c/summary.md && test -f outputs/modeling/track_c/metrics.csv && test -f outputs/modeling/track_c/config_snapshot.json && test -f outputs/modeling/track_c/drift_surface.parquet && test -f outputs/modeling/track_c/figures/monitoring_change_by_city.png` | 0 | ✅ pass | 1.93s |
| 5 | `python - <<'PY' ...artifact contract assertions for drift_surface/metrics/summary/config... PY` | 0 | ✅ pass | 0.39s |
| 6 | `python - <<'PY' ...invalid config path failure visibility check... PY` | 0 | ✅ pass | 0.63s |

## Diagnostics

Primary inspection surfaces for this task:

- `tests/test_track_c_baseline_model.py` helper tests for topic rollups, rolling-window stability, deterministic ranking, summary framing, and config snapshot keys.
- `python -m pytest tests/test_track_c_baseline_model.py -k summary`
- `python -m pytest tests/test_track_c_baseline_model.py -k config_snapshot`

Failure visibility confirmed:

- Summary framing drift fails via explicit missing-phrase or forbidden-language assertions.
- Config drift-key regressions fail with direct key-access assertions.
- Invalid config path remains inspectable through runtime failure diagnostics.

## Deviations

- Ran the full slice verification suite during T02 (in addition to task-level checks) to confirm contract stability immediately after helper-test changes.

## Known Issues

- None.

## Files Created/Modified

- `tests/test_track_c_baseline_model.py` — added summary negative-framing assertions and config snapshot drift-key/path contract coverage.
- `.gsd/milestones/M002-c1uww6/slices/S04/tasks/T02-PLAN.md` — added missing `## Observability Impact` section required by pre-flight.
- `.gsd/milestones/M002-c1uww6/slices/S04/S04-PLAN.md` — marked T02 as complete (`[x]`).
