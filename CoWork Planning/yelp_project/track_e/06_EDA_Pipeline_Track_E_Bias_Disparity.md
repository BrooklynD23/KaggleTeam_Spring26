# Track E — EDA Pipeline: Bias and Disparity

**Track:** E — Fairness and Equity Audit
**Version:** 1.0
**Date:** 2026-03-10

---

## 1. Framing Question

> What patterns of bias or disparity appear in ratings and recommendations across neighborhoods or business categories, and how can models be constrained or corrected?

---

## 2. EDA Objectives

This EDA pipeline profiles **disparities in the Yelp ecosystem** across geographic and categorical dimensions to prepare for fairness-aware modeling. The focus is on documenting what imbalances exist in the data before any model amplifies or corrects them.

Specific objectives:

- Define subgroups for fairness analysis (neighborhoods, business categories, price tiers, city regions).
- Profile coverage differences across subgroups (review density, business count, user activity).
- Identify differences in star rating distributions across subgroups.
- Assess whether usefulness votes or recommendation exposure vary by subgroup.
- Quantify data imbalance that could lead to biased model behavior.
- Identify proxy risk (features that correlate with sensitive geographic or demographic dimensions).
- Establish baseline fairness metrics at the aggregate level.
- Document candidate mitigation levers for later modeling.

---

## 3. Key Hypotheses to Test During EDA

| # | Hypothesis | How to Check |
|---|---|---|
| H1 | Businesses in certain neighborhoods receive systematically fewer reviews, creating coverage disparity. | Review count distribution by neighborhood/zip code area. |
| H2 | Star rating distributions differ across business categories in ways that could bias cross-category recommendations. | Per-category star histograms; KS tests between categories. |
| H3 | Price tier (inferred from attributes) correlates with rating patterns — lower-priced businesses may receive different rating treatment. | Star distribution by price range. |
| H4 | Usefulness votes are unevenly distributed across neighborhoods — reviews of businesses in some areas receive systematically more/fewer "useful" votes. | Per-neighborhood mean useful vote comparison. |
| H5 | Data imbalance (certain categories/cities dominate the dataset) would cause a naïve model to perform well on majority groups and poorly on minorities. | Gini coefficient of review volume across subgroups. |
| H6 | Some features commonly used in recommendation models (review count, average stars) serve as proxies for geographic or category-based privilege. | Correlation between candidate features and subgroup membership. |

---

## 4. Minimum Input Tables

| Table | Source File | Key Columns |
|---|---|---|
| `review` | `yelp_academic_dataset_review.json` | `review_id`, `user_id`, `business_id`, `stars`, `date`, `useful` |
| `business` | `yelp_academic_dataset_business.json` | `business_id`, `city`, `state`, `categories`, `attributes`, `stars`, `review_count`, `latitude`, `longitude` |
| `user` | `yelp_academic_dataset_user.json` | `user_id`, `review_count`, `average_stars`, `elite` |

---

## 5. Curated Tables to Build

| Table Name | Description | Key Columns |
|---|---|---|
| `subgroup_definitions` | Business-level subgroup assignments for fairness analysis. | `business_id`, `city`, `neighborhood_proxy`, `primary_category`, `category_group`, `price_tier`, `review_volume_tier` |
| `subgroup_coverage` | Per-subgroup review counts, business counts, and user engagement metrics. | `subgroup_type`, `subgroup_value`, `business_count`, `review_count`, `mean_stars`, `mean_useful`, `user_count` |
| `star_disparity_table` | Star distribution statistics by subgroup. | `subgroup_type`, `subgroup_value`, `mean_stars`, `median_stars`, `std_stars`, `pct_5star`, `pct_1star` |
| `usefulness_disparity_table` | Usefulness vote statistics by subgroup. | `subgroup_type`, `subgroup_value`, `mean_useful`, `median_useful`, `pct_zero_useful` |
| `imbalance_report` | Data volume imbalance metrics across subgroups. | `subgroup_type`, `gini_coefficient`, `top_10pct_share`, `bottom_10pct_share` |
| `proxy_correlation_matrix` | Correlation between candidate model features and subgroup indicators. | `feature`, `subgroup_indicator`, `correlation`, `p_value` |

---

## 6. Proposed CLI Pipeline Stages

### Directory Structure

```
src/eda/track_e/
├── __init__.py
├── subgroup_definition.py       # Stage 1: Define subgroups
├── coverage_profile.py          # Stage 2: Coverage by subgroup
├── star_disparity.py            # Stage 3: Star rating disparities
├── usefulness_disparity.py      # Stage 4: Usefulness vote disparities
├── imbalance_analysis.py        # Stage 5: Data volume imbalance
├── proxy_risk.py                # Stage 6: Proxy variable identification
├── fairness_baseline.py         # Stage 7: Baseline fairness metrics
├── mitigation_candidates.py     # Stage 8: Candidate mitigation levers
└── summary_report.py            # Stage 9: Consolidated EDA report
```

### Stage-by-Stage Pipeline

**Stage 0 — Prerequisites (shared pipeline)**

```bash
python -m src.ingest.load_yelp_json --config configs/base.yaml
python -m src.validate.schema_checks --config configs/base.yaml
python -m src.curate.build_review_fact --config configs/base.yaml
```

**Stage 1 — Subgroup Definition**

```bash
python -m src.eda.track_e.subgroup_definition --config configs/track_e.yaml
```

- Input: `data/curated/business.parquet`
- Outputs:
  - `outputs/tables/track_e_s1_subgroup_definitions.parquet`
  - `outputs/tables/track_e_s1_subgroup_summary.parquet`
- Logic: Assign each business to subgroups along multiple dimensions:
  - **Geographic**: city, and neighborhood proxy (if neighborhood field exists; otherwise use city + zip or lat/lon clustering).
  - **Category**: primary category (first listed), and broader category group (Restaurants, Shopping, Health, Services, etc.).
  - **Price tier**: extracted from business attributes (e.g., RestaurantsPriceRange2); bucket into low/medium/high/missing.
  - **Review volume tier**: low (< 10), medium (10–50), high (50+) review businesses.

**Stage 2 — Coverage Profile**

```bash
python -m src.eda.track_e.coverage_profile --config configs/track_e.yaml
```

- Input: `data/curated/review_fact.parquet`, Stage 1 subgroup definitions
- Outputs:
  - `outputs/tables/track_e_s2_coverage_by_subgroup.parquet`
  - `outputs/figures/track_e_s2_coverage_by_city.png`
  - `outputs/figures/track_e_s2_coverage_by_category.png`
  - `outputs/figures/track_e_s2_coverage_by_price.png`
- Logic: For each subgroup dimension, compute business count, review count, unique user count, and mean engagement metrics. Produce bar charts showing coverage differences.

**Stage 3 — Star Rating Disparities**

```bash
python -m src.eda.track_e.star_disparity --config configs/track_e.yaml
```

- Input: `data/curated/review_fact.parquet`, Stage 1 subgroup definitions
- Outputs:
  - `outputs/tables/track_e_s3_star_disparity.parquet`
  - `outputs/figures/track_e_s3_star_dist_by_category.png`
  - `outputs/figures/track_e_s3_star_dist_by_price.png`
  - `outputs/figures/track_e_s3_star_dist_by_city.png`
- Logic: Compute star distribution statistics (mean, median, std, %5-star, %1-star) per subgroup. Run pairwise KS tests between major subgroups to quantify distributional differences. Plot comparative histograms.

**Stage 4 — Usefulness Vote Disparities**

```bash
python -m src.eda.track_e.usefulness_disparity --config configs/track_e.yaml
```

- Input: `data/curated/review_fact.parquet`, Stage 1 subgroup definitions
- Outputs:
  - `outputs/tables/track_e_s4_usefulness_disparity.parquet`
  - `outputs/figures/track_e_s4_useful_by_subgroup.png`
- Logic: Compute mean and median `useful` votes per subgroup. Compare the zero-useful fraction across subgroups. Identify whether certain neighborhoods or categories receive systematically fewer useful votes (which could mean less visibility in ranking-based surfaces).

**Stage 5 — Imbalance Analysis**

```bash
python -m src.eda.track_e.imbalance_analysis --config configs/track_e.yaml
```

- Input: Stage 2 coverage table
- Outputs:
  - `outputs/tables/track_e_s5_imbalance_report.parquet`
  - `outputs/figures/track_e_s5_lorenz_curve.png`
  - `outputs/figures/track_e_s5_gini_by_dimension.png`
- Logic: For each subgroup dimension, compute:
  - Gini coefficient of review volume distribution.
  - Share of reviews held by top-10% of subgroups.
  - Share held by bottom-10%.

  Plot Lorenz curves. A high Gini means a model trained on this data will disproportionately learn from majority subgroups.

**Stage 6 — Proxy Risk Analysis**

```bash
python -m src.eda.track_e.proxy_risk --config configs/track_e.yaml
```

- Input: `data/curated/review_fact.parquet`, Stage 1 subgroup definitions
- Outputs:
  - `outputs/tables/track_e_s6_proxy_correlations.parquet`
  - `outputs/figures/track_e_s6_proxy_heatmap.png`
- Logic: Compute correlation between common model features (review count, average rating, text length, user fan count) and subgroup membership indicators (city dummy, category dummy, price tier). Features that correlate strongly with subgroup identity are proxy risk candidates — a model that relies on them may implicitly discriminate. Produce a heatmap of correlations.

**Stage 7 — Fairness Baseline Metrics**

```bash
python -m src.eda.track_e.fairness_baseline --config configs/track_e.yaml
```

- Input: Stage 3 and Stage 4 disparity tables
- Outputs:
  - `outputs/tables/track_e_s7_fairness_metrics.parquet`
- Logic: Compute baseline fairness metrics at the **data level** (before any model):
  - **Demographic parity gap**: difference in mean rating or useful votes between subgroups.
  - **Coverage parity**: ratio of review counts between minority and majority subgroups.
  - **Calibration gap**: difference in star distribution shape between subgroups.

  These serve as the "natural" disparity in the data against which model-induced disparity can later be measured.

**Stage 8 — Mitigation Candidates**

```bash
python -m src.eda.track_e.mitigation_candidates --config configs/track_e.yaml
```

- Input: All prior stage outputs
- Outputs:
  - `outputs/tables/track_e_s8_mitigation_candidates.md`
- Logic: Based on EDA findings, document candidate mitigation strategies for later modeling:
  - Resampling or reweighting underrepresented subgroups.
  - Feature exclusion or regularization for proxy-risk features.
  - Post-hoc calibration of predictions across subgroups.
  - Fairness constraints during model training (e.g., equalized odds).
  - Aggregate-only reporting to avoid individual-level disparate impact claims.

**Stage 9 — Summary Report**

```bash
python -m src.eda.track_e.summary_report --config configs/track_e.yaml
```

- Input: All prior stage outputs
- Outputs:
  - `outputs/tables/track_e_s9_eda_summary.md`

---

## 7. Quality Checks

| Check | Stage | Pass Criterion |
|---|---|---|
| Subgroup definitions are non-overlapping within each dimension | 1 | Each business assigned exactly one value per dimension |
| Coverage table covers all reviews | 2 | Sum of review counts across subgroups = total reviews |
| Price tier extraction works for ≥ 30% of businesses | 1 | Price tier non-null rate ≥ 30% |
| KS tests are computed for major subgroup pairs | 3 | ≥ 10 pairwise comparisons reported |
| Imbalance metrics are finite and interpretable | 5 | Gini coefficients between 0 and 1 |

---

## 8. Leakage and Validity Checks

**Track E specific concerns:**

1. **Demographic inference prohibition**: Do NOT infer protected demographic attributes (race, gender, income) from usernames, review text, or neighborhood characteristics. Subgroups are defined by observable business/geographic attributes only.

2. **Ecological fallacy**: Neighborhood-level disparities do not imply individual-level discrimination. Frame findings carefully as aggregate patterns, not causal claims about bias.

3. **Confounding**: Rating differences across categories may reflect genuine quality differences, not bias. Document confounders explicitly and avoid causal language.

4. **Simpson's paradox risk**: Aggregate-level disparities may reverse when conditioning on relevant factors (e.g., category). Conduct at least one stratified check.

5. **Temporal confounding**: If subgroup composition changes over time (e.g., new cities added), apparent disparities may be artifacts of temporal coverage differences. Check for this.

---

## 9. Recommended Visual Outputs

| # | Visualization | Purpose |
|---|---|---|
| V1 | Coverage bar chart by city (top 20) | Geographic imbalance |
| V2 | Coverage bar chart by category group | Category imbalance |
| V3 | Star distribution comparison by price tier | Price-based disparity |
| V4 | Star distribution comparison by city | Geographic disparity |
| V5 | Useful vote comparison by subgroup | Visibility disparity |
| V6 | Lorenz curve of review volume | Concentration visualization |
| V7 | Proxy correlation heatmap | Proxy risk identification |
| V8 | Fairness metric summary table | Baseline disparity quantification |

All outputs use **aggregate-level data only**. No individual businesses, users, or reviews are identified. Minimum group size of 10 for any reported aggregate.

---

## 10. Exit Criteria (Definition of Done for EDA)

Track E EDA is complete when:

- [ ] Subgroups are defined along ≥ 3 dimensions (geography, category, price).
- [ ] Coverage disparities are quantified across all subgroup dimensions.
- [ ] Star rating disparities are profiled with statistical tests.
- [ ] Usefulness vote disparities are profiled.
- [ ] Data imbalance is quantified (Gini, concentration metrics).
- [ ] Proxy risk features are identified with correlation analysis.
- [ ] Baseline fairness metrics are computed.
- [ ] Mitigation candidates are documented.
- [ ] Summary report is generated.
- [ ] All outputs use aggregate-only reporting (minimum group size ≥ 10).

---

## 11. Handoff to Modeling

Upon EDA completion, the following artifacts are handed off:

| Artifact | Location | Consumer |
|---|---|---|
| Subgroup definitions table | `data/curated/` | Fairness-aware training |
| Disparity summary tables | `outputs/tables/` | Fairness constraint design |
| Proxy correlation matrix | `outputs/tables/` | Feature vetting |
| Baseline fairness metrics | `outputs/tables/` | Pre/post model comparison |
| Mitigation candidates document | `outputs/tables/` | Modeling strategy |

**Modeling phase will then:**

1. Train standard models (from Tracks A, B, D) and evaluate fairness metrics on their outputs.
2. Compare model-induced disparity against baseline (data-level) disparity.
3. Implement at least one mitigation strategy (reweighting, constrained optimization, or post-hoc calibration).
4. Report fairness metrics alongside accuracy metrics in all evaluations.
5. Produce an aggregate-safe fairness dashboard.

---

*End of Track E EDA Pipeline Specification.*
