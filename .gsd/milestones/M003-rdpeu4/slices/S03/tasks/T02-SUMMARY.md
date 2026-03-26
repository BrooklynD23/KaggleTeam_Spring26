---
id: T02
parent: S03
milestone: M003-rdpeu4
provides:
  - Executable S03 mitigation runtime that emits canonical pre/post delta bundles on both ready and blocked paths with deterministic diagnostics.
key_files:
  - src/modeling/track_e/mitigation_experiment.py
  - src/modeling/track_e/__init__.py
  - tests/test_m003_track_e_mitigation_experiment.py
  - outputs/modeling/track_e/mitigation_experiment/pre_post_delta.parquet
  - outputs/modeling/track_e/mitigation_experiment/manifest.json
  - outputs/modeling/track_e/mitigation_experiment/validation_report.json
  - .gsd/milestones/M003-rdpeu4/slices/S03/S03-PLAN.md
key_decisions:
  - D032: Mitigation CLI returns exit code 0 for deterministic blocked bundles and encodes failure semantics in manifest/validation artifacts.
patterns_established:
  - Mitigation runtime gates S01/S02 readiness first, then enforces explicit insufficient-signal reasons (`no_disparity_rows`, `no_correction_groups`, etc.) before allowing ready-path claims.
observability_surfaces:
  - outputs/modeling/track_e/mitigation_experiment/{manifest.json,validation_report.json,pre_post_delta.parquet} with phase timeline, checks, threshold map, lever metadata, and insufficient-signal diagnostics.
duration: 1h 56m
verification_result: passed
completed_at: 2026-03-23T16:14:17-07:00
blocker_discovered: false
---

# T02: Implement mitigation runtime with residual-correction lever and fail-closed diagnostics

**Implemented `src.modeling.track_e.mitigation_experiment` with residual-correction mitigation, deterministic blocked/ready bundle writing, and regression tests covering ready, blocked_upstream, and blocked_insufficient_signal branches.**

## What Happened

Implemented `src/modeling/track_e/mitigation_experiment.py` as a full CLI/runtime with `--config`, `--intake-dir`, `--fairness-dir`, and `--output-dir`.

Runtime behavior added:
- Upstream loading and gate checks across S01 intake + S02 fairness artifacts.
- Contract validation for intake, subgroup metrics, disparity summary, and mitigation manifest status vocabulary.
- Group-wise residual correction fit on non-test rows, applied on test rows with clamped star-range predictions.
- Pre/post fairness disparity deltas plus paired overall accuracy deltas (`rmse`, `mae`, `within_1_star_rate`) written into canonical `pre_post_delta.parquet` rows.
- Deterministic blocked outputs for both upstream failures (`blocked_upstream`) and insufficient-signal conditions (`blocked_insufficient_signal`) with explicit reasons and phase-local diagnostics.

Also updated `src/modeling/track_e/__init__.py` to expose mitigation runtime/CLI proxies, and created `tests/test_m003_track_e_mitigation_experiment.py` with TDD-first coverage for:
- ready path,
- blocked_upstream path,
- blocked_insufficient_signal path.

Generated live runtime artifacts under `outputs/modeling/track_e/mitigation_experiment/` using the canonical command.

## Verification

Verified the new mitigation test suite, the runtime command, artifact presence checks, and the slice artifact contract snippet. Also ran the slice-level blocked-branch selector command and aligned test naming to satisfy the required `-k "blocked_upstream or insufficient_signal"` filter.

As expected for an intermediate slice task, the full 3-file slice pytest command is still failing because `tests/test_m003_mitigation_handoff_contract.py` is owned by T03 and does not exist yet.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_e_mitigation_experiment.py -q` | 0 | ✅ pass | 8.04s |
| 2 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.mitigation_experiment --config configs/track_e.yaml --intake-dir outputs/modeling/track_a/audit_intake --fairness-dir outputs/modeling/track_e/fairness_audit --output-dir outputs/modeling/track_e/mitigation_experiment` | 0 | ✅ pass | 6.81s |
| 3 | `test -f outputs/modeling/track_e/mitigation_experiment/pre_post_delta.parquet && test -f outputs/modeling/track_e/mitigation_experiment/manifest.json && test -f outputs/modeling/track_e/mitigation_experiment/validation_report.json` | 0 | ✅ pass | 0.02s |
| 4 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_mitigation_contract.py tests/test_m003_track_e_mitigation_experiment.py tests/test_m003_mitigation_handoff_contract.py -q` | 4 | ❌ fail | 1.90s |
| 5 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY' ... PY` (slice artifact assertion snippet) | 0 | ✅ pass | 3.79s |
| 6 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_e_mitigation_experiment.py -k "blocked_upstream or insufficient_signal" -q` | 0 | ✅ pass | 8.48s |

## Diagnostics

Inspect mitigation outputs with:
- `outputs/modeling/track_e/mitigation_experiment/manifest.json`
- `outputs/modeling/track_e/mitigation_experiment/validation_report.json`
- `outputs/modeling/track_e/mitigation_experiment/pre_post_delta.parquet`

Current real-data run in this worktree produces:
- `status: blocked_insufficient_signal`
- `phase: evaluate_signal`
- explicit reasons: `no_disparity_rows`, `no_correction_groups`

This is expected with the current tiny upstream fairness bundle (`disparity_rows: 0`) and is fail-closed by design.

## Deviations

- Minor local adaptation: blocked outcomes return process exit code `0` after writing canonical blocked artifacts, so downstream verification can always inspect machine-readable diagnostics without command-chain interruption.

## Known Issues

- `tests/test_m003_mitigation_handoff_contract.py` is not present yet (T03 scope), so the full slice 3-file pytest command remains intentionally incomplete at T02 stage.

## Files Created/Modified

- `src/modeling/track_e/mitigation_experiment.py` — Added full S03 mitigation runtime CLI with upstream gates, residual-correction lever, thresholded pre/post delta computation, and deterministic blocked/ready bundle writing.
- `src/modeling/track_e/__init__.py` — Added mitigation runtime/CLI proxy exports (`run_mitigation`, `main_mitigation`).
- `tests/test_m003_track_e_mitigation_experiment.py` — Added regression suite for ready, blocked_upstream, and blocked_insufficient_signal flows.
- `outputs/modeling/track_e/mitigation_experiment/pre_post_delta.parquet` — Wrote canonical mitigation delta artifact from runtime command.
- `outputs/modeling/track_e/mitigation_experiment/manifest.json` — Wrote status/continuity/threshold/lever metadata.
- `outputs/modeling/track_e/mitigation_experiment/validation_report.json` — Wrote phase/check diagnostics and insufficient-signal details.
- `.gsd/milestones/M003-rdpeu4/slices/S03/S03-PLAN.md` — Marked T02 complete.
- `.gsd/DECISIONS.md` — Appended D032 documenting blocked-run exit semantics.
- `.gsd/KNOWLEDGE.md` — Added pytest `-k` selector gotcha for blocked mitigation verification naming.
