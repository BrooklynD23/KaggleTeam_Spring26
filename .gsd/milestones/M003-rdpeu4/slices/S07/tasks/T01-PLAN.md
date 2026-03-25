---
estimated_steps: 5
estimated_files: 3
skills_used:
  - debug-like-expert
  - test
  - verification-loop
---

# T01: Implement sparse-support mitigation ready path with deterministic diagnostics

**Slice:** S07 — Mitigation ready-path delta closure + closeout rerun
**Milestone:** M003-rdpeu4

## Description

Unblock S03 by adding a bounded sparse-support evaluation path that can produce non-empty mitigation deltas on tiny canonical replay surfaces while preserving existing status vocabulary and fail-closed blocked behavior.

## Steps

1. Add failing-first regression coverage in `tests/test_m003_track_e_mitigation_experiment.py` for the tiny-support scenario that currently ends in `no_comparison_rows_after_alignment`, asserting the expected ready-path behavior once fixed.
2. Update `src/modeling/track_e/mitigation_experiment.py` to keep non-test correction fitting as-is but add a bounded sparse-evaluation fallback branch when primary test-group alignment yields zero comparison rows.
3. Preserve existing mitigation status vocabulary (`ready_for_closeout`, `blocked_upstream`, `blocked_insufficient_signal`) and ensure blocked reasons still surface deterministically when sparse fallback cannot produce valid rows.
4. Emit explicit diagnostics in `lever_metadata` and/or `insufficient_signal` describing evaluation path, evaluated subgroup types, skipped comparisons, and sparse fallback activation.
5. Update `tests/test_m003_mitigation_contract.py` as needed for additive diagnostics invariants, then re-run mitigation tests to confirm sparse-ready fixtures now produce non-empty `pre_post_delta.parquet` with `status=ready_for_closeout`.

## Must-Haves

- [ ] Sparse replay path can produce contract-valid non-empty pre/post rows without introducing new status strings.
- [ ] Blocked branches remain fail-closed with deterministic `insufficient_signal` diagnostics when mitigation evidence is truly insufficient.
- [ ] Added diagnostics make primary vs sparse-evaluation path machine-readable for downstream S05/M004 consumers.

## Verification

- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_e_mitigation_experiment.py tests/test_m003_mitigation_contract.py -q`
- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_e_mitigation_experiment.py -k "sparse or comparison_rows or ready_bundle" -q`

## Observability Impact

- Signals added/changed: mitigation manifest/validation diagnostics around sparse-evaluation activation and comparison-row alignment outcomes.
- How a future agent inspects this: inspect `outputs/modeling/track_e/mitigation_experiment/{manifest.json,validation_report.json}` and run `tests/test_m003_track_e_mitigation_experiment.py`.
- Failure state exposed: sparse-path failures surface explicit reason codes and skipped-comparison diagnostics instead of opaque empty-output behavior.

## Inputs

- `src/modeling/track_e/mitigation_experiment.py` — Existing S03 runtime currently blocking on sparse comparison alignment.
- `tests/test_m003_track_e_mitigation_experiment.py` — Runtime regression harness for ready/blocked mitigation branches.
- `tests/test_m003_mitigation_contract.py` — Contract assertions that must remain stable while diagnostics become richer.
- `.gsd/milestones/M003-rdpeu4/slices/S07/S07-RESEARCH.md` — Verified failure mode and recommended sparse-ready seam.

## Expected Output

- `src/modeling/track_e/mitigation_experiment.py` — Sparse-support mitigation evaluation logic with deterministic diagnostics.
- `tests/test_m003_track_e_mitigation_experiment.py` — Regression coverage for sparse-ready branch and preserved blocked semantics.
- `tests/test_m003_mitigation_contract.py` — Updated/additive contract assertions for any new diagnostics fields.
