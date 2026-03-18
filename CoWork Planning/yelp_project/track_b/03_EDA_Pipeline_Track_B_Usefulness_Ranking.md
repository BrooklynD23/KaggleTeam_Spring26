# Track B — EDA Pipeline: Snapshot Usefulness Ranking

**Track:** B — Learning-to-Rank
**Version:** 2.1
**Date:** 2026-03-11

---

## 1. Framing Question

> At a fixed Yelp dataset snapshot, which reviews are comparatively more useful within the same business/category after controlling for review age?

---

## 2. Task Reframe

The Yelp academic dataset is a **single cumulative snapshot**, not a historical log of vote growth. That means this track is **not** a valid "predict future usefulness over time" task unless external historical snapshots are available.

This track is therefore reframed as a **snapshot-time ranking task**:

- Rank reviews using the snapshot's observed `useful` counts.
- Control aggressively for review age so older reviews are not rewarded simply for existing longer.
- Compare reviews only inside documented ranking groups, primarily `business_id x age_bucket`.
- Treat any row-level outputs as internal academic artifacts only.

---

## 3. EDA Objectives

This EDA pipeline establishes a defensible setup for **age-controlled snapshot ranking**.

Specific objectives:

- Profile the distribution of `useful` votes across reviews, businesses, and categories.
- Quantify how strongly review age explains observed `useful` counts.
- Define stable age buckets and maturity thresholds for comparable ranking labels.
- Define ranking groups with enough within-group diversity for pointwise, pairwise, or listwise training.
- Construct candidate labels that are valid under a single-snapshot dataset.
- Identify permissible features at snapshot time and flag obvious leakage sources.
- Determine whether the task is better posed at business level, category level, or both.

---

## 4. Key Hypotheses to Test During EDA

| # | Hypothesis | How to Check |
|---|---|---|
| H1 | The `useful` vote distribution is strongly zero-inflated and long-tailed. | Histogram with zero-bin highlighted; log-scale tail profile. |
| H2 | Review age is one of the strongest correlates of `useful`, so age control is mandatory. | `useful` by age bucket; partial correlations controlling for age. |
| H3 | Longer reviews receive more `useful` votes within the same age bucket. | Text length vs. `useful` inside age-stratified groups. |
| H4 | Usefulness patterns differ across business categories even after age control. | Age-controlled `useful` distributions by category. |
| H5 | Business-level ranking groups are sparse, so category fallback groups may be needed. | Group-size distribution for `business_id x age_bucket` and `category x age_bucket`. |
| H6 | A within-group percentile or top-decile label is more stable than raw-count labels. | Compare class balance and tie rates across candidate label schemes. |

---

## 5. Minimum Input Tables

| Table | Source File | Key Columns |
|---|---|---|
| `review` | `yelp_academic_dataset_review.json` | `review_id`, `user_id`, `business_id`, `stars`, `date`, `text`, `useful`, `funny`, `cool` |
| `business` | `yelp_academic_dataset_business.json` | `business_id`, `city`, `categories` |
| `user` | `yelp_academic_dataset_user.json` | `user_id`, `elite`, `fans` |
| `snapshot_metadata` | `data/curated/snapshot_metadata.json` | `snapshot_reference_date`, `dataset_release_tag`, optional `computed_from` |

---

## 6. Curated Tables to Build

| Table Name | Description | Key Columns |
|---|---|---|
| `review_usefulness_snapshot` | Review table derived from `review_fact_track_b.parquet`, enriched with age, text length, user metadata, and business grouping keys. | `review_id`, `user_id`, `business_id`, `review_date`, `useful`, `review_age_days`, `age_bucket`, `text_word_count`, `elite`, `fans`, `primary_category`, `city` |
| `ranking_group_summary` | Group sizes and usefulness statistics for business/category age-controlled groups. | `group_type`, `group_id`, `age_bucket`, `review_count`, `pct_zero_useful`, `mean_useful`, `max_useful`, `tie_rate` |
| `label_candidates` | Candidate snapshot labels for ranking. | `review_id`, `group_type`, `group_id`, `age_bucket`, `binary_useful`, `graded_useful`, `within_group_percentile`, `top_decile_label` |
| `age_effect_summary` | Quantification of age confounding in `useful`. | `age_bucket`, `review_count`, `mean_useful`, `median_useful`, `pct_zero_useful` |

---

## 7. Proposed CLI Pipeline Stages

### Directory Structure

```
src/eda/track_b/
├── __init__.py
├── usefulness_distribution.py    # Stage 1: Vote distribution profiling
├── age_confounding.py            # Stage 2: Review-age confounding analysis
├── ranking_group_analysis.py     # Stage 3: Group definition and sizing
├── label_construction.py         # Stage 4: Snapshot-safe labels
├── feature_correlates.py         # Stage 5: Within-age-bucket feature analysis
├── training_feasibility.py       # Stage 6: Pairwise/listwise feasibility
├── leakage_scope_check.py        # Stage 7: Scope and leakage checks
└── summary_report.py             # Stage 8: Consolidated EDA report
```

### Stage-by-Stage Pipeline

**Stage 0 — Prerequisites (shared pipeline)**

```bash
python -m src.ingest.load_yelp_json --config configs/base.yaml
python -m src.validate.schema_checks --config configs/base.yaml
python -m src.curate.build_review_fact --config configs/base.yaml
```

Stage 0 must materialize all three shared artifacts before Track B runs:
- `data/curated/review_fact_track_b.parquet`
- `data/curated/review_fact.parquet`
- `data/curated/snapshot_metadata.json`

Track B reads `review_fact_track_b.parquet` and `snapshot_metadata.json`. It must not re-infer the snapshot date inside each stage.

**Stage 1 — Usefulness Vote Distribution**

```bash
python -m src.eda.track_b.usefulness_distribution --config configs/track_b.yaml
```

- Input: `data/curated/review_fact_track_b.parquet`, `data/curated/snapshot_metadata.json`
- Outputs:
  - `outputs/tables/track_b_s1_useful_vote_distribution.parquet`
  - `outputs/tables/track_b_s1_bucket_summary.parquet`
  - `outputs/tables/track_b_s1_age_distribution.parquet`
  - `outputs/figures/track_b_s1_useful_histogram.png`
  - `outputs/figures/track_b_s1_zero_fraction_by_category.png`
- Logic: Compute the overall `useful` vote distribution, bucket summary, the review-age distribution relative to `snapshot_reference_date` read from `snapshot_metadata.json`, and category-level zero fractions.

**Stage 2 — Age Confounding**

```bash
python -m src.eda.track_b.age_confounding --config configs/track_b.yaml
```

- Input: `data/curated/review_fact_track_b.parquet`, `data/curated/snapshot_metadata.json`
- Outputs:
  - `outputs/tables/track_b_s2_age_effect_summary.parquet`
  - `outputs/figures/track_b_s2_useful_by_age_bucket.png`
  - `outputs/figures/track_b_s2_textlen_vs_useful_within_age.png`
- Logic: Compute `review_age_days` and assign age buckets (for example 0-90, 91-180, 181-365, 366-730, 731+ days). Quantify how much `useful` changes with age and write `recommended_for_modeling = True` for all configured buckets as a schema pass-through. Stage 3 is the authoritative filter that updates the recommended list.

**Stage 3 — Ranking Group Analysis**

```bash
python -m src.eda.track_b.ranking_group_analysis --config configs/track_b.yaml
```

- Input: `data/curated/review_fact_track_b.parquet`, Stage 2 outputs
- Outputs:
  - `outputs/tables/track_b_s3_group_sizes_by_business_age.parquet`
  - `outputs/tables/track_b_s3_group_sizes_by_category_age.parquet`
  - `outputs/figures/track_b_s3_group_size_distribution.png`
- Logic: Build groups using `business_id x age_bucket` first, then `primary_category x age_bucket` as fallback. Report size, tie rate, and coverage.
- **Authoritative bucket filter**: After computing group summaries, Stage 3 writes `outputs/tables/track_b_s3_recommended_age_buckets.parquet` with `recommended_for_modeling` flags. An age bucket is recommended when its combined qualifying-group count (business + category) meets the `min_qualifying_groups` gate from config. Stages 4 and 5 read this artifact and raise a `RuntimeError` if no buckets qualify.
- Also outputs: `outputs/tables/track_b_s3_recommended_age_buckets.parquet`

**Stage 4 — Label Construction**

```bash
python -m src.eda.track_b.label_construction --config configs/track_b.yaml
```

- Input: Stage 3 outputs
- Outputs:
  - `outputs/tables/track_b_s4_label_candidates.parquet`
  - `outputs/tables/track_b_s4_label_scheme_summary.parquet`
- Logic: Construct only snapshot-safe labels:
  - **Binary**: `useful > 0`
  - **Graded**: 0 / 1 / 2-4 / 5-9 / 10+
  - **Within-group percentile**: percentile inside `group_id x age_bucket`
  - **Top-decile label**: 1 if review is in the top decile of `useful` within `group_id x age_bucket`

  Recommend one primary label using **measured criteria** — not config alone. Priority order:
  1. `passes_balance_gate` (max class fraction < 0.95) — desc
  2. `non_degenerate_fraction` (fraction of groups with > 1 distinct label value) — desc
  3. `mean_tie_rate` (lower is better) — asc
  4. `max_class_fraction` (lower is better) — asc
  5. Config rank (`primary` → `secondary` → other) — tie-break only

  Labels must compare reviews only within the same ranking group and age bucket. If Stage 3 has filtered all age buckets below the qualifying-groups gate, Stage 4 raises a `RuntimeError` before running.

**Stage 5 — Feature Correlates Within Age Buckets**

```bash
python -m src.eda.track_b.feature_correlates --config configs/track_b.yaml
```

- Input: `data/curated/review_fact_track_b.parquet`, Stage 2 outputs
- Outputs:
  - `outputs/tables/track_b_s5_feature_correlates.parquet`
  - `outputs/figures/track_b_s5_stars_vs_useful_within_age.png`
  - `outputs/figures/track_b_s5_elite_vs_useful_within_age.png`
- Logic: Compute age-controlled associations between `useful` and candidate features such as text length, star rating, elite status, fan count, and category.

**Stage 6 — Training Feasibility**

```bash
python -m src.eda.track_b.training_feasibility --config configs/track_b.yaml
```

- Input: Stage 3 and Stage 4 outputs
- Outputs:
  - `outputs/tables/track_b_s6_pairwise_stats.parquet`
  - `outputs/tables/track_b_s6_listwise_stats.parquet`
- Logic: For qualifying groups, compute raw pair counts `C(n, 2)`, tied pairs based on identical raw `useful` values within a ranking group, and net valid pairwise comparisons `C(n, 2) - tied_pairs`. Report both raw and net valid pair counts, average list length, and the fraction of groups with non-degenerate labels.
- **Feasibility sign-off**: `feasibility_signoff = meets_min_group_gate AND (valid_pairs > 0)`. Both conditions must be true — passing the qualifying-group count gate alone is not sufficient.

**Stage 7 — Leakage and Scope Check**

```bash
python -m src.eda.track_b.leakage_scope_check --config configs/track_b.yaml
```

- Input: `data/curated/review_fact_track_b.parquet`, `data/curated/snapshot_metadata.json`, Stage 4 outputs
- Outputs:
  - `outputs/tables/track_b_s7_leakage_scope_report.parquet`
  - `outputs/logs/track_b_s7_leakage_scope_check.log`
- Logic: Stage 7 is a real validation stage with zero-tolerance failures for:
  - `funny` or `cool` appearing in **any** `outputs/tables/track_b_*.parquet` artifact (not only s4/s5).
  - Raw review text columns (`text`, `review_text`, `raw_text`, `review_body`) in any Track B parquet artifact — checked case-insensitively.
  - Any label scheme that compares reviews across materially different ages without explicit age control.
  - Unsupported temporal claims in any `outputs/tables/track_b_*` or `outputs/logs/track_b_*` artifact.
  - Any row-level raw review text emitted in Track B artifacts.
- **Scan scope**: All `outputs/tables/track_b_*.parquet` files are scanned. Required artifacts (s4, s5) produce FAIL if missing; all other discovered parquets are checked if present.

Minimum prohibited temporal-claim patterns (case-insensitive regex):

```text
predict\s+future
vote\s+growth
future\s+useful(ness)?
temporal\s+target
vote.*(trajectory|trend|accumulate)
usefulness.at.time
reconstruct.*(vote|useful)
```

Implementation uses `re.search(..., re.IGNORECASE)` over each target file, records named findings in the Stage 7 log, and fails Stage 7 on any match.

**Stage 8 — Summary Report**

```bash
python -m src.eda.track_b.summary_report --config configs/track_b.yaml
```

- Input: All prior stage outputs
- Outputs:
  - `outputs/tables/track_b_s8_eda_summary.md`
- Logic: Summarize the age-control decision, viable group definitions, candidate labels, and modeling recommendation.

---

## 8. Quality Checks

| Check | Stage | Pass Criterion |
|---|---|---|
| `useful` field non-null | 1 | > 99.9% non-null |
| Vote counts are non-negative integers | 1 | Zero negative values |
| Age buckets are documented and mutually exclusive | 2 | 100% of reviews assigned exactly one age bucket |
| Ranking groups meet minimum size | 3 | ≥ 1,000 qualifying groups with ≥ 5 reviews |
| Label scheme has non-degenerate class balance | 4 | Selected scheme has no single class > 90% |
| Pairwise feasibility is net-of-ties | 6 | Stage 6 reports raw pairs, tied pairs, and net valid pairs with `valid_pairs = C(n, 2) - tied_pairs` |
| Snapshot-only scope is enforced | 7 | Zero `funny`/`cool` columns in generated label tables, zero cross-age comparisons, zero unsupported temporal claims, and zero row-level raw review text in Track B artifacts |

---

## 9. Leakage and Validity Checks

**Track B specific risks:**

1. **Single-snapshot limitation**: The dataset does not support reconstructing vote trajectories over time. Do not infer `useful_at_t` or vote plateau timing.

2. **Exposure-time bias**: Older reviews have had more opportunity to accumulate votes. All labels and evaluations must control for review age.

3. **Simultaneous vote signals**: `funny` and `cool` are concurrent engagement signals and must not be used as model features. Their appearance in generated label tables is a Stage 7 failure.

4. **Group mismatch**: Comparing reviews across businesses or categories without enough local context can wash out the ranking signal. Business-first grouping with category fallback is preferred.

5. **Pairwise overcounting**: Raw combinations overstate feasible pairwise data when ties are common. Always subtract tied pairs computed on raw `useful` values within each ranking group.

---

## 10. Recommended Visual Outputs

| # | Visualization | Purpose |
|---|---|---|
| V1 | `useful` vote histogram | Understand zero inflation and long tail |
| V2 | `useful` by age bucket | Quantify age confounding |
| V3 | Zero-fraction by category | Category-specific signal |
| V4 | Group size distribution | Training feasibility |
| V5 | Text length vs. `useful` within age bucket | Feature signal check |
| V6 | Star rating vs. `useful` within age bucket | Feature signal check |
| V7 | Label scheme comparison chart | Label decision |

All visualizations use aggregate data only. No raw review text is displayed.

---

## 11. Exit Criteria (Definition of Done for EDA)

Track B EDA is complete when:

- [ ] `useful` vote and review-age distributions are profiled.
- [ ] Age confounding is quantified and a primary age-bucketing strategy is selected.
- [ ] Ranking groups are defined with documented fallback logic.
- [ ] At least one snapshot-safe label scheme is constructed and justified.
- [ ] Pairwise/listwise feasibility is assessed on qualifying groups.
- [ ] Leakage and scope checks confirm no unsupported temporal claims.
- [ ] Summary report is generated.
- [ ] All output files exist in `outputs/tables/` and `outputs/figures/`.

---

## 12. Handoff to Modeling

Upon EDA completion, the following artifacts are handed off:

| Artifact | Location | Consumer |
|---|---|---|
| `review_usefulness_snapshot` table | `data/curated/` | Feature engineering |
| Recommended age buckets | `configs/track_b.yaml` | Data preparation |
| Recommended label scheme | `outputs/tables/` | Label construction |
| Ranking group definitions | `outputs/tables/` | Data loader for LTR model |
| Leakage and scope report | `outputs/tables/` | Feature vetting |
| Pairwise/listwise feasibility stats | `outputs/tables/` | Model architecture decision |

**Modeling phase will then:**

1. Construct ranking features without `funny`/`cool` and without unsupported temporal labels.
2. Train pointwise, pairwise, and/or listwise ranking models.
3. Evaluate using NDCG@K and Recall@K within documented age-controlled groups.
4. Compare against baselines: age-only, text-length-only, and star-rating-only.
5. State explicitly that this is a snapshot usefulness ranking task, not future usefulness forecasting.

---

*End of Track B EDA Pipeline Specification.*
