# Track C — EDA Pipeline: Sentiment and Topic Drift

**Track:** C — Geo-Temporal NLP Analysis
**Version:** 1.0
**Date:** 2026-03-10

---

## 1. Framing Question

> How does sentiment and topic prevalence shift over time across cities/neighborhoods, and what events or business changes correlate with those shifts?

---

## 2. EDA Objectives

This EDA pipeline profiles the **temporal and geographic structure of review language** to prepare for trend detection, topic modeling, and event-correlation analysis. The focus is on understanding what data is available, how it is distributed across time and space, and whether meaningful signal exists for drift detection.

Specific objectives:

- Map city and neighborhood coverage across the dataset.
- Define temporal bins appropriate for trend analysis (monthly, quarterly).
- Profile text language characteristics and establish normalization assumptions.
- Compute baseline sentiment proxies and validate them against star ratings.
- Estimate topic prevalence using lightweight methods (keyword frequencies, TF-IDF clusters).
- Detect category-level and city-level drift patterns.
- Identify candidate events or business changes (open/close signals, attribute changes) that could correlate with sentiment shifts.
- Profile check-in volume as a supplementary temporal signal.

---

## 3. Key Hypotheses to Test During EDA

| # | Hypothesis | How to Check |
|---|---|---|
| H1 | Sentiment (as proxied by stars or text polarity) shows detectable trends within cities. | Monthly sentiment aggregates with trend-line fitting per city. |
| H2 | Topic prevalence varies by city and shifts over time (e.g., "delivery" mentions increase). | Keyword frequency time series per city. |
| H3 | Business openings and closings correlate with neighborhood-level sentiment shifts. | Cross-reference business `is_open` field with neighborhood sentiment changes. |
| H4 | Check-in volume changes precede or coincide with sentiment shifts. | Lagged correlation between check-in volume and sentiment aggregates. |
| H5 | Coverage is uneven — a few cities dominate, making city-level comparisons unequal. | City review-count distribution; identify "analyzable" cities. |
| H6 | Category-specific topics (e.g., "wait time" in restaurants) show different drift patterns than general topics. | Category-filtered keyword trends. |

---

## 4. Minimum Input Tables

| Table | Source File | Key Columns |
|---|---|---|
| `review` | `yelp_academic_dataset_review.json` | `review_id`, `business_id`, `stars`, `date`, `text` |
| `business` | `yelp_academic_dataset_business.json` | `business_id`, `city`, `state`, `categories`, `is_open`, `latitude`, `longitude`, `neighborhood` (if present) |
| `checkin` | `yelp_academic_dataset_checkin.json` | `business_id`, `date` |
| `tip` | `yelp_academic_dataset_tip.json` | `business_id`, `date`, `text` |

---

## 5. Curated Tables to Build

| Table Name | Description | Key Columns |
|---|---|---|
| `review_geo_temporal` | Reviews enriched with city, state, categories, and year-month bin. | `review_id`, `business_id`, `city`, `state`, `primary_category`, `year_month`, `stars`, `text_word_count`, `sentiment_proxy` |
| `city_coverage` | Per-city review counts by year, with analyzability flag. | `city`, `state`, `year`, `review_count`, `business_count`, `is_analyzable` |
| `monthly_sentiment_agg` | City × month sentiment aggregates. | `city`, `year_month`, `mean_stars`, `mean_sentiment`, `review_count`, `std_stars` |
| `keyword_trends` | Top-N keyword frequencies by city × quarter. | `city`, `year_quarter`, `keyword`, `frequency`, `relative_frequency` |
| `business_lifecycle` | Business open/close signals with temporal context. | `business_id`, `city`, `first_review_date`, `last_review_date`, `is_open`, `review_count`, `category` |
| `checkin_volume_monthly` | Aggregated check-in counts per business per month. | `business_id`, `city`, `year_month`, `checkin_count` |

---

## 6. Proposed CLI Pipeline Stages

### Directory Structure

```
src/eda/track_c/
├── __init__.py
├── geo_coverage.py              # Stage 1: City/neighborhood coverage
├── temporal_binning.py          # Stage 2: Temporal bin definition
├── text_normalization.py        # Stage 3: Text preprocessing profiling
├── sentiment_baseline.py        # Stage 4: Sentiment proxy computation
├── topic_prevalence.py          # Stage 5: Keyword/topic frequency analysis
├── drift_detection.py           # Stage 6: City and category drift
├── event_candidates.py          # Stage 7: Business change and event signals
├── checkin_correlation.py       # Stage 8: Check-in volume as temporal signal
└── summary_report.py            # Stage 9: Consolidated EDA report
```

### Stage-by-Stage Pipeline

**Stage 0 — Prerequisites (shared pipeline)**

```bash
python -m src.ingest.load_yelp_json --config configs/base.yaml
python -m src.validate.schema_checks --config configs/base.yaml
python -m src.curate.build_review_fact --config configs/base.yaml
```

**Stage 1 — Geographic Coverage**

```bash
python -m src.eda.track_c.geo_coverage --config configs/track_c.yaml
```

- Input: `data/curated/review_fact.parquet`, `data/curated/business.parquet`
- Outputs:
  - `outputs/tables/track_c_s1_city_coverage.parquet`
  - `outputs/tables/track_c_s1_state_coverage.parquet`
  - `outputs/figures/track_c_s1_city_review_count_bar.png`
  - `outputs/figures/track_c_s1_coverage_map.png` (if lat/lon available)
- Logic: Count reviews and businesses per city/state. Flag "analyzable" cities (e.g., ≥ 1,000 reviews). Identify top-20 cities by volume. If latitude/longitude are available, produce a geographic scatter plot.

**Stage 2 — Temporal Binning**

```bash
python -m src.eda.track_c.temporal_binning --config configs/track_c.yaml
```

- Input: `data/curated/review_fact.parquet`
- Outputs:
  - `outputs/tables/track_c_s2_review_volume_by_month.parquet`
  - `outputs/tables/track_c_s2_review_volume_by_quarter.parquet`
  - `outputs/figures/track_c_s2_volume_timeline.png`
- Logic: Bin reviews by year-month and year-quarter. Plot volume over time. Identify date range boundaries. Recommend granularity (monthly vs. quarterly) based on volume stability.

**Stage 3 — Text Normalization Profiling**

```bash
python -m src.eda.track_c.text_normalization --config configs/track_c.yaml
```

- Input: `data/curated/review_fact.parquet` (sampled)
- Outputs:
  - `outputs/tables/track_c_s3_text_stats.parquet`
  - `outputs/tables/track_c_s3_language_detection.parquet`
- Logic: On a sample (e.g., 100K reviews), compute text length, detect language (most should be English), identify non-English reviews. Compute basic text cleanliness metrics (HTML artifacts, encoding issues). Recommend normalization steps (lowercasing, punctuation handling, stop-word policy).

**Stage 4 — Sentiment Baseline**

```bash
python -m src.eda.track_c.sentiment_baseline --config configs/track_c.yaml
```

- Input: `data/curated/review_fact.parquet` (sampled or full for aggregates)
- Outputs:
  - `outputs/tables/track_c_s4_sentiment_by_city_month.parquet`
  - `outputs/figures/track_c_s4_sentiment_vs_stars.png`
  - `outputs/figures/track_c_s4_sentiment_timeseries_top_cities.png`
- Logic: Compute sentiment proxy (TextBlob polarity or VADER compound score) on review text sample. Validate against star ratings (correlation check). Aggregate to city × month level. Plot sentiment time series for top-5 cities.

**Stage 5 — Topic Prevalence**

```bash
python -m src.eda.track_c.topic_prevalence --config configs/track_c.yaml
```

- Input: `data/curated/review_fact.parquet`
- Outputs:
  - `outputs/tables/track_c_s5_keyword_trends.parquet`
  - `outputs/tables/track_c_s5_tfidf_cluster_summary.parquet`
  - `outputs/figures/track_c_s5_keyword_trend_lines.png`
- Logic: Define a curated keyword list targeting known topics (e.g., "delivery", "outdoor", "mask", "wait", "service", "price"). Compute keyword frequency by city × quarter. Optionally run lightweight TF-IDF + clustering on a sample to discover emergent topics. Plot keyword trend lines for top cities.

**Stage 6 — Drift Detection**

```bash
python -m src.eda.track_c.drift_detection --config configs/track_c.yaml
```

- Input: Stage 4 and Stage 5 outputs
- Outputs:
  - `outputs/tables/track_c_s6_sentiment_drift_by_city.parquet`
  - `outputs/tables/track_c_s6_topic_drift_by_city.parquet`
  - `outputs/figures/track_c_s6_drift_heatmap.png`
- Logic: For each analyzable city, compute rolling sentiment mean and keyword frequency slopes. Flag cities/periods with statistically significant drift (linear regression slope p-value < 0.05). Produce a heatmap of drift strength across cities × time periods.

**Stage 7 — Event and Business Change Candidates**

```bash
python -m src.eda.track_c.event_candidates --config configs/track_c.yaml
```

- Input: `data/curated/business.parquet`, `data/curated/review_fact.parquet`
- Outputs:
  - `outputs/tables/track_c_s7_business_lifecycle.parquet`
  - `outputs/tables/track_c_s7_event_candidates.parquet`
  - `outputs/figures/track_c_s7_open_close_timeline.png`
- Logic: Construct business lifecycle table (first review, last review, is_open flag). Identify periods of high business closure or opening in specific cities. Cross-reference with sentiment drift periods from Stage 6 to identify candidate event-drift correlations. Note: actual causal attribution is beyond EDA — this stage identifies *candidates* for further investigation.

**Stage 8 — Check-in Correlation**

```bash
python -m src.eda.track_c.checkin_correlation --config configs/track_c.yaml
```

- Input: `data/curated/checkin.parquet`, Stage 4 sentiment aggregates
- Outputs:
  - `outputs/tables/track_c_s8_checkin_volume_monthly.parquet`
  - `outputs/tables/track_c_s8_checkin_sentiment_correlation.parquet`
  - `outputs/figures/track_c_s8_checkin_vs_sentiment.png`
- Logic: Parse check-in timestamps and aggregate to city × month. Compute correlation between check-in volume and sentiment aggregates (contemporaneous and lagged). Plot dual-axis time series for top cities.

**Stage 9 — Summary Report**

```bash
python -m src.eda.track_c.summary_report --config configs/track_c.yaml
```

- Input: All prior stage outputs
- Outputs:
  - `outputs/tables/track_c_s9_eda_summary.md`

---

## 7. Quality Checks

| Check | Stage | Pass Criterion |
|---|---|---|
| City coverage is profiled | 1 | ≥ 5 cities flagged as analyzable (≥ 1,000 reviews) |
| Temporal bins have no gaps | 2 | Continuous year-month sequence for analyzable cities |
| Sentiment proxy correlates with stars | 4 | Spearman correlation > 0.3 |
| Keyword list is relevant | 5 | Manual review of top keywords confirms domain relevance |
| Drift detection is not degenerate | 6 | At least some cities show significant drift |

---

## 8. Leakage and Validity Checks

**Track C specific concerns:**

1. **Survivorship bias**: Analyzing only businesses that are still open biases toward positive trajectories. Include closed businesses in temporal analysis.

2. **Volume-sentiment confounding**: Cities with growing review volume may show sentiment shifts simply due to changing reviewer demographics, not genuine sentiment change. Monitor volume alongside sentiment.

3. **Keyword anachronism**: Using keywords that only became relevant after a certain date (e.g., pandemic-related terms) to analyze pre-event periods would be misleading. Document keyword temporal applicability.

4. **Aggregation artifact**: Very small monthly bins (few reviews) produce noisy sentiment estimates. Enforce minimum review count per bin before computing aggregates.

---

## 9. Recommended Visual Outputs

| # | Visualization | Purpose |
|---|---|---|
| V1 | City review-count bar chart (top 20) | Coverage understanding |
| V2 | Review volume timeline (monthly) | Temporal density |
| V3 | Sentiment proxy vs. stars scatter | Proxy validation |
| V4 | Sentiment time series for top cities | Trend detection |
| V5 | Keyword trend lines by city | Topic drift |
| V6 | Drift strength heatmap (city × period) | Cross-city comparison |
| V7 | Business open/close timeline by city | Event candidates |
| V8 | Check-in vs. sentiment dual-axis chart | Signal correlation |

All outputs use city/neighborhood-level aggregates. No raw review text is displayed.

---

## 10. Exit Criteria (Definition of Done for EDA)

Track C EDA is complete when:

- [ ] City and neighborhood coverage is mapped with analyzability flags.
- [ ] Temporal bins are defined and review volume is profiled.
- [ ] Text normalization assumptions are documented.
- [ ] Sentiment proxy is computed and validated against star ratings.
- [ ] Topic/keyword prevalence is profiled over time for top cities.
- [ ] Drift detection identifies candidate cities/periods with significant shifts.
- [ ] Business lifecycle events are cross-referenced with drift periods.
- [ ] Check-in volume correlation is assessed.
- [ ] Summary report is generated.
- [ ] All output files exist in `outputs/tables/` and `outputs/figures/`.

---

## 11. Handoff to Modeling

Upon EDA completion, the following artifacts are handed off:

| Artifact | Location | Consumer |
|---|---|---|
| City coverage table with analyzability flags | `data/curated/` | Scoping decisions |
| Monthly sentiment aggregates by city | `outputs/tables/` | Trend modeling |
| Keyword trend tables | `outputs/tables/` | Topic model training |
| Drift candidate dataset | `outputs/tables/` | Event-correlation analysis |
| Business lifecycle table | `data/curated/` | Event detection |
| Check-in volume monthly | `data/curated/` | Multi-signal modeling |

**Modeling phase will then:**

1. Apply proper topic modeling (LDA, BERTopic) to discover latent topics at scale.
2. Fit time-series models to sentiment and topic trends per city.
3. Detect changepoints formally (e.g., PELT, Bayesian changepoint detection).
4. Correlate changepoints with business lifecycle events and external calendars.
5. Produce an aggregate-safe geo-temporal dashboard.

---

*End of Track C EDA Pipeline Specification.*
