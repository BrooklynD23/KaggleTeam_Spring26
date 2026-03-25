---
id: T02
parent: S06
milestone: M003-rdpeu4
provides:
  - S02 fairness runtime now enforces non-empty subgroup/disparity sufficiency and emits deterministic `signal_sufficiency` diagnostics for primary, fallback, and insufficient branches.
key_files:
  - src/modeling/track_e/fairness_audit.py
  - tests/test_m003_track_e_fairness_audit.py
  - configs/track_e.yaml
key_decisions:
  - Adopted deterministic aggregate-safe fallback strategy `split_name_metrics` behind `fairness.signal_sufficiency.fallback.*` config, while keeping fairness manifest status vocabulary unchanged.
patterns_established:
  - Sufficiency truth is encoded via additive diagnostics (`signal_sufficiency`) and fail-closed status (`blocked_upstream`) instead of introducing new status strings.
observability_surfaces:
  - outputs/modeling/track_e/fairness_audit/{manifest.json,validation_report.json,subgroup_metrics.parquet,disparity_summary.parquet} with `signal_sufficiency`, fallback phase entries, and row-count deltas.
duration: ~2h
verification_result: passed
completed_at: 2026-03-23
blocker_discovered: false
---

# T02: Implement S02 fairness sufficiency gate with approved fallback subgroup strategy

**Implemented a fail-closed fairness sufficiency gate with deterministic fallback replay (`split_name_metrics`) so S02 only reports `ready_for_mitigation` when subgroup and disparity signal are non-empty, with explicit insufficiency diagnostics otherwise.**

## What Happened

I followed TDD for this task: first expanded `tests/test_m003_track_e_fairness_audit.py` to cover three runtime branches (primary sufficient, fallback sufficient, and blocked insufficient), ran the suite to confirm red failures, then implemented runtime behavior to satisfy those tests.

Runtime changes in `src/modeling/track_e/fairness_audit.py`:
- Added post-primary signal sufficiency evaluation.
- Added configured fallback execution via `fairness.signal_sufficiency.fallback`.
- Implemented `split_name_metrics` fallback (aggregate-only grouping by `split_name`) for sparse primary contexts.
- Added deterministic `signal_sufficiency` payload construction (`outcome`, `reasons`, `fallback_metadata`, row deltas, primary/selected counts).
- Validated `signal_sufficiency` payloads with `validate_signal_sufficiency_payload(...)` and surfaced checks in validation output.
- Enforced status gating:
  - `ready_for_mitigation` only when outcome is `primary_sufficient` or `fallback_sufficient`.
  - `blocked_upstream` + `validation.status=fail` when outcome is `insufficient`.
- Updated blocked bundle writing to preserve computed subgroup/disparity artifacts and include `signal_sufficiency` + `row_counts` in blocked manifests for deterministic triage.

Config changes in `configs/track_e.yaml`:
- Added fallback config keys with conservative documented defaults:
  - `fairness.signal_sufficiency.fallback.enabled: true`
  - `fairness.signal_sufficiency.fallback.strategy: split_name_metrics`
  - `fairness.signal_sufficiency.fallback.min_group_size: 1`

Canonical replay now lands in a truthful fallback-ready state on this sparse worktree:
- `manifest.status=ready_for_mitigation`
- `signal_sufficiency.outcome=fallback_sufficient`
- `row_counts.primary_subgroup_rows=0`, `primary_disparity_rows=0`
- `row_counts.subgroup_rows=3`, `disparity_rows=8` after fallback.

## Verification

I verified task-level and slice-level gates:
- Focused fairness runtime tests now pass with branch coverage for primary/fallback/insufficient sufficiency outcomes.
- Full S06 fairness suites pass (`contract + runtime + handoff`).
- Canonical fairness replay emits `signal_sufficiency` in both manifest and validation and respects ready/blocked semantics.
- Canonical mitigation smoke now confirms that when fairness is ready, mitigation blockage no longer cites `no_disparity_rows`.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_e_fairness_audit.py -q` | 0 | ✅ pass | 5.76s |
| 2 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_fairness_audit_contract.py tests/test_m003_track_e_fairness_audit.py tests/test_m003_fairness_audit_handoff_contract.py -q` | 0 | ✅ pass | 7.97s |
| 3 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.fairness_audit --config configs/track_e.yaml --intake-dir outputs/modeling/track_a/audit_intake --output-dir outputs/modeling/track_e/fairness_audit` | 0 | ✅ pass | 6.32s |
| 4 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY' ... s06 t02 runtime sufficiency verified ... PY` | 0 | ✅ pass | 0.08s |
| 5 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY' ... m003 s06 fairness sufficiency contract verified ... PY` | 0 | ✅ pass | 0.07s |
| 6 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.mitigation_experiment --config configs/track_e.yaml --intake-dir outputs/modeling/track_a/audit_intake --fairness-dir outputs/modeling/track_e/fairness_audit --output-dir outputs/modeling/track_e/mitigation_experiment` | 0 | ✅ pass | 5.83s |
| 7 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY' ... m003 s06 mitigation readiness smoke verified ... PY` | 0 | ✅ pass | 0.07s |

## Diagnostics

Use these surfaces for branch triage:
- `outputs/modeling/track_e/fairness_audit/manifest.json`
  - `status`, `row_counts`, `signal_sufficiency.outcome`, `signal_sufficiency.reasons`, fallback `row_deltas`.
- `outputs/modeling/track_e/fairness_audit/validation_report.json`
  - `signal_sufficiency`, `checks[]`, `phases[]` (`fallback_subgroups`, `evaluate_signal`).
- `tests/test_m003_track_e_fairness_audit.py`
  - direct runtime branch coverage for primary/fallback/insufficient outcomes.

## Deviations

None.

## Known Issues

- Even with S02 fallback sufficiency active, canonical mitigation remains `blocked_insufficient_signal` in this sparse replay due `no_correction_groups` (not `no_disparity_rows`), which is expected follow-on scope for S07.

## Files Created/Modified

- `src/modeling/track_e/fairness_audit.py` — Added sufficiency gate, fallback execution path, `signal_sufficiency` diagnostics emission, and fail-closed blocked semantics for insufficient signal.
- `tests/test_m003_track_e_fairness_audit.py` — Added branch tests for primary sufficient, fallback sufficient, and blocked insufficient paths; updated runtime assertions for sufficiency payloads.
- `configs/track_e.yaml` — Added explicit fallback strategy config keys under `fairness.signal_sufficiency.fallback` with governance-aligned comments.
- `.gsd/milestones/M003-rdpeu4/slices/S06/S06-PLAN.md` — Marked T02 complete (`[x]`).
- `.gsd/DECISIONS.md` — Appended D042 documenting the chosen fairness fallback strategy and status compatibility choice.
- `.gsd/KNOWLEDGE.md` — Added S06 runtime/triage gotcha on `fallback_sufficient` behavior and downstream mitigation reason-shift expectations.
