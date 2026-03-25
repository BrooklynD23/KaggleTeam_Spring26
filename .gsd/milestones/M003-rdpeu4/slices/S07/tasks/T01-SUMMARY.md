---
id: T01
parent: S07
milestone: M003-rdpeu4
provides:
  - Sparse-support mitigation ready path that can emit non-empty pre/post deltas on tiny replay inputs while preserving existing status vocabulary.
key_files:
  - src/modeling/track_e/mitigation_experiment.py
  - tests/test_m003_track_e_mitigation_experiment.py
  - .gsd/KNOWLEDGE.md
key_decisions:
  - D044 — Use primary test-only evaluation first, then bounded sparse-all-splits fallback; treat no_correction_groups as non-blocking unless both paths fail.
patterns_established:
  - Machine-readable evaluation path diagnostics via lever_metadata.evaluation_diagnostics.active_path and sparse_fallback_activated.
observability_surfaces:
  - outputs/modeling/track_e/mitigation_experiment/manifest.json
  - outputs/modeling/track_e/mitigation_experiment/validation_report.json
  - outputs/modeling/track_e/mitigation_experiment/pre_post_delta.parquet
  - outputs/modeling/m003_closeout/manifest.json
duration: 2h
verification_result: passed
completed_at: 2026-03-24
blocker_discovered: false
---

# T01: Implement sparse-support mitigation ready path with deterministic diagnostics

**Added bounded sparse mitigation fallback evaluation with explicit path diagnostics so canonical sparse replay now emits a non-empty ready-for-closeout bundle and unblocks closeout handoff.**

## What Happened

I started with failing-first regression coverage for the sparse alignment seam: a new test fixture where fairness disparities are `split_name`-based now asserts ready-path behavior via sparse fallback, and an additional guard test asserts fail-closed behavior when even fallback cannot produce comparisons.

Then I updated `src/modeling/track_e/mitigation_experiment.py` by:
- preserving non-test correction fitting as-is,
- splitting signal reasons into hard-block (`no_disparity_rows`, `no_test_rows`, `no_non_test_rows`) vs non-blocking (`no_correction_groups`),
- keeping primary test-only evaluation semantics intact,
- adding a bounded sparse fallback (`sparse_all_splits`) that evaluates comparison-group-filtered rows and can compute disparities even when primary test-only alignment is empty,
- emitting machine-readable path diagnostics (`active_path`, `sparse_fallback_activated`, primary/fallback diagnostics, skipped comparisons) under `lever_metadata.evaluation_diagnostics`, and
- preserving status vocabulary (`ready_for_closeout`, `blocked_upstream`, `blocked_insufficient_signal`) plus deterministic blocked reasoning (`no_comparison_rows_after_alignment` etc.).

I also recorded a durable decision (D044) and a knowledge-log entry documenting the sparse split-name gotcha and the new triage surface.

## Verification

I ran the task-level required pytest commands, then ran the full slice verification commands (including canonical mitigation + closeout rerun and assertion scripts). All checks passed, including canonical replay statuses:
- mitigation: `manifest.status=ready_for_closeout`, non-empty `pre_post_delta.parquet`, diagnostics present,
- closeout: `manifest.status=ready_for_handoff`, `stage_rollup.readiness_block_stage_ids=[]`, S03 row marked `ready_for_closeout`.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_e_mitigation_experiment.py tests/test_m003_mitigation_contract.py -q` | 0 | ✅ pass | 7.97s |
| 2 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_e_mitigation_experiment.py -k "sparse or comparison_rows or ready_bundle" -q` | 0 | ✅ pass | 7.84s |
| 3 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_mitigation_contract.py tests/test_m003_track_e_mitigation_experiment.py tests/test_m003_mitigation_handoff_contract.py tests/test_m003_milestone_closeout_gate.py tests/test_m003_closeout_handoff_contract.py -q` | 0 | ✅ pass | 8.14s |
| 4 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.mitigation_experiment --config configs/track_e.yaml --intake-dir outputs/modeling/track_a/audit_intake --fairness-dir outputs/modeling/track_e/fairness_audit --output-dir outputs/modeling/track_e/mitigation_experiment` | 0 | ✅ pass | 5.78s |
| 5 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY' ... (mitigation artifact assertions) ... PY` | 0 | ✅ pass | 3.53s |
| 6 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.m003_closeout_gate --track-a-config configs/track_a.yaml --track-e-config configs/track_e.yaml --predictions outputs/modeling/track_a/predictions_test.parquet --metrics outputs/modeling/track_a/metrics.csv --candidate-metrics tests/fixtures/m003_candidate_metrics.csv --output-dir outputs/modeling/m003_closeout` | 0 | ✅ pass | 20.96s |
| 7 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY' ... (closeout artifact assertions) ... PY` | 0 | ✅ pass | 3.53s |
| 8 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY' ... (evaluation diagnostics observability assertions) ... PY` | 0 | ✅ pass | 0.07s |

## Diagnostics

Primary inspection points:
- `outputs/modeling/track_e/mitigation_experiment/manifest.json`
  - `status`, `row_counts.pre_post_rows`
  - `lever_metadata.fit_diagnostics`
  - `lever_metadata.evaluation_diagnostics.active_path`
  - `lever_metadata.evaluation_diagnostics.sparse_fallback_activated`
  - `insufficient_signal.reasons` (blocked branches)
- `outputs/modeling/track_e/mitigation_experiment/validation_report.json`
  - `phase`, `status`, `insufficient_signal`, `lever_metadata`
- `outputs/modeling/m003_closeout/manifest.json`
  - `status`, `compute_escalation_decision`, `stage_rollup.readiness_block_stage_ids`

## Deviations

Added one extra regression beyond the minimum plan scope: a blocked sparse-fallback test for deterministic fail-closed behavior when no subgroup comparisons are possible.

## Known Issues

None.

## Files Created/Modified

- `src/modeling/track_e/mitigation_experiment.py` — added bounded sparse fallback evaluation path, hard-vs-nonblocking insufficient-signal gating, and structured evaluation diagnostics.
- `tests/test_m003_track_e_mitigation_experiment.py` — added sparse ready-path regression and sparse fail-closed regression; extended fairness fixture helper for custom disparity rows.
- `.gsd/KNOWLEDGE.md` — added S03 sparse split-name mitigation gotcha and triage guidance.
- `.gsd/DECISIONS.md` — appended D044 for the sparse-fallback mitigation decision.
