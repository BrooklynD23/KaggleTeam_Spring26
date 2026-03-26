# S03 — Research

**Date:** 2026-03-23

## Summary

S03 is a **targeted research** slice, not a greenfield modeling design problem. The repo already has the full Track B EDA handoff needed for a first baseline: `data/curated/review_fact_track_b.parquet`, `data/curated/snapshot_metadata.json`, Stage 3 recommended age buckets, Stage 4 label candidates / label-scheme ranking, and Stage 6 pairwise/listwise feasibility tables. The modeling scaffold from S01 also exists under `src/modeling/` and `outputs/modeling/`.

The main execution gap is that **`src/modeling/track_b/` has no runtime code yet** — only `__init__.py` exists. However, `outputs/modeling/track_b/` already contains a metrics/config/summary/figure bundle from a prior run. That bundle is useful as a reference surface for the intended Track B baseline, but per `debug-like-expert`'s “verify, don’t assume” rule it should **not** be treated as sufficient proof because the implementation source is absent and the current bundle also omits the contract’s scored-output artifact.

## Recommendation

Implement `src/modeling/track_b/baseline.py` as a **pointwise baseline** that mirrors the Track A modeling style: load config via `src.common.config.load_config()`, read the existing Track B EDA artifacts, derive a deterministic **group-level split** that keeps entire ranking groups together, train a simple `HistGradientBoostingRegressor` on the Stage 4 primary label `within_group_percentile`, and emit the standard artifact bundle under `outputs/modeling/track_b/`.

Keep the slice narrow. Follow `coding-standards` KISS/YAGNI guidance: do not add pairwise/listwise learners in M002. Use existing EDA outputs to lock decisions already made by the repo: business-first / category fallback groups, age-controlled evaluation, Stage 4 label ranking, and Stage 6 feasibility evidence. Follow `tdd-workflow` / `test` guidance by adding focused pytest coverage around pure helper logic first, then the artifact-writing path, then the entrypoint. Follow `verification-loop` by finishing with an explicit run of the baseline entrypoint and pytest, not by trusting existing output files.

## Implementation Landscape

### Key Files

- `src/modeling/track_b/__init__.py` — package exists but currently has no baseline implementation.
- `src/modeling/track_a/baseline.py` — best in-repo template for M002 modeling code: config loading, required-input checks, artifact bundle writing, config snapshot, summary contract, CLI entrypoint, and capped runtime controls.
- `src/modeling/README.md` — canonical M002 modeling contract. Track B must emit metrics, scored output, config snapshot, and summary under `outputs/modeling/track_b/`.
- `configs/track_b.yaml` — Track B rules: snapshot date framing, age buckets, ranking-group thresholds, primary/secondary labels, banned features, and quality gates.
- `src/eda/track_b/common.py` — authoritative snapshot helpers. Use `load_snapshot_metadata()`, `create_snapshot_view()`, and the existing temporal-claim constraints instead of re-deriving snapshot logic.
- `src/eda/track_b/ranking_group_analysis.py` — defines Stage 3 qualifying groups and writes `track_b_s3_recommended_age_buckets.parquet`; all six age buckets currently pass the gate.
- `src/eda/track_b/label_construction.py` — defines Stage 4 label candidates and `build_label_scheme_summary()`. Current artifact state ranks `within_group_percentile` as recommended primary and `graded_useful` as recommended secondary.
- `src/eda/track_b/training_feasibility.py` — defines group-level pairwise/listwise feasibility stats. Useful for deciding whether to restrict evaluation to business groups or how to report fallback-group coverage.
- `src/eda/track_b/feature_correlates.py` — shows the snapshot-safe numeric/binary feature families already used in Track B EDA (`text_*`, `review_stars`, `fans`, `user_tenure_days`, `elite_flag`, `is_open`, location, review year/month).
- `tests/test_track_a_baseline_model.py` — concrete style reference for Track A modeling unit tests: pure helper tests first, not giant integration-only coverage.
- `tests/test_m002_modeling_contract.py` — verifies the shared scaffold, not Track B runtime behavior. Keep passing.
- `outputs/modeling/track_b/summary.md` — reference-only artifact showing the intended baseline family, feature set, split description, and target metrics. It claims a deterministic hash split on `group_type|group_id|age_bucket` and a pointwise HGB regressor.
- `outputs/modeling/track_b/config_snapshot.json` / `metrics.csv` — reference-only output shapes for the currently desired Track B artifact surface.

### Build Order

1. **Lock the Track B runtime contract first**
   - Create `src/modeling/track_b/baseline.py` with the same outer structure as Track A: config load, required-input checks, run function, artifact writers, CLI parser.
   - This unblocks every later decision because the planner/executors then have one canonical entrypoint.

2. **Implement deterministic group assembly + split logic**
   - Read Stage 4 `track_b_s4_label_candidates.parquet` as the authoritative row/group/label surface.
   - Join back to `review_fact_track_b.parquet`-derived snapshot-safe features.
   - Split by whole ranking group, not by row, to avoid cross-split leakage inside the same ranked list.
   - The existing output bundle says the intended split key is `group_type|group_id|age_bucket`; use that unless execution finds contradictory code-level evidence.

3. **Implement feature preparation + simple comparators**
   - Convert `elite` to `elite_flag` using the same logic already encoded in `create_snapshot_view()`.
   - Start with the feature family already reflected in the existing artifact bundle: `text_char_count`, `text_word_count`, `review_stars`, `fans`, `user_tenure_days`, `is_open`, `elite_flag`, `review_year`, `review_month`, `latitude`, `longitude`.
   - Preserve explicit exclusions for `review.funny`, `review.cool`, and any vote-growth reconstruction.
   - Add trivial comparators that are rankable within groups. The current bundle uses `text_length_only` and `review_stars_only`.

4. **Implement grouped ranking evaluation helpers**
   - Compute NDCG@10 and Recall@10 on Stage 4 `top_decile_label` within held-out groups.
   - Emit per-age-bucket rows plus `ALL` aggregate rows, matching the existing `metrics.csv` shape.
   - Decide and document how groups with no positive top-decile labels are handled before writing tests.

5. **Implement artifact bundle + summary**
   - Write at least:
     - `outputs/modeling/track_b/metrics.csv`
     - `outputs/modeling/track_b/config_snapshot.json`
     - `outputs/modeling/track_b/summary.md`
     - a scored-output artifact (currently missing from the existing bundle; add something like `group_rankings_test.parquet` or `scores_test.parquet`)
     - `outputs/modeling/track_b/figures/test_ndcg_by_age_bucket.png`
   - Make the summary satisfy the `src/modeling/README.md` summary contract, not just the current ad hoc headings.

6. **Add Track B-specific tests**
   - New `tests/test_track_b_baseline_model.py` should cover pure logic: split stability, comparator scoring, grouped metric helpers, and maybe summary/config snapshot markers.
   - Keep one small artifact-writing smoke test if feasible with synthetic data.

### Verification Approach

- Scaffold regression:
  - `python -m pytest tests/test_m002_modeling_contract.py`
- Keep upstream EDA assumptions green:
  - `python -m pytest tests/test_label_scheme_ranking.py tests/test_feasibility_signoff.py`
- New Track B modeling tests (to add):
  - `python -m pytest tests/test_track_b_baseline_model.py`
- Real entrypoint verification:
  - `python -m src.modeling.track_b.baseline --config configs/track_b.yaml`
- Post-run artifact checks:
  - confirm `outputs/modeling/track_b/` contains metrics + scored output + config snapshot + summary + figure
  - confirm summary explicitly names inputs, excluded features, grouping logic, comparators, and NDCG@10
  - confirm model beats trivial comparators on held-out `ALL` NDCG@10

## Constraints

- Track B is **snapshot-only**. Do not model vote growth, stabilization, or future usefulness.
- `review_fact_track_b.parquet` and `snapshot_metadata.json` are the canonical inputs; do not infer the snapshot date from the data.
- `review.funny` and `review.cool` are banned features.
- Age control is mandatory; all evaluation is within age-controlled ranking groups.
- Ranking groups are business-first with category fallback, always within age buckets.
- Stage 3 currently recommends **all six** configured age buckets for modeling.
- The curated Track B table is large (`~6.99M` rows). Runtime caps like Track A’s `train_cap` / `eval_cap` pattern are worth preserving if full-data training becomes expensive.

## Common Pitfalls

- **Trusting existing outputs as implementation proof** — `outputs/modeling/track_b/` already has artifacts, but `src/modeling/track_b/` has no baseline entrypoint. Recreate from source and verify.
- **Splitting rows instead of groups** — a row-level split would leak ranking context across train/validation/test because the same `group_type|group_id|age_bucket` list would appear in multiple splits.
- **Missing the required scored-output artifact** — the current Track B bundle has metrics/config/summary/figure but no saved per-group score/ranking artifact, even though the modeling contract requires one.
- **Over-weighting category fallback in acceptance logic** — Stage 6 shows business groups pass per-bucket feasibility gates; category groups do not always pass per-bucket minimum-group gates even though they help overall coverage. Report that nuance clearly.
- **Reinventing label selection** — Stage 4 already measured scheme quality and picked `within_group_percentile` as primary; don’t add new label debates inside S03.

## Open Risks

- The current artifact bundle documents a deterministic hash split strategy, but the code implementing it is absent. The executor will need to formalize that behavior in source and pin it with tests.
- Full validation/test evaluation spans ~2.1M held-out rows in the current bundle. If runtime is high locally, keep deterministic caps configurable rather than changing the evaluation definition silently.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| DuckDB | `silvainfm/claude-skills@duckdb` | available |
| scikit-learn | `davila7/claude-code-templates@scikit-learn` | available |
| Python / pytest | built-in repo patterns + installed `test` / `tdd-workflow` skills | available |
