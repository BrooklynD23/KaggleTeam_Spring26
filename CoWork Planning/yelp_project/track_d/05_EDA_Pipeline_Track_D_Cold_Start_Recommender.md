# Track D — EDA Pipeline: Cold-Start Recommender

**Track:** D — Recommendation Under Cold Start
**Version:** 2.0
**Date:** 2026-03-10

---

## 1. Framing Question

> Can separate business-cold-start and user-cold-start recommenders outperform explicit as-of popularity baselines without using post-hoc information?

---

## 2. Subtrack Split

Track D is intentionally split into two related but distinct subtracks:

- **D1 — Business Cold Start:** recommend newly introduced businesses to users when the business has little or no interaction history.
- **D2 — User Cold Start:** recommend businesses to users with zero or very limited prior interaction history.

These subtracks share ingestion and leakage controls but require different cohorts, features, baselines, and evaluation logic.

---

## 3. EDA Objectives

This EDA pipeline characterizes both cold-start settings under strict as-of evaluation.

Specific objectives:

- Define "new business" and "new user" with explicit temporal rules.
- Profile business review-accrual curves and user activity ramp-up curves.
- Catalog valid early signals for D1 and D2 separately.
- Construct explicit as-of popularity baselines for each subtrack.
- Define temporally valid evaluation cohorts for both D1 and D2.
- Identify which features are truly available at decision time.
- Prevent post-hoc leakage in cohort definitions, features, and labels.

---

## 4. Key Hypotheses to Test During EDA

| # | Hypothesis | How to Check |
|---|---|---|
| H1 | Many businesses remain information-poor after their first few observed interactions. | Business age vs. review accrual curves. |
| H2 | Business metadata and first observed interactions provide useful D1 signal before popularity dominates. | Feature coverage and baseline comparison for new businesses. |
| H3 | Pure zero-interaction user cold start is too sparse, but a warm-up definition using the first 1-3 interactions is tractable. | User activity ramp-up and cohort size analysis. |
| H4 | D2 baselines based on city/category popularity are strong but not unbeatable after a short user warm-up. | As-of popularity baseline performance after first K interactions. |
| H5 | Leakage risk is highest when "newness" or baseline rankings are defined using lifetime totals. | Leakage audit on cohort logic and baseline construction. |
| H6 | Business and user cold start need separate metrics and separate feature sets. | Compare cohort structure, coverage, and candidate evaluation tasks. |

---

## 5. Minimum Input Tables

| Table | Source File | Key Columns |
|---|---|---|
| `review` | `yelp_academic_dataset_review.json` | `review_id`, `user_id`, `business_id`, `stars`, `date`, `text` |
| `business` | `yelp_academic_dataset_business.json` | `business_id`, `city`, `state`, `categories`, `attributes`, `latitude`, `longitude` |
| `user` | `yelp_academic_dataset_user.json` | `user_id`, `yelping_since`, `fans`, `elite` |
| `tip` | `yelp_academic_dataset_tip.json` | `user_id`, `business_id`, `date` |
| `checkin` | `yelp_academic_dataset_checkin.json` | `business_id`, `date` |

---

## 6. Curated Tables to Build

| Table Name | Description | Key Columns |
|---|---|---|
| `business_lifecycle` | Per-business first/last observed review dates and accrual milestones. | `business_id`, `first_review_date`, `last_review_date`, `days_to_3rd_review`, `days_to_5th_review`, `days_to_10th_review`, `city`, `primary_category` |
| `business_cold_start_cohort` | Businesses that are new as of an evaluation date. | `business_id`, `as_of_date`, `prior_review_count`, `cohort_label`, `city`, `primary_category` |
| `business_early_signals` | Features available for D1 at the business cold-start boundary. | `business_id`, `as_of_date`, `categories`, `city`, `price_range`, `has_hours`, `attribute_count`, `prior_review_count`, `first_observed_review_stars`, `first_observed_review_length`, `first_checkin_seen`, `first_tip_seen` |
| `user_cold_start_cohort` | Users segmented by prior interaction count at each recommendation time. | `user_id`, `as_of_date`, `prior_review_count`, `prior_tip_count`, `cohort_label` |
| `user_warmup_profile` | User-side features available after the first K interactions. | `user_id`, `as_of_date`, `first_k_categories`, `first_k_cities`, `first_k_avg_stars`, `first_k_review_length_mean`, `first_k_primary_category_entropy`, `first_k_unique_business_count` |
| `popularity_baseline_asof` | As-of popularity rankings for candidate sets. | `baseline_type`, `as_of_date`, `city`, `category`, `business_id`, `prior_review_count`, `prior_avg_stars`, `popularity_rank` |
| `evaluation_cohorts` | D1 and D2 evaluation cohorts with candidate-set metadata. | `subtrack`, `entity_id`, `as_of_date`, `candidate_set_id`, `label_business_id`, `cohort_size` |

---

## 7. Proposed CLI Pipeline Stages

### Directory Structure

```
src/eda/track_d/
├── __init__.py
├── business_lifecycle.py         # Stage 1: Business accrual curves
├── business_cold_start.py        # Stage 2: D1 cohort definitions
├── business_early_signals.py     # Stage 3: D1 feature catalog
├── popularity_baseline.py        # Stage 4: As-of baseline construction
├── user_cold_start.py            # Stage 5: D2 cohort definitions
├── user_warmup_profile.py        # Stage 6: D2 feature catalog
├── evaluation_cohorts.py         # Stage 7: D1 and D2 evaluation cohorts
├── leakage_check.py              # Stage 8: Leakage-specific checks
└── summary_report.py             # Stage 9: Consolidated EDA report
```

### Stage-by-Stage Pipeline

**Stage 0 — Prerequisites (shared pipeline)**

```bash
python -m src.ingest.load_yelp_json --config configs/base.yaml
python -m src.validate.schema_checks --config configs/base.yaml
python -m src.curate.build_review_fact --config configs/base.yaml
```

**Stage 1 — Business Lifecycle**

```bash
python -m src.eda.track_d.business_lifecycle --config configs/track_d.yaml
```

- Input: `data/curated/review_fact.parquet`
- Outputs:
  - `outputs/tables/track_d_s1_business_lifecycle.parquet`
  - `outputs/figures/track_d_s1_review_accrual_curves.png`
  - `outputs/figures/track_d_s1_days_to_nth_review.png`
- Logic: Compute first review date and early accrual milestones for each business. Use these only as descriptive inputs to D1 cohort selection, not as future-aware features.

**Stage 2 — D1 Business Cold-Start Cohorts**

```bash
python -m src.eda.track_d.business_cold_start --config configs/track_d.yaml
```

- Input: Stage 1 output, temporal split definitions from Track A
- Outputs:
  - `outputs/tables/track_d_s2_business_cold_start_cohort.parquet`
  - `outputs/tables/track_d_s2_business_cohort_size_by_threshold.parquet`
  - `outputs/figures/track_d_s2_business_cohort_sizes.png`
- Logic: Define D1 using only as-of information, for example:
  - `prior_review_count = 0`
  - `prior_review_count <= 3`
  - `first_seen_within_last_30/90 days`

  Do not define "new" using total lifetime review count or future observation windows.

**Stage 3 — D1 Business Early Signals**

```bash
python -m src.eda.track_d.business_early_signals --config configs/track_d.yaml
```

- Input: `data/curated/business.parquet`, `data/curated/review_fact.parquet`, `data/curated/checkin.parquet`, `data/curated/tip.parquet`, Stage 2 output
- Outputs:
  - `outputs/tables/track_d_s3_business_early_signals.parquet`
  - `outputs/tables/track_d_s3_business_signal_summary.parquet`
- Logic: Collect only D1 features available at the recommendation time: categories, city, price range, hours present, attribute count, prior review count, first observed interaction summaries, first observed check-in/tip presence.

**Stage 4 — As-of Popularity Baselines**

```bash
python -m src.eda.track_d.popularity_baseline --config configs/track_d.yaml
```

- Input: `data/curated/review_fact.parquet`, Stage 2 output, Track A temporal splits
- Outputs:
  - `outputs/tables/track_d_s4_popularity_baseline_asof.parquet`
  - `outputs/figures/track_d_s4_popularity_concentration.png`
- Logic: Build baseline rankings separately for D1 and D2 using only interactions observed before each `as_of_date`. Candidate baselines include:
  - Most-reviewed business in city/category as of date
  - Highest prior average stars with minimum support as of date
  - Popularity within user's observed city/category envelope for D2

**Stage 5 — D2 User Cold-Start Cohorts**

```bash
python -m src.eda.track_d.user_cold_start --config configs/track_d.yaml
```

- Input: `data/curated/review_fact.parquet`, `data/curated/tip.parquet`
- Outputs:
  - `outputs/tables/track_d_s5_user_cold_start_cohort.parquet`
  - `outputs/figures/track_d_s5_user_activity_ramp.png`
  - `outputs/figures/track_d_s5_first_k_review_behavior.png`
- Logic: Segment users by prior observed interactions at each candidate recommendation time:
  - `K = 0` interactions
  - `K = 1` interaction
  - `K <= 3` interactions

  Recommend one primary D2 definition that is both feasible and explicit about the zero-interaction limitation.

**Stage 6 — D2 User Warm-Up Profiles**

```bash
python -m src.eda.track_d.user_warmup_profile --config configs/track_d.yaml
```

- Input: `data/curated/review_fact.parquet`, Stage 5 output
- Outputs:
  - `outputs/tables/track_d_s6_user_warmup_profile.parquet`
  - `outputs/tables/track_d_s6_user_feature_coverage.parquet`
- Logic: For users in the D2 cohort, summarize only features available after the first K observed interactions, such as category mix, city mix, mean star rating on the first K reviews, and mean review length.

**Stage 7 — Evaluation Cohorts**

```bash
python -m src.eda.track_d.evaluation_cohorts --config configs/track_d.yaml
```

- Input: Stage 2, Stage 4, Stage 5, Stage 6 outputs, temporal split definitions from Track A
- Outputs:
  - `outputs/tables/track_d_s7_eval_cohorts.parquet`
  - `outputs/tables/track_d_s7_eval_cohort_summary.parquet`
- Logic:
  - **D1:** identify new businesses that were cold as of recommendation time and received a relevant user interaction in the test period.
  - **D2:** identify new or near-new users and measure whether their next observed interaction appears in the ranked candidate set.

  Report D1 and D2 separately.

**Stage 8 — Leakage Check**

```bash
python -m src.eda.track_d.leakage_check --config configs/track_d.yaml
```

- Input: Stage 2 through Stage 7 outputs
- Outputs:
  - `outputs/tables/track_d_s8_leakage_report.parquet`
  - `outputs/logs/track_d_s8_leakage_check.log`
- Logic: Check for:
  - Use of lifetime business `stars`, lifetime `review_count`, or `average_stars`.
  - Any cohort field containing post-hoc outcomes such as "eventual" quality metrics.
  - Any baseline rank that uses interactions after the recommendation date.
  - Recommending businesses a user had already interacted with before the evaluation point.

**Stage 9 — Summary Report**

```bash
python -m src.eda.track_d.summary_report --config configs/track_d.yaml
```

- Input: All prior stage outputs
- Outputs:
  - `outputs/tables/track_d_s9_eda_summary.md`
- Logic: Summarize D1 and D2 separately, including primary cohort definitions, viable features, baseline strength, and modeling feasibility.

---

## 8. Quality Checks

| Check | Stage | Pass Criterion |
|---|---|---|
| Business lifecycle table covers all businesses | 1 | Row count = number of unique business_id in reviews |
| D1 cohort is non-trivial | 2 | ≥ 500 businesses in the primary D1 definition |
| D2 cohort is non-trivial | 5 | ≥ 1,000 users in the primary D2 definition |
| D1 feature table has at least 3 strong features | 3 | ≥ 3 features with > 80% coverage |
| D2 warm-up profile has at least 2 strong features | 6 | ≥ 2 features with > 70% coverage |
| Evaluation cohorts exist in the test period | 7 | Non-zero D1 and D2 test cohorts |
| Leakage audit passes | 8 | Zero critical leakage findings |

---

## 9. Leakage and Validity Checks

**Track D specific risks:**

1. **Lifetime aggregate leakage**: Business `stars`, business `review_count`, user `review_count`, and user `average_stars` are unsafe unless reconstructed as-of.

2. **Newness definition leakage**: Defining "new" via total lifetime outcomes or future windows is not allowed. Cohorts must be defined from information available at `as_of_date`.

3. **Post-hoc outcome leakage**: Fields such as `eventual_avg_stars` or other later outcomes must not appear in shared cohort or feature tables.

4. **Evaluation contamination**: Candidate sets must exclude businesses already seen by the user before the recommendation point.

5. **D2 scope confusion**: Zero-interaction user cold start and first-K-interaction user cold start are different tasks. The selected primary task must be named explicitly.

---

## 10. Recommended Visual Outputs

| # | Visualization | Purpose |
|---|---|---|
| V1 | Review accrual curves by business age | D1 ramp-up dynamics |
| V2 | D1 cohort size by threshold | Business cold-start definition |
| V3 | User activity ramp-up curve | D2 feasibility |
| V4 | First-K interaction profile summary | D2 feature availability |
| V5 | As-of popularity concentration curve | Baseline strength |
| V6 | D1 feature availability bars | Business-side feature selection |
| V7 | D2 feature availability bars | User-side feature selection |
| V8 | Evaluation cohort summary by subtrack | Modeling feasibility |

All visualizations use aggregate data only. No raw review text is displayed.

---

## 11. Exit Criteria (Definition of Done for EDA)

Track D EDA is complete when:

- [ ] D1 and D2 are defined as separate subtracks with separate cohort rules.
- [ ] Business lifecycle and user activity ramp-up are profiled.
- [ ] D1 early-signal catalog is complete with availability rates.
- [ ] D2 warm-up profile is complete with availability rates.
- [ ] Explicit as-of popularity baselines are constructed for both subtracks.
- [ ] D1 and D2 evaluation cohorts are defined within temporal splits.
- [ ] Leakage audit confirms that no post-hoc outcomes or lifetime aggregates are used improperly.
- [ ] Summary report is generated with separate D1 and D2 recommendations.

---

## 12. Handoff to Modeling

Upon EDA completion, the following artifacts are handed off:

| Artifact | Location | Consumer |
|---|---|---|
| Business lifecycle table | `data/curated/` | D1 cohort definition |
| D1 business cold-start cohort | `outputs/tables/` | D1 training data filtering |
| D1 business early signals | `data/curated/` | D1 feature engineering |
| D2 user cold-start cohort | `outputs/tables/` | D2 training data filtering |
| D2 user warm-up profile | `data/curated/` | D2 feature engineering |
| As-of popularity baselines | `outputs/tables/` | Baseline comparison |
| Evaluation cohorts | `outputs/tables/` | Model evaluation |

**Modeling phase will then:**

1. Train D1 business cold-start recommenders against D1 as-of popularity baselines.
2. Train D2 user cold-start recommenders against D2 as-of popularity baselines.
3. Report Recall@K and NDCG@K separately for D1 and D2.
4. Analyze which early signals matter for each subtrack.
5. Keep D1 and D2 results separate in every evaluation table and presentation slide.

---

*End of Track D EDA Pipeline Specification.*
