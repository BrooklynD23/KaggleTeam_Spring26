# Track A — EDA Pipeline: Future Star Rating Prediction

**Track:** A — Predictive Regression
**Version:** 1.1
**Date:** 2026-03-11

---

## 1. Framing Question

> How well can review text, user history, and business attributes predict future star ratings under strict time-split evaluation?

---

## 2. EDA Objectives

This EDA pipeline establishes the data foundation for a **temporal regression task**. Before any model is trained, we need to understand the structure, quality, and temporal dynamics of the prediction target (star ratings) and the candidate feature space (text, user history, business attributes).

Specific objectives:

- Profile the distribution of star ratings over time and across entities.
- Assess feature availability and completeness as-of any given review timestamp.
- Identify and quantify target leakage risks in the relational structure.
- Select and validate temporal split cutoffs (T₁, T₂) based on volume and drift analysis.
- Produce a feature availability matrix documenting what is and isn't usable under strict as-of constraints.
- Characterize sparsity in user and business histories, especially near the cold-start boundary.

---

## 3. Key Hypotheses to Test During EDA

| # | Hypothesis | How to Check |
|---|---|---|
| H1 | Star distributions shift over calendar years (rating inflation or deflation). | Year-over-year star histograms. |
| H2 | Longer reviews correlate with more extreme ratings (1-star or 5-star). | Text length vs. star scatter/box plots. |
| H3 | Users with longer histories have more stable rating patterns. | User tenure vs. rating variance. |
| H4 | Business attribute completeness varies significantly by category and city. | Attribute null-rate heatmaps by category × city. |
| H5 | A substantial fraction of user-business pairs have very sparse histories, making as-of features thin. | History-depth distribution at review time. |
| H6 | The chosen temporal split does not create a severe distribution shift in star balance. | Split-period star distributions compared with KS test. |

---

## 4. Minimum Input Tables

| Table | Source File | Key Columns |
|---|---|---|
| `review` | `yelp_academic_dataset_review.json` | `review_id`, `user_id`, `business_id`, `stars`, `date`, `text`, `useful` |
| `business` | `yelp_academic_dataset_business.json` | `business_id`, `city`, `state`, `categories`, `attributes` |
| `user` | `yelp_academic_dataset_user.json` | `user_id`, `yelping_since` |
| `tip` | `yelp_academic_dataset_tip.json` | `user_id`, `business_id`, `date` |
| `checkin` | `yelp_academic_dataset_checkin.json` | `business_id`, `date` |

---

## 5. Curated Tables to Build

| Table Name | Description | Key Columns |
|---|---|---|
| `review_fact` | Track A-safe review table materialized by the shared pipeline. It excludes raw review text, lifetime aggregates, and snapshot-only fields. | `review_id`, `user_id`, `business_id`, `review_stars`, `review_date`, `useful`, `text_char_count`, `text_word_count`, `city`, `state`, `categories`, `latitude`, `longitude`, `yelping_since`, `review_year`, `review_month`, `user_tenure_days` |
| `temporal_split_def` | Split cutoff dates with row counts per partition. | `split_name`, `start_date`, `end_date`, `review_count` |
| `user_history_asof` | Per-user rolling statistics at each review timestamp. | `user_id`, `as_of_date`, `prior_review_count`, `prior_avg_stars`, `prior_std_stars` |
| `business_history_asof` | Per-business rolling statistics at each review timestamp. | `business_id`, `as_of_date`, `prior_review_count`, `prior_avg_stars`, `prior_std_stars` |
| `feature_availability_matrix` | For each feature, the fraction of reviews where it is non-null under as-of rules. | `feature_name`, `overall_coverage`, `train_coverage`, `val_coverage`, `test_coverage` |

---

## 6. Proposed CLI Pipeline Stages

### Directory Structure

```
src/eda/track_a/
├── __init__.py
├── temporal_profile.py        # Stage 1: Star distribution over time
├── text_profile.py            # Stage 2: Text length and sentiment proxies
├── user_history_profile.py    # Stage 3: User history availability
├── business_attr_profile.py   # Stage 4: Business attribute completeness
├── split_selection.py         # Stage 5: Temporal split analysis
├── leakage_audit.py           # Stage 6: Leakage risk identification
├── feature_availability.py    # Stage 7: Feature availability matrix
└── summary_report.py          # Stage 8: Consolidated EDA report
```

### Stage-by-Stage Pipeline

**Stage 0 — Prerequisites (shared pipeline)**

```bash
python -m src.ingest.load_yelp_json --config configs/base.yaml
python -m src.validate.schema_checks --config configs/base.yaml
python -m src.curate.build_review_fact --config configs/base.yaml
```

These shared stages produce the `review_fact` table and validated Parquet files that all tracks depend on.
For Track A, `review_fact.parquet` is the enforceable allowlisted base. Track A must never read `review_fact_track_b.parquet` or the DuckDB view `review_fact_track_b`.

**Stage 1 — Temporal Profile**

```bash
python -m src.eda.track_a.temporal_profile --config configs/track_a.yaml
```

- Input: `data/curated/review_fact.parquet`
- Outputs:
  - `outputs/tables/track_a_s1_stars_by_year_month.parquet`
  - `outputs/tables/track_a_s1_review_volume_by_period.parquet`
  - `outputs/figures/track_a_s1_star_distribution_over_time.png`
  - `outputs/figures/track_a_s1_review_volume_timeline.png`
- Logic: Group reviews by year-month, compute star histograms and volume counts per period. Plot time series of mean star rating and review count.

**Stage 2 — Text Profile**

```bash
python -m src.eda.track_a.text_profile --config configs/track_a.yaml
```

- Input: `data/curated/review_fact.parquet`
- Outputs:
  - `outputs/tables/track_a_s2_text_length_stats.parquet`
  - `outputs/figures/track_a_s2_text_length_by_star.png`
  - `outputs/figures/track_a_s2_text_length_distribution.png`
- Logic: Use the Track A-safe derived text-length columns from `review_fact.parquet`. If sentiment proxy work samples raw text from `review.parquet`, it must first semijoin against `review_fact.parquet` review_ids (i.e., `WHERE review_id IN (SELECT review_id FROM review_fact.parquet)`) to restrict sampling to curated reviews only. It must not join or extract banned snapshot-only fields from any source.

**Stage 3 — User History Profile**

```bash
python -m src.eda.track_a.user_history_profile --config configs/track_a.yaml
```

- Input: `data/curated/review_fact.parquet`, `data/curated/user.parquet`
- Outputs:
  - `outputs/tables/track_a_s3_user_history_depth.parquet`
  - `outputs/figures/track_a_s3_user_prior_review_count_dist.png`
  - `outputs/figures/track_a_s3_user_tenure_vs_rating_var.png`
- Logic: For each review, compute the user's prior review count and average star rating using strictly earlier dates only. Aggregate to user-day, lag by one full day, and attach the same prior-history values to all reviews on that date. Do not fabricate same-day order with `review_id`. Identify first reviews with `user_prior_review_count = 0` and label that bucket `0 (first review)`.

**Stage 4 — Business Attribute Profile**

```bash
python -m src.eda.track_a.business_attr_profile --config configs/track_a.yaml
```

- Input: `data/curated/business.parquet`
- Outputs:
  - `outputs/tables/track_a_s4_attr_completeness_by_category.parquet`
  - `outputs/tables/track_a_s4_attr_completeness_by_city.parquet`
  - `outputs/figures/track_a_s4_attr_null_rate_heatmap.png`
- Logic: Flatten business `attributes` JSON. Compute null rate per attribute. Group by top-N categories and cities. Produce heatmap of completeness.

**Stage 5 — Split Selection**

```bash
python -m src.eda.track_a.split_selection --config configs/track_a.yaml
```

- Input: `data/curated/review_fact.parquet`, Stage 1 outputs
- Outputs:
  - `outputs/tables/track_a_s5_candidate_splits.parquet`
  - `outputs/tables/track_a_s5_split_star_balance.parquet`
  - `outputs/figures/track_a_s5_split_comparison.png`
- Logic: Propose 3–5 candidate T₁/T₂ cutoffs based on volume percentiles. For each, compute star distribution in train/val/test. Run KS test to quantify distribution shift. Recommend optimal split.
- **Schema contract**: The output parquet uses canonical column names `t1` and `t2` (ISO date strings). Downstream stages (6, 7, 8) read splits via `load_candidate_splits()` in `src/common/artifacts.py`, which also normalises any legacy `t1_date`/`t2_date` columns from older runs for backward compatibility.

**Stage 6 — Leakage Audit**

```bash
python -m src.eda.track_a.leakage_audit --config configs/track_a.yaml
```

- Input: `data/curated/review_fact.parquet`, selected split
- Outputs:
  - `outputs/tables/track_a_s6_leakage_report.parquet`
  - `outputs/logs/track_a_s6_leakage_audit.log`
- Logic: Check for the following leakage vectors:
  - Business aggregate `stars` (computed from all reviews including future) used as feature → **flag**.
  - Business `review_count` and `is_open` used as features without an explicitly as-of version → **flag**.
  - User `average_stars` (pre-computed aggregate) used as feature → **flag**.
  - User `review_count`, `fans`, or `elite` used as features without an explicitly as-of version → **flag**.
  - Any feature derived from data after the review timestamp → **flag**.
  - Any code path or query that reads `review_fact_track_b.parquet`, the DuckDB view `review_fact_track_b`, or raw entity joins that reintroduce banned fields → **flag**.
  - Reviews from the same user on the same business appearing in both train and test → **quantify**.
- **Scan scope**: The code-path scan covers all Track A-reachable modules (`src/eda/track_a/`, `src/common/`, `src/ingest/`, `src/curate/`, `src/validate/`). Track B directories are excluded.
- **Same-day history detection**: The audit flags `review_id` used as a same-day tiebreaker only when it appears inside a window `OVER(... ORDER BY review_date, review_id ...)` clause. Stable presentation sorts using `ORDER BY review_id` alone do not trigger the check.

**Stage 7 — Feature Availability Matrix**

```bash
python -m src.eda.track_a.feature_availability --config configs/track_a.yaml
```

- Input: All curated tables, selected split
- Outputs:
  - `outputs/tables/track_a_s7_feature_availability.parquet`
  - `outputs/figures/track_a_s7_feature_coverage_bars.png`
- Logic: For each candidate feature (text length, user history depth, business attributes, etc.), compute the fraction of reviews in each split where the feature is non-null and valid under as-of rules.

**Stage 8 — Summary Report**

```bash
python -m src.eda.track_a.summary_report --config configs/track_a.yaml
```

- Input: All prior stage outputs
- Outputs:
  - `outputs/tables/track_a_s8_eda_summary.md`
- Logic: Compile key findings into a markdown summary with embedded figure references.

---

## 7. Quality Checks

| Check | Stage | Pass Criterion |
|---|---|---|
| Row count after join stays within approved gate | 0 | `dropped_rows / raw_review_count <= 0.001`; any non-zero row loss must log orphan `review_id` values and missing foreign-key reasons |
| No future data in as-of features | 6 | Zero flagged rows in leakage report |
| Star distribution stable across splits | 5 | KS statistic < 0.05 between train and test |
| Text field non-null rate | 2 | > 99% of reviews have non-empty text |
| Date parsing success rate | 0 | 100% of review dates parse correctly |

---

## 8. Leakage and Validity Checks

This track is the most leakage-sensitive because the prediction target (stars) is also embedded in pre-aggregated fields on the business and user entities.

**Specific leakage vectors to audit:**

1. **Business-level `stars` field**: This is a lifetime average computed over all reviews, including those in the future. It must not be used as a feature. Instead, compute `business_avg_stars_asof` from training-period reviews only.

2. **User-level `average_stars` field**: Same issue — lifetime aggregate. Replace with `user_avg_stars_asof`.

3. **Business `review_count`**: Lifetime count. Replace with `business_review_count_asof`.

4. **User `review_count`**: Lifetime count. Replace with `user_review_count_asof`.

5. **Business `is_open`, user `fans`, and user `elite`**: Snapshot-only fields. These belong to Track B only and must not be used in Track A unless an explicitly as-of version is computed.

6. **Direct joins to raw entity data**: Any Track A stage that reads raw entity Parquet files must not join or extract banned fields from raw files, `review_fact_track_b`, or DuckDB views.

7. **Temporal overlap**: If a user reviews the same business multiple times, ensure the train/test split does not allow the model to "see" the user's later review of the same business during training while predicting it during testing.

---

## 9. Recommended Visual Outputs

| # | Visualization | Purpose |
|---|---|---|
| V1 | Star distribution histogram by year | Detect rating drift |
| V2 | Review volume time series (monthly) | Inform split selection |
| V3 | Text length boxplot by star rating | Feature engineering signal |
| V4 | User history depth CDF | Cold-start boundary |
| V5 | Business attribute null-rate heatmap | Feature feasibility |
| V6 | Split candidate comparison chart | Split decision |
| V7 | Feature availability bar chart | Modeling readiness |

All visualizations use aggregate data only. No raw review text is displayed.

---

## 10. Exit Criteria (Definition of Done for EDA)

Track A EDA is complete when:

- [ ] Star distributions are profiled over time, revealing any drift patterns.
- [ ] Text length and sentiment proxy statistics are computed and summarized.
- [ ] User and business history availability is quantified under as-of rules.
- [ ] Business attribute completeness is mapped by category and city.
- [ ] Temporal split cutoffs (T₁, T₂) are selected and justified.
- [ ] Leakage audit passes with zero flagged rows for the recommended feature set.
- [ ] Feature availability matrix is complete for all candidate features.
- [ ] Summary report is generated with all key findings.
- [ ] All output files exist in `outputs/tables/` and `outputs/figures/` with correct naming.

---

## 11. Handoff to Modeling

Upon EDA completion, the following artifacts are handed off to the modeling phase:

| Artifact | Location | Consumer |
|---|---|---|
| `review_fact` with clean temporal keys | `data/curated/` | Feature engineering pipeline |
| Selected T₁/T₂ cutoffs | `configs/track_a.yaml` | Train/val/test split logic |
| Feature availability matrix | `outputs/tables/` | Feature selection |
| Leakage audit report | `outputs/tables/` | Feature vetting |
| User/business history as-of tables | `data/curated/` | Feature computation |

**Modeling phase will then:**

1. Construct the final feature matrix using only EDA-approved features.
2. Train baseline models (mean predictor, user-mean, business-mean).
3. Train regression models (linear, gradient boosted, neural) with text embeddings.
4. Evaluate on the held-out test set using MAE and RMSE.
5. Report calibration plots (predicted vs. actual star distributions).

---

*End of Track A EDA Pipeline Specification.*
