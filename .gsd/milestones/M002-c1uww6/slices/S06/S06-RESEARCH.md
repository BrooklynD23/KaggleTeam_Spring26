# S06 — Research

**Date:** 2026-03-23

## Summary

S06 is a **targeted integration/handoff** slice, not a new modeling-architecture slice.

Primary requirement targeting for this slice:
- **Owns closure proof for R005, R006, R007, R008** (all four baseline tracks integrated under one contract).
- **Supports R009 and R012** by leaving a clean, explicit upstream model handoff surface (Track A preferred default audit target, cross-track trust narrative coherence).

Current repo truth (verified in this worktree):
- All four baseline runtimes execute successfully:
  - `python -m src.modeling.track_a.baseline --config configs/track_a.yaml --train-cap 100000 --eval-cap 200000`
  - `python -m src.modeling.track_b.baseline --config configs/track_b.yaml`
  - `python -m src.modeling.track_c.baseline --config configs/track_c.yaml`
  - `python -m src.modeling.track_d.baseline --config configs/track_d.yaml`
- Integrated regression gate passes:
  - `python -m pytest tests/test_track_a_baseline_model.py tests/test_track_b_baseline_model.py tests/test_track_c_baseline_model.py tests/test_track_d_baseline_model.py tests/test_track_d_cohorts.py tests/test_label_scheme_ranking.py tests/test_feasibility_signoff.py tests/test_track_c_common.py tests/test_m002_modeling_contract.py -q`
  - Result: `49 passed`.
- `outputs/modeling/track_a|track_b|track_c|track_d/` all contain the expected artifact bundles and required summary phrases.

Key remaining integration gaps (important for planner):
1. **No milestone-level M002 handoff harness exists yet** (only per-track tests + scaffold contract test).
2. **Slice docs are incomplete for handoff quality**:
   - `.gsd/milestones/M002-c1uww6/slices/S02/S02-SUMMARY.md` missing
   - `.gsd/milestones/M002-c1uww6/slices/S03/S03-SUMMARY.md` missing
   - `.gsd/milestones/M002-c1uww6/slices/S04/S04-SUMMARY.md` missing
   - `.gsd/milestones/M002-c1uww6/slices/S05/S05-SUMMARY.md` missing
   - `S02`–`S05` UAT files are still doctor placeholders (contain “Recovery placeholder” text).
3. **Requirement/project state is stale for M002 progress**:
   - `R005`–`R008` still marked `active` in `.gsd/REQUIREMENTS.md`.
   - `.gsd/PROJECT.md` still says “no baseline modeling layer yet,” which is now false.

Skill-informed stance:
- From `debug-like-expert`: **verify, don’t assume** — S06 should prove integrated truth from regenerated artifacts/tests, not from prior slice prose.
- From `coding-standards`: **KISS/DRY/YAGNI** — prefer a thin integration harness + documentation/state repair over new orchestration subsystems.
- From `verification-loop`: finish with explicit quality gates (tests + runtime + artifact assertions), not narrative-only closure.

## Recommendation

Implement S06 as a **thin integrated closeout layer**:

1. Add a dedicated milestone-level pytest harness (recommended: `tests/test_m002_handoff_verification.py`) that composes cross-track agreement checks without re-testing every helper in depth.
2. Repair handoff docs so a fresh agent does not land on placeholder artifacts:
   - Replace placeholder UAT files for S02–S05.
   - Backfill missing S02–S05 slice summaries from task summaries + real command evidence.
3. Run one explicit integrated verification sequence and record it in S06 UAT.
4. Update state surfaces (`REQUIREMENTS`, `PROJECT`, roadmap checkbox/S06 docs) only after integrated verification is green.

This gives S06 the same successful pattern used in M001 integrated closure: compose existing verified surfaces, add one thin cross-surface harness, and remove stale/placeholder handoff drift.

## Implementation Landscape

### Key Files and Their Roles

- `src/modeling/README.md`
  - Canonical M002 modeling contract (`outputs/modeling/<track>/`, required bundle, summary contract, D1-required/D2-optional notes).
- `src/modeling/track_a/baseline.py`
  - Emits explicit `Known limitations` + `M003 audit suitability` sections and preferred Track A audit-target language.
- `src/modeling/track_b/baseline.py`
  - Enforces snapshot/age-group ranking framing with comparator semantics.
- `src/modeling/track_c/baseline.py`
  - Enforces monitoring-only framing and `not a forecast` summary language.
- `src/modeling/track_d/baseline.py`
  - Enforces D1-required comparator evaluation and explicit D2 optional/non-blocking report.
- `tests/test_m002_modeling_contract.py`
  - Current scaffold-level contract test (dirs/markers only); too shallow for final integrated handoff proof.
- `outputs/modeling/track_*/{metrics.csv,config_snapshot.json,summary.md,...}`
  - The real integrated evidence surfaces S06 must freeze and verify together.
- `.gsd/milestones/M002-c1uww6/slices/S02..S05/*`
  - Handoff docs currently incomplete (missing summaries + placeholder UATs).
- `.gsd/REQUIREMENTS.md`, `.gsd/PROJECT.md`
  - State surfaces that should reflect post-S06 integrated truth.

### Natural Seams for Planner Decomposition

1. **Test harness seam (required)**
   - Add milestone-level integration assertions across all four tracks and handoff docs.
2. **Documentation seam (required)**
   - Replace placeholder UAT artifacts and add missing slice summaries for S02–S05.
3. **Verification seam (required)**
   - Execute one authoritative integrated rerun (tests + all baselines + assertions).
4. **State/update seam (required)**
   - Update requirements/project/milestone status only after proof is captured.

### Suggested Build Order

1. **Create the integrated handoff pytest harness first** (it should fail if contract drift exists).
2. **Repair S02–S05 summary/UAT artifacts** to satisfy handoff-quality assertions.
3. **Run integrated verification sequence** and capture exact evidence in `S06-UAT.md`.
4. **Apply requirement/project/roadmap state updates** using the captured evidence.

## Constraints

- Preserve all track guardrails:
  - Track A leakage-safe as-of framing.
  - Track B snapshot-only ranking framing.
  - Track C monitoring-only (non-forecast) framing.
  - Track D D1 required / D2 optional non-blocking semantics.
- No raw review text in any new handoff artifact.
- Keep all modeling outputs under `outputs/modeling/` contract; no ad hoc roots.
- In this harness, prefer foreground `bash` verification for slice-close checks (known `async_bash` mirror-path mismatch risk in auto-mode).

## Common Pitfalls

- **Treating per-track “green” as integrated closure.** S06 needs cross-track agreement checks in one pass.
- **Leaving doctor placeholder UAT files in shipped handoff docs.** This breaks fresh-agent usability.
- **Overstating model superiority in summaries.**
  - Track A beats `naive_mean` but trails `naive_business_prior_avg` on test MAE.
  - Track D beats popularity on overall `ALL` test metrics, but underperforms in `established` cohort.
- **Adding a heavyweight orchestration script prematurely.** Thin pytest + existing CLIs is sufficient for M002 closure.

## Verification Approach

Recommended S06 integrated gate (authoritative order):

1. Regression + contract suite (including new S06 harness):
   - `python -m pytest tests/test_track_a_baseline_model.py tests/test_track_b_baseline_model.py tests/test_track_c_baseline_model.py tests/test_track_d_baseline_model.py tests/test_track_d_cohorts.py tests/test_label_scheme_ranking.py tests/test_feasibility_signoff.py tests/test_track_c_common.py tests/test_m002_modeling_contract.py tests/test_m002_handoff_verification.py -q`
2. Rerun all four baselines (real artifact regeneration):
   - `python -m src.modeling.track_a.baseline --config configs/track_a.yaml --train-cap 100000 --eval-cap 200000`
   - `python -m src.modeling.track_b.baseline --config configs/track_b.yaml`
   - `python -m src.modeling.track_c.baseline --config configs/track_c.yaml`
   - `python -m src.modeling.track_d.baseline --config configs/track_d.yaml`
3. Cross-track semantic assertion snippet:
   - Assert artifact existence/schema across all tracks.
   - Assert required summary phrases per track.
   - Assert key comparator truths (A beats naive_mean; B model > text_length > stars on test ALL NDCG@10; D1 model vs as-of popularity metrics present; D2 gate non-blocking).
4. Handoff doc hygiene assertion:
   - Assert no `Recovery placeholder` text remains in S02–S05 UAT files.
   - Assert S02–S05 slice summary files exist.

## Observed Cross-Track Metrics (Current Worktree)

- **Track A (test):** model MAE `1.1089`, naive_mean MAE `1.3200`, naive_business_prior_avg MAE `1.0827`.
- **Track B (test/ALL):** model NDCG@10 `0.9173` > text_length `0.8782` > review_stars `0.7958`; model Recall@10 `0.8482`.
- **Track C:** city_count `378`, significant_sentiment_city_count `21`, significant_topic_city_count `39`, mean_monitoring_change_score `0.1664`.
- **Track D (D1 test/ALL):** model Recall@20 `0.1997` vs popularity `0.1666`; model NDCG@10 `0.0534` vs popularity `0.0508`; label_coverage_rate `0.1527`; D2 gate `not_attempted`, non-blocking.

## Skills Discovered

Checked direct technology skill candidates (not installed):

- DuckDB: `npx skills add silvainfm/claude-skills@duckdb`
- Pandas: `npx skills add jeffallan/claude-skills@pandas-pro`
- scikit-learn: `npx skills add davila7/claude-code-templates@scikit-learn`
- Matplotlib: `npx skills add davila7/claude-code-templates@matplotlib`

No installation performed in this slice.
