---
id: S03
parent: M003-rdpeu4
milestone: M003-rdpeu4
provides:
  - Executable mitigation runtime (`python -m src.modeling.track_e.mitigation_experiment`) that consumes S01/S02 artifacts and emits canonical pre/post mitigation bundle outputs.
  - Strict mitigation contract surface (schema + status vocabulary + handoff continuity tests) for S05 closeout consumption.
  - Fail-closed blocked semantics (`blocked_upstream`, `blocked_insufficient_signal`) with machine-readable diagnostics instead of narrative-only mitigation claims.
requires:
  - slice: M003-rdpeu4/S02
    provides: Canonical fairness bundle with disparity metrics plus `baseline_anchor`/`split_context` continuity context.
affects:
  - M003-rdpeu4/S04
  - M003-rdpeu4/S05
  - M004-fjc2zy
key_files:
  - src/modeling/common/mitigation_contract.py
  - src/modeling/common/__init__.py
  - src/modeling/track_e/mitigation_experiment.py
  - src/modeling/track_e/__init__.py
  - src/modeling/README.md
  - tests/test_m003_mitigation_contract.py
  - tests/test_m003_track_e_mitigation_experiment.py
  - tests/test_m003_mitigation_handoff_contract.py
  - .gsd/milestones/M003-rdpeu4/slices/S03/S03-UAT.md
  - outputs/modeling/track_e/mitigation_experiment/pre_post_delta.parquet
  - outputs/modeling/track_e/mitigation_experiment/manifest.json
  - outputs/modeling/track_e/mitigation_experiment/validation_report.json
key_decisions:
  - D031: Canonical mitigation lever/status semantics are group-wise residual correction with explicit `ready_for_closeout`/blocked vocab.
  - D032: CLI returns exit code 0 for blocked outcomes after writing canonical diagnostics artifacts.
  - D033: Canonical replay command and authoritative bundle root are locked to `outputs/modeling/track_e/mitigation_experiment/`.
  - D034: Mitigation schema/status validators are centralized in `src/modeling/common/mitigation_contract.py` and re-exported via `src.modeling.common`.
patterns_established:
  - Contract-first mitigation delivery: shared contract module → runtime implementation → handoff continuity regression tests.
  - Fail-closed mitigation gating: no disparity/correction signal yields deterministic `blocked_insufficient_signal` instead of vacuous pre/post claims.
  - Handoff continuity is enforced by exact `baseline_anchor` + `split_context` equality checks from S02 into S03 manifest and validation artifacts.
observability_surfaces:
  - outputs/modeling/track_e/mitigation_experiment/manifest.json
  - outputs/modeling/track_e/mitigation_experiment/validation_report.json
  - outputs/modeling/track_e/mitigation_experiment/pre_post_delta.parquet
  - tests/test_m003_track_e_mitigation_experiment.py
  - tests/test_m003_mitigation_handoff_contract.py
  - src/modeling/README.md
duration: 3h54m
verification_result: passed
completed_at: 2026-03-23
---

# S03: One mitigation lever with pre/post fairness-accuracy deltas

**S03 closed successfully.** The slice now provides one executable mitigation lever with canonical pre/post fairness+accuracy delta contract outputs, plus deterministic blocked diagnostics when upstream readiness or subgroup signal is insufficient.

## What Happened

S03 integrated all three planned tasks into one handoff-safe mitigation surface:

1. **T01 contract hardening**
   - Added `src/modeling/common/mitigation_contract.py` with required pre/post delta schema, status vocabulary, and strict threshold-boolean validation.
   - Added deterministic validator diagnostics for missing columns, malformed threshold flags, and invalid statuses.

2. **T02 mitigation runtime**
   - Implemented `src.modeling.track_e.mitigation_experiment` CLI that gates on S01/S02 readiness, fits group-wise residual corrections on non-test rows, applies/clamps on test rows, and writes canonical bundle artifacts.
   - Runtime emits explicit blocked semantics (`blocked_upstream`, `blocked_insufficient_signal`) with phase-local reasons and still writes artifacts for downstream automation.

3. **T03 handoff closure**
   - Added `tests/test_m003_mitigation_handoff_contract.py` to lock continuity (`baseline_anchor`, `split_context`), required delta schema, status vocabulary, and redaction constraints.
   - Updated docs/UAT surfaces to one canonical command/path and deterministic replay+triage flow.

As slice closer, I reran every slice-plan verification command, validated observability fields in live artifacts, updated requirement state notes (R009/R010/R012), appended missing decisions (D033/D034), added one non-obvious runtime knowledge note, refreshed project state, and marked S03 complete in the milestone roadmap.

## Verification

All slice-plan verification checks passed in this worktree:

| # | Command | Result |
|---|---|---|
| 1 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_mitigation_contract.py tests/test_m003_track_e_mitigation_experiment.py tests/test_m003_mitigation_handoff_contract.py -q` | ✅ 11 passed |
| 2 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.mitigation_experiment --config configs/track_e.yaml --intake-dir outputs/modeling/track_a/audit_intake --fairness-dir outputs/modeling/track_e/fairness_audit --output-dir outputs/modeling/track_e/mitigation_experiment` | ✅ exit 0 (writes canonical bundle; current data resolves to blocked-insufficient-signal) |
| 3 | Slice-plan artifact assertion snippet (required files/status branches/schema/redaction checks) | ✅ prints `m003 s03 mitigation bundle verified` |
| 4 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_e_mitigation_experiment.py -k "blocked_upstream or insufficient_signal" -q` | ✅ 2 passed, 1 deselected |

## Observability / Diagnostics Confirmed

Declared S03 observability surfaces are live:

- `manifest.json` exposes:
  - `status`, `phase`, `validation_status`
  - `insufficient_signal.reasons` and fit diagnostics
  - `threshold_checks`, `lever_metadata`
  - continuity payloads: `baseline_anchor`, `split_context`
- `validation_report.json` exposes:
  - check-level `checks[]`
  - phase timeline `phases[]`
  - `missing_inputs`, `insufficient_signal`, and upstream paths

Current replay state is **fail-closed by design**:
- `manifest.status = blocked_insufficient_signal`
- reasons include `no_disparity_rows` and `no_correction_groups`
- bundle still writes deterministically for S05 triage.

## Requirements Advanced

- **R009 (active):** advanced from S02 fairness-only proof to mitigation-runtime proof with canonical pre/post-delta schema/status surfaces and blocked diagnostics.
- **R010 (active):** S03 now preserves comparator prerequisites by locking mitigation handoff continuity/status/path semantics for downstream materiality gating.
- **R012 (active):** continuity support advanced with canonical mitigation replay and handoff contract tests for trust-story assembly.

## Requirements Validated

- none (R009 remains partial until S05 integrated closeout confirms milestone-wide evidence continuity).

## Known Limitations

- Real-data replay in this stripped/low-signal worktree currently blocks as `blocked_insufficient_signal`; non-vacuous ready-path behavior is verified by regression tests.
- S03 does not perform stronger/combined model materiality decisions (S04 scope).
- Integrated rerun + compute-escalation disposition remains S05 scope.

## Follow-ups for Next Slices

1. **S04:** preserve S03 continuity fields/status semantics when combining mitigation context with stronger-model adoption decisions.
2. **S05:** include S03 mitigation command in integrated closeout rerun and treat blocked vs ready via artifact statuses (not exit code).
3. **M004:** consume `outputs/modeling/track_e/mitigation_experiment/` as authoritative mitigation evidence source in narrative/report layers.

## Files Created/Modified

- `src/modeling/common/mitigation_contract.py`
- `src/modeling/common/__init__.py`
- `src/modeling/track_e/mitigation_experiment.py`
- `src/modeling/track_e/__init__.py`
- `src/modeling/README.md`
- `tests/test_m003_mitigation_contract.py`
- `tests/test_m003_track_e_mitigation_experiment.py`
- `tests/test_m003_mitigation_handoff_contract.py`
- `.gsd/milestones/M003-rdpeu4/slices/S03/S03-UAT.md`
- `.gsd/milestones/M003-rdpeu4/slices/S03/S03-SUMMARY.md`
- `outputs/modeling/track_e/mitigation_experiment/pre_post_delta.parquet`
- `outputs/modeling/track_e/mitigation_experiment/manifest.json`
- `outputs/modeling/track_e/mitigation_experiment/validation_report.json`
- `.gsd/REQUIREMENTS.md`
- `.gsd/DECISIONS.md` (D033, D034)
- `.gsd/KNOWLEDGE.md`
- `.gsd/PROJECT.md`
- `.gsd/milestones/M003-rdpeu4/M003-rdpeu4-ROADMAP.md` (S03 marked complete)

## Forward Intelligence

### What the next slice should know
S03 guarantees one canonical mitigation command/path with strict status semantics and continuity locking. Downstream automation should consume artifact JSON status fields as the source of truth.

### What is most fragile
- Any drift in status vocabulary, required delta columns, or continuity payload equality.
- Any workflow that treats CLI exit code alone as success/failure for mitigation outcomes.

### Authoritative triage surfaces
- `outputs/modeling/track_e/mitigation_experiment/manifest.json`
- `outputs/modeling/track_e/mitigation_experiment/validation_report.json`
- `tests/test_m003_track_e_mitigation_experiment.py`
- `tests/test_m003_mitigation_handoff_contract.py`
