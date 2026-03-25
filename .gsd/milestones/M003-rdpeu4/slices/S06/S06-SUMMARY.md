---
id: S06
parent: M003-rdpeu4
milestone: M003-rdpeu4
provides:
  - Fairness replay now encodes explicit `signal_sufficiency` truth (`primary_sufficient` / `fallback_sufficient` / `insufficient`) instead of allowing empty-but-pass readiness.
  - Deterministic fallback subgroup strategy (`split_name_metrics`) that can recover actionable aggregate fairness signal when primary subgroup construction is empty.
  - Handoff-locked continuity and triage contract for S03/S05/M004 consumers (`baseline_anchor`, `split_context`, sufficiency diagnostics, fail-closed blocked semantics).
requires:
  - slice: M003-rdpeu4/S01
    provides: Canonical upstream scored intake bundle (`scored_intake.parquet`, intake manifest/validation).
  - slice: M003-rdpeu4/S02
    provides: Model-aware fairness runtime boundary consumed and hardened by this remediation slice.
affects:
  - M003-rdpeu4/S07
  - M004-fjc2zy
key_files:
  - src/modeling/common/fairness_audit_contract.py
  - src/modeling/common/__init__.py
  - src/modeling/track_e/fairness_audit.py
  - configs/track_e.yaml
  - tests/test_m003_fairness_audit_contract.py
  - tests/test_m003_track_e_fairness_audit.py
  - tests/test_m003_fairness_audit_handoff_contract.py
  - src/modeling/README.md
  - .gsd/milestones/M003-rdpeu4/slices/S06/S06-UAT.md
  - outputs/modeling/track_e/fairness_audit/manifest.json
  - outputs/modeling/track_e/fairness_audit/validation_report.json
  - .gsd/REQUIREMENTS.md
  - .gsd/DECISIONS.md
  - .gsd/milestones/M003-rdpeu4/M003-rdpeu4-ROADMAP.md
key_decisions:
  - D041: Keep fairness status vocabulary unchanged and add additive `signal_sufficiency` diagnostics contract.
  - D042: Use deterministic aggregate-safe fallback strategy `split_name_metrics` when primary fairness signal is empty.
  - D043: Treat readiness as outcome-aware truth (`ready_for_mitigation` requires sufficient outcome + non-empty subgroup/disparity rows).
patterns_established:
  - Compatibility-preserving hardening pattern: keep existing top-level statuses stable while introducing stricter additive diagnostics.
  - Fail-closed fairness readiness pattern: insufficient signal is an explicit blocked artifact state, not silent success.
  - Canonical replay + smoke triage pattern: fairness sufficiency replay is always paired with mitigation reason-shift smoke checks.
observability_surfaces:
  - outputs/modeling/track_e/fairness_audit/manifest.json
  - outputs/modeling/track_e/fairness_audit/validation_report.json
  - outputs/modeling/track_e/fairness_audit/subgroup_metrics.parquet
  - outputs/modeling/track_e/fairness_audit/disparity_summary.parquet
  - outputs/modeling/track_e/mitigation_experiment/manifest.json
  - tests/test_m003_fairness_audit_contract.py
  - tests/test_m003_track_e_fairness_audit.py
  - tests/test_m003_fairness_audit_handoff_contract.py
duration: ~5h
verification_result: passed
completed_at: 2026-03-24
---

# S06: Fairness-signal sufficiency replay on real upstream predictions

**S06 is complete.** This remediation slice eliminated the "empty fairness signal but ready status" gap by making fairness readiness depend on explicit sufficiency truth, with deterministic fallback and blocked diagnostics.

## What This Slice Delivered

1. **Contract hardening (T01)**
   - Added `signal_sufficiency` schema/constants/validator support in `src/modeling/common/fairness_audit_contract.py`.
   - Locked allowed outcomes/reasons and deterministic machine-readable check surfaces for malformed payloads.

2. **Runtime sufficiency gate + fallback (T02)**
   - Updated `src/modeling/track_e/fairness_audit.py` to evaluate primary signal sufficiency, run configured fallback when needed, and set status fail-closed.
   - Added fallback configuration in `configs/track_e.yaml`:
     - `fairness.signal_sufficiency.fallback.enabled: true`
     - `strategy: split_name_metrics`
     - `min_group_size: 1`
   - Preserved status compatibility (`ready_for_mitigation`, `blocked_upstream`) while making sufficiency path explicit.

3. **Handoff/docs/traceability lock (T03)**
   - Extended handoff regression tests to enforce sufficiency semantics + continuity equality.
   - Updated modeling docs/UAT so downstream slices can replay and triage deterministically.
   - Updated requirement traceability (R009/R010/R012) with S06 evidence and current readiness truth.

## Verification Executed (Closer Run)

All S06 slice-plan verification commands were rerun and passed:

| # | Command | Result |
|---|---|---|
| 1 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_fairness_audit_contract.py tests/test_m003_track_e_fairness_audit.py tests/test_m003_fairness_audit_handoff_contract.py -q` | ✅ 18 passed |
| 2 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.fairness_audit --config configs/track_e.yaml --intake-dir outputs/modeling/track_a/audit_intake --output-dir outputs/modeling/track_e/fairness_audit` | ✅ bundle regenerated |
| 3 | Fairness sufficiency assertion snippet from S06 plan | ✅ `m003 s06 fairness sufficiency contract verified` |
| 4 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.mitigation_experiment --config configs/track_e.yaml --intake-dir outputs/modeling/track_a/audit_intake --fairness-dir outputs/modeling/track_e/fairness_audit --output-dir outputs/modeling/track_e/mitigation_experiment` | ✅ blocked bundle regenerated as designed |
| 5 | Mitigation readiness smoke snippet from S06 plan | ✅ `m003 s06 mitigation readiness smoke verified` |

## Observability / Diagnostic Outcome (Current Replay)

From `outputs/modeling/track_e/fairness_audit/manifest.json` and `validation_report.json`:

- `status = ready_for_mitigation`
- `validation.status = pass`
- `signal_sufficiency.outcome = fallback_sufficient`
- `signal_sufficiency.path = fallback`
- `signal_sufficiency.reasons = ["primary_empty_disparity_rows", "primary_empty_subgroup_rows"]`
- `row_counts.primary_subgroup_rows = 0`, `row_counts.primary_disparity_rows = 0`
- `row_counts.subgroup_rows = 3`, `row_counts.disparity_rows = 8`
- fallback strategy recorded as `split_name_metrics` with positive row deltas.

From `outputs/modeling/track_e/mitigation_experiment/manifest.json` (smoke follow-up):

- `status = blocked_insufficient_signal`
- `insufficient_signal.reasons = ["no_correction_groups"]`
- **`no_disparity_rows` is no longer present**, confirming S06 fixed the fairness-signal emptiness regression path.

## Requirement State Update (Post-S06)

- **R009**: remains **active / partially validated**, now with S06 sufficiency truthfulness and fallback evidence added; still not fully validated until S07 lands non-empty authoritative pre/post mitigation deltas on real replay.
- **R010**: remains **active / partially validated**; S06 now strengthens comparator prerequisite fairness-signal reliability.
- **R012**: remains **active** (M004 owner), with stronger continuity support through S06 replay + triage contract surfaces.

## Decisions / Knowledge Carry-Forward

- Added **D043** in `.gsd/DECISIONS.md` to lock outcome-aware readiness interpretation at handoff.
- Existing S06 gotcha in `.gsd/KNOWLEDGE.md` remains valid: fairness can be fallback-ready while mitigation still blocks for sparse correction support (`no_correction_groups`).

## What S07 Must Do Next

1. Turn mitigation from blocked to materially evaluable on canonical replay (non-empty `pre_post_delta.parquet`).
2. Preserve S06 sufficiency semantics while addressing tiny-support correction-group scarcity.
3. Rerun S05 integrated closeout and target `ready_for_handoff` with explicit mitigation/comparator/escalation evidence.

## Files Updated During S06 Closeout

- `.gsd/milestones/M003-rdpeu4/slices/S06/S06-SUMMARY.md`
- `.gsd/milestones/M003-rdpeu4/slices/S06/S06-UAT.md`
- `.gsd/milestones/M003-rdpeu4/M003-rdpeu4-ROADMAP.md` (S06 marked complete)
- `.gsd/REQUIREMENTS.md` (R009/R010/R012 updates)
- `.gsd/DECISIONS.md` (D043)
- `.gsd/PROJECT.md`
