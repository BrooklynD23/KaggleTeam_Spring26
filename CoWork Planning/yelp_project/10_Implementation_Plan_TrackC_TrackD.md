# Implementation Plan: Track C and Track D EDA Pipelines

**Version:** 1.0
**Date:** 2026-03-13
**Scope:** Track C (Sentiment and Topic Drift) + Track D (Cold-Start Recommender)
**Status:** Draft — awaiting PM approval
**Predecessor documents:**
- `04_EDA_Pipeline_Track_C_Sentiment_Topic_Drift.md` (Track C EDA spec)
- `05_EDA_Pipeline_Track_D_Cold_Start_Recommender.md` (Track D EDA spec)
- `07_Implementation_Plan_Ingestion_TrackA_TrackB.md` (shared infrastructure baseline)
- `09_Resolution_TrackA_TrackB_Implementation_Plan.md` (resolved contracts)

---

## Table of Contents

1. [Part 1: Shared Input Contract and Curated Extensions](#part-1-shared-input-contract-and-curated-extensions)
2. [Part 2: Track C Pipeline Design](#part-2-track-c-pipeline-design)
3. [Part 3: Track D Pipeline Design](#part-3-track-d-pipeline-design)
4. [Part 4: Verification, Testing, and Implementation Order](#part-4-verification-testing-and-implementation-order)

---

## Adversarial Findings Incorporated

This plan was drafted after validating six high-severity findings from adversarial review against the actual codebase. Each finding is CONFIRMED and addressed in the relevant section. Cross-references are provided so reviewers can trace each fix to its origin.

| # | Finding | Verdict | Where Addressed |
|---|---------|---------|-----------------|
| F1 | Track C Stages 3–5 cannot read text from `review_fact.parquet` — it strips raw text to `text_char_count`/`text_word_count` only | CONFIRMED | §1.5 Raw Text Access Contract, §2 Stages 3–5 |
| F2 | No `neighborhood` field exists in the ingest schema; `is_open` is a snapshot field carried only in Track B's view | CONFIRMED | §1.4 No Neighborhood Field, §2 Stage 7 |
| F3 | `tip.parquet` and `checkin.parquet` are written by curation but not verified by the dispatcher; `checkin_expanded.parquet` does not exist | CONFIRMED (partial) | §1.2 Dispatcher Registration, §1.3 New Shared Artifact |
| F4 | `load_candidate_splits()` silently falls back to placeholder dates when Track A Stage 5 artifact is missing | CONFIRMED | §1.7 Split Dependency for Track D |
| F5 | Zero-history D1 cannot expose first-review features; existing as-of history logic is day-grain only | CONFIRMED | §3 Stages 3, 5, 6 |
| F6 | Track A leakage audit exits 0 always (soft); Track B raises RuntimeError (hard gate); dispatcher only blocks on non-zero exit | CONFIRMED | §3 Stage 8 |

---

## Part 1: Shared Input Contract and Curated Extensions

### 1.1 Existing Shared Artifacts (No Changes Required)

These artifacts are already written by `src/curate/build_review_fact.py` (line 60, `ENTITY_TABLES` loop at lines 245–248):

| Artifact | Status | Verified by Dispatcher | Consumers |
|---|---|---|---|
| `data/curated/review_fact.parquet` | Exists | Yes | Track A, Track C (temporal/star stats only), Track D |
| `data/curated/review_fact_track_b.parquet` | Exists | Yes | Track B only |
| `data/curated/review.parquet` | Exists | Yes | Track A (sentiment semijoin), Track C (NLP stages), Track D |
| `data/curated/business.parquet` | Exists | Yes | Track A, Track C, Track D |
| `data/curated/user.parquet` | Exists | **No** | Track D |
| `data/curated/tip.parquet` | Exists | **No** | Track C (Stage 8), Track D (Stages 3, 5) |
| `data/curated/checkin.parquet` | Exists | **No** | Track C (Stage 8 fallback), Track D (Stage 3) |
| `data/curated/snapshot_metadata.json` | Exists | Yes | Track B, Track C (Stage 7 proxy) |

**Key observation:** The curation code writes `user.parquet`, `tip.parquet`, and `checkin.parquet` via the `ENTITY_TABLES` loop, but the dispatcher's `required_outputs` for the `build_review_fact` stage (lines 150–156) does not list them. A silent curation failure could leave these files missing without any error.

### 1.2 Required Dispatcher Registration (Phase 0)

**File:** `scripts/pipeline_dispatcher.py`
**Location:** Lines 150–156, `build_review_fact` stage `required_outputs`

Add the following to the shared stage's `required_outputs` tuple:

- `"data/curated/user.parquet"`
- `"data/curated/tip.parquet"`
- `"data/curated/checkin.parquet"`
- `"data/curated/checkin_expanded.parquet"` (new, see §1.3)

**Rationale:** Track C and Track D both depend on `tip.parquet` and `checkin.parquet`. Track D depends on `user.parquet`. Without dispatcher verification, a partial curation run could leave these files missing and cause opaque downstream failures.

### 1.3 New Shared Artifact: `checkin_expanded.parquet`

**Owner:** `src/curate/build_review_fact.py` (extend existing curation module)

The raw `checkin.parquet` contains one row per business with a comma-separated `checkin_dates` VARCHAR. Both Track C (Stage 8: check-in volume correlation) and Track D (Stage 3: first-checkin-seen signal) need per-timestamp rows.

**New artifact:** `data/curated/checkin_expanded.parquet`

**Schema:**

| Column | Type | Description |
|---|---|---|
| `business_id` | VARCHAR | Foreign key to business |
| `checkin_date` | DATE | Single check-in date (parsed from comma-separated string, time component dropped) |

**Implementation approach:**

Add a new SQL constant `CHECKIN_EXPANDED_SQL` to `build_review_fact.py`:

```sql
SELECT
    c.business_id,
    CAST(TRIM(unnested.value) AS DATE) AS checkin_date
FROM read_parquet($1) c,
     UNNEST(STRING_SPLIT(c.date, ',')) AS unnested(value)
WHERE TRIM(unnested.value) != ''
```

Export via the existing `_export_parquet()` helper, after the `ENTITY_TABLES` loop. Add `"data/curated/checkin_expanded.parquet"` to the dispatcher's `required_outputs`.

**Risk:** The `checkin_dates` VARCHAR uses comma-separated timestamps (e.g., `"2016-04-26 19:49:16, 2016-08-30 18:36:57"`). Parsing must handle whitespace via `TRIM()` and cast to DATE (dropping the time component). Invalid timestamps should be logged and dropped, not silently propagated.

### 1.4 No Neighborhood Field

**Status:** The Yelp Academic Dataset as ingested does not include a `neighborhood` field.

**Evidence:** `src/ingest/load_yelp_json.py`, lines 26–41 lists exactly 14 business columns: `business_id`, `name`, `address`, `city`, `state`, `postal_code`, `latitude`, `longitude`, `stars`, `review_count`, `is_open`, `attributes`, `categories`, `hours`. No `neighborhood` field exists. A grep for `neighborhood` across all source files returns zero matches.

**Resolution:** Track C uses `city` as its primary geographic aggregation unit. `latitude`/`longitude` from `review_fact.parquet` can be used for geographic scatter plots but not as a substitute for neighborhood-level analysis. All Track C documentation and outputs must reference "city," not "neighborhood."

**Note:** The planning doc `04_EDA_Pipeline_Track_C` (Section 4, business table) lists `neighborhood (if present)`. This field is confirmed absent. Neighborhood analysis is **explicitly deferred** until ingestion materializes that field in a future data release.

### 1.5 Raw Text Access Contract

**Governing rule:** No raw review text in any output artifact (`CLAUDE.md` Key Constraint #1).

**Established safe pattern** (from `src/eda/track_a/text_profile.py`, lines 70–123):

1. Read raw text from `data/curated/review.parquet` only.
2. Semijoin against review_ids present in `review_fact.parquet` to restrict to curated reviews:
   ```sql
   WHERE r.review_id IN (SELECT review_id FROM read_parquet($review_fact_path))
   ```
3. Compute derived features (sentiment scores, keyword counts, topic assignments) in memory.
4. Drop all raw text columns before writing any output parquet or table.
5. Sample where full-corpus processing is infeasible (configurable via `configs/track_c.yaml`).

**Track C NLP stages (3, 4, 5) MUST follow this pattern.** The contract is:

- Read text from `review.parquet` only — never from `review_fact.parquet` (which deliberately strips text).
- Never persist raw text to any output file.
- Always semijoin against `review_fact.parquet` review_ids to maintain curated scope.
- All output parquet files must be aggregate-level or have raw text columns dropped before `.to_parquet()`.

**Enforcement:** Track C Stage 9 (summary report) includes a lightweight leakage scan that verifies no output parquet contains a `text`, `review_text`, or `raw_text` column.

### 1.6 Config Files

**File:** `configs/track_c.yaml`

```yaml
extends: "configs/base.yaml"

track:
  name: "track_c"
  label: "Sentiment and Topic Drift"

geography:
  min_city_reviews: 1000        # minimum reviews for a city to be "analyzable"
  top_n_cities: 20              # number of top cities for detailed analysis

temporal:
  bin_granularity: "month"      # "month" or "quarter"
  min_reviews_per_bin: 30       # minimum reviews per time bin for stable aggregates

nlp:
  sentiment_engine: "textblob"  # "textblob" or "vader"
  sample_size: 100000           # NLP sample size for text-heavy stages
  random_seed: 42
  keyword_list:
    - "delivery"
    - "outdoor"
    - "takeout"
    - "mask"
    - "covid"
    - "wait"
    - "service"
    - "price"
    - "parking"
    - "reservation"
  tfidf_n_clusters: 10
  tfidf_sample_size: 50000

drift:
  slope_p_threshold: 0.05       # significance threshold for drift detection
  rolling_window_months: 6

events:
  inactivity_close_proxy_days: 180  # days since last review to flag closure candidate

quality:
  sentiment_star_correlation_min: 0.3   # minimum Spearman correlation
  min_analyzable_cities: 5
```

**File:** `configs/track_d.yaml`

```yaml
extends: "configs/base.yaml"

track:
  name: "track_d"
  label: "Cold-Start Recommender"

splits:
  # Track D MUST use Track A's finalized splits from Stage 5 output.
  # These fallback values trigger a hard failure if require_stage5_artifact is true.
  t1: "2019-06-01"
  t2: "2020-09-01"
  require_stage5_artifact: true

cold_start:
  d1_thresholds:
    zero_history: 0
    sparse_history: 3
    emerging: 10
  d1_recency_windows_days: [30, 90]
  d2_k_values: [0, 1, 3]
  d2_primary_k: 0

interaction:
  # D2 threshold basis: count reviews + tips with strict earlier-date semantics
  d2_interaction_basis: "reviews_plus_tips"
  same_day_review_policy: "batch"   # all same-day reviews count as one batch
  tip_granularity: "day"            # tips aggregated to day level only

baseline:
  min_support_reviews: 3             # minimum reviews for avg-star baseline
  candidate_set_max_size: 100        # max businesses in a candidate set

evaluation:
  recall_k: [5, 10, 20]
  ndcg_k: [5, 10, 20]

leakage:
  banned_fields:
    - "business.stars"
    - "business.review_count"
    - "business.is_open"
    - "user.average_stars"
    - "user.review_count"
    - "user.fans"
    - "user.elite"
  hard_gate: true                    # Stage 8 raises on FAIL (Track B pattern)

quality:
  min_d1_cohort_size: 500
  min_d2_cohort_size: 1000
  min_feature_coverage: 0.80
  min_d2_feature_coverage: 0.70
```

### 1.7 Split Dependency for Track D

**Problem:** `load_candidate_splits()` in `src/common/artifacts.py` (lines 14–68) checks for `track_a_s5_candidate_splits.parquet`. If the parquet file is missing (line 37), it silently falls through to lines 67–68 and returns placeholder dates from `configs/track_a.yaml` (lines 8–11: `t1: "2019-06-01"`, `t2: "2020-09-01"`) with `source="config"`.

**Resolution:** Add a wrapper function `load_splits_strict()` in `src/common/artifacts.py`:

```python
def load_splits_strict(
    config: dict[str, Any],
    tables_dir: Path | None = None,
) -> tuple[str, str, str]:
    """Load candidate splits, failing hard if only placeholder dates are available.

    Raises RuntimeError when the source is 'config' and the track config
    has require_stage5_artifact=True.
    """
    t1, t2, source = load_candidate_splits(config, tables_dir)
    require = config.get("splits", {}).get("require_stage5_artifact", False)
    if source == "config" and require:
        raise RuntimeError(
            "Track D requires Track A Stage 5 split artifact "
            "(track_a_s5_candidate_splits.parquet) but it was not found. "
            "Run Track A through Stage 5 before running Track D. "
            f"Placeholder dates t1={t1}, t2={t2} were NOT used."
        )
    return t1, t2, source
```

**All Track D stages that load splits (Stages 2, 4, 5, 7) must use `load_splits_strict()` instead of `load_candidate_splits()`.**

### 1.8 Ownership Boundaries

| Owner | Scope |
|---|---|
| `src/curate/` + `scripts/pipeline_dispatcher.py` + `configs/` + `requirements.txt` | Shared infrastructure |
| `src/eda/track_c/*` | Track C implementation |
| `src/eda/track_d/*` | Track D implementation |

**No Track C-to-Track D artifact dependency.** Track C and Track D read only from shared curated artifacts and their own prior stage outputs. Neither track reads from the other's `outputs/tables/` directory.

### 1.9 New Dependencies

Add to `requirements.txt`:

```
langdetect>=1.0.9
```

`textblob` is already in the dependency contract (used by Track A `text_profile.py`). Verify it is present; add if missing.

The dispatcher's import-check block should verify `langdetect` is importable before running Track C.

---

## Part 2: Track C Pipeline Design

### Track C Dependency Graph

```
shared (ingest → validate → curate)
    │
    ▼
S1: geo_coverage
    │
    ▼
S2: temporal_binning
    │
    ▼
S3: text_normalization          ← reads review.parquet (semijoin)
    │
    ▼
S4: sentiment_baseline          ← reads review.parquet (semijoin)
    │
    ▼
S5: topic_prevalence            ← reads review.parquet (semijoin)
    │
    ▼
S6: drift_detection             ← reads S4 + S5 outputs
    │
    ├─────────────┐
    ▼             ▼
S7: event_       S8: checkin_
    candidates       correlation
    │             │
    └──────┬──────┘
           ▼
S9: summary_report
```

The analyzable-city filter computed in S1 is reused by S4–S8 to restrict geographic scope.

### Track C Module Map

```
src/eda/track_c/
├── __init__.py
├── geo_coverage.py              # S1
├── temporal_binning.py          # S2
├── text_normalization.py        # S3
├── sentiment_baseline.py        # S4
├── topic_prevalence.py          # S5
├── drift_detection.py           # S6
├── event_candidates.py          # S7
├── checkin_correlation.py       # S8
└── summary_report.py            # S9
```

### Stage 1 — Geographic Coverage (`geo_coverage.py`)

```bash
python -m src.eda.track_c.geo_coverage --config configs/track_c.yaml
```

**Inputs:**
- `data/curated/review_fact.parquet` — for `city`, `state`, `latitude`, `longitude`, review counts
- `data/curated/business.parquet` — for per-business city/state
- `configs/track_c.yaml` — `geography.min_city_reviews`, `geography.top_n_cities`

**Outputs:**
- `outputs/tables/track_c_s1_city_coverage.parquet`
- `outputs/tables/track_c_s1_state_coverage.parquet`
- `outputs/tables/track_c_s1_city_variant_diagnostic.parquet`
- `outputs/figures/track_c_s1_city_review_count_bar.png`
- `outputs/figures/track_c_s1_coverage_map.png`

**Key logic:**

1. Aggregate reviews per city from `review_fact.parquet`.
2. Derive `normalized_city = LOWER(TRIM(city))` and `primary_category = TRIM(SPLIT_PART(categories, ',', 1))` inline via SQL. Keep raw `city` in curated tables; normalization is a query convention, not a rewritten base field.
3. Flag cities with >= `min_city_reviews` as analyzable.
4. Write `city_coverage` with columns: `city`, `normalized_city`, `state`, `review_count`, `business_count`, `is_analyzable`, `first_review_date`, `last_review_date`.
5. Write `city_variant_diagnostic` — groups raw city names that map to the same `normalized_city` — for manual review. Spell-variant merging is diagnostic only; do not auto-merge.
6. Top-N cities bar chart; lat/lon scatter if coordinates available.

**No raw text access needed.** Risk: Low.

### Stage 2 — Temporal Binning (`temporal_binning.py`)

```bash
python -m src.eda.track_c.temporal_binning --config configs/track_c.yaml
```

**Inputs:**
- `data/curated/review_fact.parquet`
- `configs/track_c.yaml` — `temporal.bin_granularity`, `temporal.min_reviews_per_bin`

**Outputs:**
- `outputs/tables/track_c_s2_review_volume_by_month.parquet`
- `outputs/tables/track_c_s2_review_volume_by_quarter.parquet`
- `outputs/figures/track_c_s2_volume_timeline.png`

**Key logic:**

1. Bin reviews by `review_year` and `review_month` (both available in `review_fact.parquet`).
2. Compute quarterly bins from monthly bins.
3. Identify analyzable date ranges: continuous months with >= `min_reviews_per_bin` reviews.
4. Plot volume timeline with overall and per-top-city facets.
5. Recommend granularity (monthly vs. quarterly) based on volume stability.

**No raw text access needed.** Risk: Low.

### Stage 3 — Text Normalization Profiling (`text_normalization.py`)

```bash
python -m src.eda.track_c.text_normalization --config configs/track_c.yaml
```

**Inputs:**
- `data/curated/review.parquet` — for raw `text` (SEMIJOIN against `review_fact.parquet`)
- `data/curated/review_fact.parquet` — for review_id scope
- `configs/track_c.yaml` — `nlp.sample_size`, `nlp.random_seed`

**Outputs:**
- `outputs/tables/track_c_s3_text_stats.parquet` — aggregate text quality metrics
- `outputs/tables/track_c_s3_language_detection.parquet` — language distribution summary

**CRITICAL TEXT CONTRACT (Finding F1):**

1. Read text from `review.parquet` only.
2. Semijoin: `WHERE r.review_id IN (SELECT review_id FROM read_parquet($review_fact_path))`.
3. Sample via `USING SAMPLE {sample_size} ROWS (REPEATABLE ({seed}))`.
4. Compute metrics in-memory: text length distribution, non-ASCII rate, HTML artifact detection, language detection (`langdetect`).
5. **Drop `text` column before any `.to_parquet()` call.**
6. Output is aggregate-only: counts and percentages by language, quality metric distributions (mean, median, P5, P95 of text length).

Risk: Medium — first stage that touches raw text. Must be carefully implemented per the semijoin contract.

### Stage 4 — Sentiment Baseline (`sentiment_baseline.py`)

```bash
python -m src.eda.track_c.sentiment_baseline --config configs/track_c.yaml
```

**Inputs:**
- `data/curated/review.parquet` — for raw `text` (SEMIJOIN)
- `data/curated/review_fact.parquet` — for `review_id`, `city`, `review_year`, `review_month`, `review_stars`
- `configs/track_c.yaml` — `nlp.sentiment_engine`, `nlp.sample_size`

**Outputs:**
- `outputs/tables/track_c_s4_sentiment_by_city_month.parquet`
- `outputs/figures/track_c_s4_sentiment_vs_stars.png`
- `outputs/figures/track_c_s4_sentiment_timeseries_top_cities.png`

**Key logic:**

1. Sample reviews via semijoin pattern (see §1.5).
2. Compute sentiment polarity (TextBlob polarity or VADER compound, configurable).
3. **Drop raw text from DataFrame.**
4. Join sentiment scores back to `review_fact` metadata (city, year_month) using `review_id`.
5. Aggregate to city × month: `mean_sentiment`, `std_sentiment`, `review_count`, `mean_stars`.
6. Validate: compute Spearman correlation between sentiment and star ratings. Log warning if < `quality.sentiment_star_correlation_min`.
7. Filter to analyzable cities only (from Stage 1 output or min-reviews threshold).
8. Plot: sentiment-vs-stars scatter for proxy validation; top-city sentiment time series.

**CRITICAL:** All outputs are aggregate (city × month level). No per-review sentiment scores in output parquet. This follows the established pattern from `src/eda/track_a/text_profile.py:70–123`.

Risk: Medium.

### Stage 5 — Topic Prevalence (`topic_prevalence.py`)

```bash
python -m src.eda.track_c.topic_prevalence --config configs/track_c.yaml
```

**Inputs:**
- `data/curated/review.parquet` — for raw `text` (SEMIJOIN)
- `data/curated/review_fact.parquet` — for `review_id`, `city`, `review_year`, `review_month`, `categories`
- `configs/track_c.yaml` — `nlp.keyword_list`, `nlp.tfidf_n_clusters`, `nlp.tfidf_sample_size`

**Outputs:**
- `outputs/tables/track_c_s5_keyword_trends.parquet`
- `outputs/tables/track_c_s5_tfidf_cluster_summary.parquet` (optional)
- `outputs/figures/track_c_s5_keyword_trend_lines.png`

**Key logic:**

1. Semijoin text from `review.parquet` (see §1.5).
2. For each keyword in the configured list, compute case-insensitive presence per review (boolean flag).
3. **Drop raw text.**
4. Join keyword flags to `review_fact` metadata.
5. Aggregate keyword frequency to city × quarter: `keyword`, `city`, `year_quarter`, `frequency`, `relative_frequency`.
6. Optional: TF-IDF + KMeans clustering on a subsample for topic discovery. Output cluster term summaries only (top-10 terms per cluster), no raw text.

Risk: Medium. Same text access contract. TF-IDF vectorization must use the sample, not the full corpus.

### Stage 6 — Drift Detection (`drift_detection.py`)

```bash
python -m src.eda.track_c.drift_detection --config configs/track_c.yaml
```

**Inputs:**
- `outputs/tables/track_c_s4_sentiment_by_city_month.parquet` (Stage 4)
- `outputs/tables/track_c_s5_keyword_trends.parquet` (Stage 5)
- `configs/track_c.yaml` — `drift.slope_p_threshold`, `drift.rolling_window_months`

**Outputs:**
- `outputs/tables/track_c_s6_sentiment_drift_by_city.parquet`
- `outputs/tables/track_c_s6_topic_drift_by_city.parquet`
- `outputs/figures/track_c_s6_drift_heatmap.png`

**Key logic:**

1. For each analyzable city, fit OLS regression on monthly sentiment time series. Record slope, p-value, R².
2. Compute rolling sentiment mean (window = `rolling_window_months`) and flag periods with significant change (|slope| > threshold AND p < `slope_p_threshold`).
3. Repeat for keyword frequency trends per city.
4. Produce heatmap: cities (rows) × time periods (columns) × drift strength (color).
5. Output drift tables with: `city`, `metric`, `period_start`, `period_end`, `slope`, `p_value`, `is_significant`.

**No raw text access.** Risk: Low.

### Stage 7 — Event Candidates (`event_candidates.py`)

```bash
python -m src.eda.track_c.event_candidates --config configs/track_c.yaml
```

**Inputs:**
- `data/curated/business.parquet` — for `is_open`, `categories`, `city`
- `data/curated/review_fact.parquet` — for per-business first/last review dates
- `data/curated/snapshot_metadata.json` — for snapshot date reference
- `outputs/tables/track_c_s6_sentiment_drift_by_city.parquet` (Stage 6)
- `configs/track_c.yaml` — `events.inactivity_close_proxy_days`

**Outputs:**
- `outputs/tables/track_c_s7_business_lifecycle.parquet`
- `outputs/tables/track_c_s7_event_candidates.parquet`
- `outputs/figures/track_c_s7_open_close_timeline.png`

**Key logic (Finding F2 — event proxies only):**

1. Build business lifecycle table from `review_fact.parquet`: `first_review_date = MIN(review_date)`, `last_review_date = MAX(review_date)`, review count, `primary_category`.
2. Read `is_open` from `business.parquet` — NOT from `review_fact_track_b.parquet` (Track B only).
3. Compute event proxies:
   - `opening_proxy_date = first_review_date` (the first review is the earliest observable signal of a business existing)
   - `closure_candidate = (is_open = 0) AND (days_since_last_review >= inactivity_close_proxy_days)`, where `days_since_last_review` is measured from `last_review_date` to the snapshot date from `snapshot_metadata.json`.
4. `is_open` is reported as **snapshot context**, not a true event timestamp. No exact close date is available.
5. Identify periods of high business closure/opening per city. Cross-reference with sentiment drift periods from Stage 6.
6. Output candidate event-drift correlations. This is EDA-level — no causal claims.

Risk: Low. No text access. `is_open` is a snapshot field used appropriately as a descriptive lifecycle indicator.

### Stage 8 — Check-in Correlation (`checkin_correlation.py`)

```bash
python -m src.eda.track_c.checkin_correlation --config configs/track_c.yaml
```

**Inputs:**
- `data/curated/checkin_expanded.parquet` (new shared artifact, see §1.3)
- `data/curated/business.parquet` — for business_id → city mapping
- `outputs/tables/track_c_s4_sentiment_by_city_month.parquet` (Stage 4)
- `configs/track_c.yaml`

**Outputs:**
- `outputs/tables/track_c_s8_checkin_volume_monthly.parquet`
- `outputs/tables/track_c_s8_checkin_sentiment_correlation.parquet`
- `outputs/figures/track_c_s8_checkin_vs_sentiment.png`

**Key logic:**

1. Aggregate `checkin_expanded.parquet` to business × month.
2. Join to city via `business.parquet`.
3. Aggregate to city × month checkin volume.
4. Compute Pearson/Spearman correlation with sentiment aggregates (contemporaneous and 1-month lag).
5. Dual-axis plot for top cities.

**Fallback:** If `checkin_expanded.parquet` does not exist, parse `checkin.parquet` inline with explicit comma-split + date cast. Log a warning recommending the shared artifact.

**Dependency:** Requires `checkin_expanded.parquet` from §1.3.

Risk: Medium — depends on new shared artifact.

### Stage 9 — Summary Report (`summary_report.py`)

```bash
python -m src.eda.track_c.summary_report --config configs/track_c.yaml
```

**Inputs:** All prior stage outputs (S1–S8 tables and figures)

**Outputs:**
- `outputs/tables/track_c_s9_eda_summary.md`

**Key logic:**

1. Read all stage output tables.
2. Generate consolidated markdown report with:
   - Dataset coverage summary (analyzable cities, date range, review volume)
   - Hypothesis assessment table (H1–H6 with findings and evidence references)
   - Key figures referenced by filename (not embedded)
   - Modeling feasibility assessment for drift detection and event correlation
3. **Lightweight leakage scan (text-column check):**
   - Describe all `track_c_*.parquet` files in `outputs/tables/`.
   - Flag any column named `text`, `review_text`, or `raw_text`.
   - Flag any parquet with per-review rows containing a text-like VARCHAR column.
   - Log findings. This is a **soft audit** (exit 0) — Track C has no temporal prediction task, so the key leakage concern is text exposure rather than future data leakage.
4. Document limitations: city-only geography, event proxies not true timestamps, sentiment proxy vs. star correlation caveats.

Risk: Low.

---

## Part 3: Track D Pipeline Design

### Track D Dependency Graph

```
shared (ingest → validate → curate)
    │
    │     Track A Stage 5
    │     (split selection)
    │         │
    │    ┌────┘  REQUIRED DEPENDENCY
    │    │       (hard-fail via load_splits_strict)
    │    ▼
    ├──▶ S1: business_lifecycle (report-only)
    │    │
    │    ▼
    ├──▶ S2: business_cold_start (D1 cohorts)
    │    │
    │    ▼
    ├──▶ S3: business_early_signals (D1 features)
    │    │
    │    ▼
    ├──▶ S4: popularity_baseline (D1 + D2)
    │    │
    │    ▼
    ├──▶ S5: user_cold_start (D2 cohorts)
    │    │
    │    ▼
    ├──▶ S6: user_warmup_profile (D2 features)
    │    │         │
    │    ▼         ▼
    ├──▶ S7: evaluation_cohorts (D1 + D2)
    │    │
    │    ▼
    ├──▶ S8: leakage_check ← HARD GATE (raises on FAIL)
    │    │
    │    ▼
    └──▶ S9: summary_report
```

**Alternative view:** S1 is report-only and does not feed into S2–S7 feature construction. S2 → S3 → S4 → S7 is the D1 path. S5 → S6 → S4/S7 is the D2 path. S8 audits S2–S7. S9 summarizes all.

### Track D Module Map

```
src/eda/track_d/
├── __init__.py
├── business_lifecycle.py        # S1  (report-only)
├── business_cold_start.py       # S2  (D1 cohorts)
├── business_early_signals.py    # S3  (D1 features)
├── popularity_baseline.py       # S4  (D1 + D2 baselines)
├── user_cold_start.py           # S5  (D2 cohorts)
├── user_warmup_profile.py       # S6  (D2 features)
├── evaluation_cohorts.py        # S7  (D1 + D2 eval)
├── leakage_check.py             # S8  (HARD GATE)
└── summary_report.py            # S9
```

### Stage 1 — Business Lifecycle (`business_lifecycle.py`)

```bash
python -m src.eda.track_d.business_lifecycle --config configs/track_d.yaml
```

**Inputs:**
- `data/curated/review_fact.parquet`
- `configs/track_d.yaml`

**Outputs:**
- `outputs/tables/track_d_s1_business_lifecycle.parquet`
- `outputs/figures/track_d_s1_review_accrual_curves.png`
- `outputs/figures/track_d_s1_days_to_nth_review.png`

**Key logic:**

For each `business_id`, compute:
- `first_review_date`: MIN(review_date)
- `last_review_date`: MAX(review_date)
- `total_review_count`: COUNT(*)
- `days_to_3rd_review`, `days_to_5th_review`, `days_to_10th_review`: diff between first and Nth review date
- `city`, `primary_category` (first value from categories split)

Plot: CDF of days-to-Nth-review. Median accrual curves.

**IMPORTANT:** This table is **purely descriptive**. `total_review_count`, `last_review_date`, and `days_to_nth_review` are lifetime values used ONLY for lifecycle profiling. **They must NOT be used as features or cohort inputs in any downstream stage (S2–S7).**

Risk: Low.

### Stage 2 — D1 Business Cold-Start Cohorts (`business_cold_start.py`)

```bash
python -m src.eda.track_d.business_cold_start --config configs/track_d.yaml
```

**Inputs:**
- `data/curated/review_fact.parquet`
- Track A Stage 5 splits via `load_splits_strict()` — **hard-fails** if artifact missing (Finding F4)
- `configs/track_d.yaml` — `cold_start.d1_thresholds`, `cold_start.d1_recency_windows_days`

**Outputs:**
- `outputs/tables/track_d_s2_business_cold_start_cohort.parquet`
- `outputs/tables/track_d_s2_business_cohort_size_by_threshold.parquet`
- `outputs/figures/track_d_s2_business_cohort_sizes.png`

**Key logic:**

1. Load T1/T2 splits using `load_splits_strict()`.
2. For each `as_of_date` in [T1, T2]:
   - Compute `prior_review_count` for each business as of that date: `COUNT(*) WHERE review_date < as_of_date`.
   - Assign cohort labels based on `d1_thresholds`:
     - `zero_history`: prior_review_count = 0
     - `sparse_history`: 1 ≤ prior_review_count ≤ 3
     - `emerging`: 4 ≤ prior_review_count ≤ 10
     - `established`: prior_review_count ≥ 11
   - Also flag businesses first seen within `d1_recency_windows_days` of the as_of_date.
3. Report cohort sizes by threshold.

**CRITICAL:** "Newness" is defined strictly as-of. Never use `total_review_count` from the lifecycle table (Stage 1) to define cohorts. The as-of prior count must be computed from `review_fact.parquet` with a date filter.

Risk: Medium — temporal logic must be strictly as-of.

### Stage 3 — D1 Business Early Signals (`business_early_signals.py`)

```bash
python -m src.eda.track_d.business_early_signals --config configs/track_d.yaml
```

**Inputs:**
- `data/curated/business.parquet` — for `categories`, `city`, `attributes`, `hours`, `latitude`, `longitude`
- `data/curated/review_fact.parquet`
- `data/curated/tip.parquet` — for first-tip-seen signal
- `data/curated/checkin_expanded.parquet` — for first-checkin-seen signal
- `outputs/tables/track_d_s2_business_cold_start_cohort.parquet` (Stage 2)
- `configs/track_d.yaml`

**Outputs:**
- `outputs/tables/track_d_s3_business_early_signals.parquet`
- `outputs/tables/track_d_s3_business_signal_summary.parquet`

**Key logic (Finding F5 — zero-history constraint):**

For each business in the D1 cohort, collect features available at cold-start time:

**Static features (always available, even for zero_history):**
- `categories` (from `business.parquet`)
- `city`, `state` (from `business.parquet`)
- `price_range` (parsed from `attributes` JSON in `business.parquet`)
- `has_hours` (boolean, from `business.parquet`)
- `attribute_count` (count of non-null attributes)
- `latitude`, `longitude`

**As-of interaction features (available only for cohorts with prior_review_count > 0):**
- `prior_review_count` (carried from Stage 2)
- `prior_review_mean_stars` (mean star rating of reviews before as_of_date)
- `prior_review_mean_length` (mean text_word_count of reviews before as_of_date)
- `prior_tip_count` (tips before as_of_date)
- `prior_checkin_count` (checkins before as_of_date)

**REMOVED from prior draft (Finding F5):** `first_observed_review_stars` and `first_observed_review_length`. These are event-sequence features that the existing day-grain as-of logic (`user_history_profile.py:29–55`) cannot safely extract without introducing synthetic within-day ordering. Replace with `prior_review_mean_stars` and `prior_review_mean_length` which are safe day-grain aggregates.

**CRITICAL CONSTRAINT:** For the pure zero-interaction cohort (`prior_review_count = 0`), ALL as-of interaction features are **NULL**. Only static features are valid. The `signal_summary` table must report coverage rates separately for each cohort tier.

**BANNED FIELDS (from config `leakage.banned_fields`):** Do NOT use `business.stars`, `business.review_count`, or `business.is_open` from `business.parquet` — these are snapshot-level lifetime aggregates.

**Implementation note:** This stage cannot reuse Track A's `build_business_history()` from `user_history_profile.py` because that function operates on a day-grain cumulative window. D1 needs prior-interaction aggregates scoped to the cohort's as_of_date, which requires a fresh query with explicit date filtering.

Risk: High — complex as-of logic with multiple sources.

### Stage 4 — As-of Popularity Baselines (`popularity_baseline.py`)

```bash
python -m src.eda.track_d.popularity_baseline --config configs/track_d.yaml
```

**Inputs:**
- `data/curated/review_fact.parquet`
- `outputs/tables/track_d_s2_business_cold_start_cohort.parquet` (Stage 2)
- Track A splits via `load_splits_strict()`
- `configs/track_d.yaml` — `baseline.min_support_reviews`

**Outputs:**
- `outputs/tables/track_d_s4_popularity_baseline_asof.parquet`
- `outputs/figures/track_d_s4_popularity_concentration.png`

**Key logic:**

For each `as_of_date`:

1. Compute as-of popularity for each business: `prior_review_count` and `prior_avg_stars` (using only reviews with `review_date < as_of_date`).
2. Rank businesses within each city/category by popularity.
3. Baseline types:
   - `most_reviewed_in_city`: highest `prior_review_count` in the same city
   - `highest_rated_in_city`: highest `prior_avg_stars` with >= `min_support_reviews`
   - `most_reviewed_in_category`: same, within primary category
4. Output: baseline rankings for D1 and D2 candidate sets.
5. Plot popularity concentration (Lorenz curve / Gini coefficient by city).

**CRITICAL:** Baselines must use only as-of counts. Never use `business.review_count` or `business.stars` from the entity table.

Risk: Medium.

### Stage 5 — D2 User Cold-Start Cohorts (`user_cold_start.py`)

```bash
python -m src.eda.track_d.user_cold_start --config configs/track_d.yaml
```

**Inputs:**
- `data/curated/review_fact.parquet`
- `data/curated/tip.parquet` — for prior tip count
- Track A splits via `load_splits_strict()`
- `configs/track_d.yaml` — `cold_start.d2_k_values`, `cold_start.d2_primary_k`, `interaction.*`

**Outputs:**
- `outputs/tables/track_d_s5_user_cold_start_cohort.parquet`
- `outputs/figures/track_d_s5_user_activity_ramp.png`
- `outputs/figures/track_d_s5_first_k_review_behavior.png`

**Key logic (Finding F5 — D2 thresholds):**

For each `as_of_date` in [T1, T2]:

1. Compute `prior_review_count` for each user (reviews with `review_date < as_of_date`).
2. Compute `prior_tip_count` from `tip.parquet` (tips with `date < as_of_date`).
3. Compute `prior_total_interaction_count = prior_review_count + prior_tip_count`.
4. Assign D2 cohort labels based on `d2_k_values`:
   - K=0: `zero_history` (no prior interactions)
   - K=1: `first_interaction` (exactly 1 prior interaction)
   - K=3: `early` (2–3 prior interactions)
5. **Same-day review policy:** All reviews on the same date count as one batch. If a user reviews 3 businesses on the same day, `prior_review_count` increments by 3 (count of reviews), but no synthetic within-day ordering is introduced. Tips use day-level aggregates only.
6. Plot user activity ramp-up: CDF of `prior_review_count` at each `as_of_date`.
7. Report cohort sizes. Log warning if any cohort has fewer than `quality.min_d2_cohort_size` members.

Risk: Medium.

### Stage 6 — D2 User Warm-Up Profiles (`user_warmup_profile.py`)

```bash
python -m src.eda.track_d.user_warmup_profile --config configs/track_d.yaml
```

**Inputs:**
- `data/curated/review_fact.parquet`
- `outputs/tables/track_d_s5_user_cold_start_cohort.parquet` (Stage 5)
- `configs/track_d.yaml`

**Outputs:**
- `outputs/tables/track_d_s6_user_warmup_profile.parquet`
- `outputs/tables/track_d_s6_user_feature_coverage.parquet`

**Key logic (Finding F5 — warm-up as aggregates, not event-sequence):**

For users in the D2 cohort with K > 0:

1. Collect ALL prior reviews before `as_of_date`, ordered by `review_date`.
2. Compute warm-up features as **as-of aggregates over all prior reviews/tips available before `as_of_date`**, not exact event-sequence "first K" reconstructions:
   - `prior_categories`: set of categories from all prior reviewed businesses
   - `prior_cities`: set of cities from all prior reviewed businesses
   - `prior_avg_stars`: mean of star ratings from all prior reviews
   - `prior_review_length_mean`: mean `text_word_count` from all prior reviews
   - `prior_unique_business_count`: distinct businesses in all prior reviews
   - `prior_primary_category_entropy`: Shannon entropy of category distribution in prior reviews
3. **Same-day ambiguity:** If a user reviews 3 businesses on the same day, all three are included in the aggregate. No within-day ordering is introduced. Same-day reviews are a batch — they all contribute equally to the aggregate.
4. For K=0 users, **all warm-up features are NULL**. The `feature_coverage` table must report this explicitly.

**Implementation note:** This stage cannot reuse Track A's `build_user_history()` which computes cumulative day-grain running aggregates. D2 warm-up needs a simpler pattern: filter all reviews/tips before `as_of_date`, aggregate. The day-grain window from Track A is for computing history at *each review date*; D2 needs history at a *single evaluation point*.

Risk: High — must correctly handle the boundary between K=0 (all NULL) and K>0 (aggregated priors).

### Stage 7 — Evaluation Cohorts (`evaluation_cohorts.py`)

```bash
python -m src.eda.track_d.evaluation_cohorts --config configs/track_d.yaml
```

**Inputs:**
- `outputs/tables/track_d_s2_business_cold_start_cohort.parquet` (Stage 2)
- `outputs/tables/track_d_s4_popularity_baseline_asof.parquet` (Stage 4)
- `outputs/tables/track_d_s5_user_cold_start_cohort.parquet` (Stage 5)
- `outputs/tables/track_d_s6_user_warmup_profile.parquet` (Stage 6)
- Track A splits via `load_splits_strict()`
- `data/curated/review_fact.parquet`
- `configs/track_d.yaml` — `baseline.candidate_set_max_size`, `evaluation.entity_cap_per_group` (default 10,000), `evaluation.recall_k`, `evaluation.ndcg_k`

**Outputs:**
- `outputs/tables/track_d_s7_eval_cohorts.parquet`
- `outputs/tables/track_d_s7_eval_cohort_summary.parquet`
- `outputs/tables/track_d_s7_eval_candidate_members.parquet`

**Key logic:**

**Implementation approach (bounded construction):** D1 and D2 no longer use spill-heavy DuckDB joins. Candidate sets are built from already-materialized Track D artifacts via pandas operations. `evaluation.entity_cap_per_group` (default 10,000) caps entities per group so Stage 7 stays reproducible and tractable on the Yelp dataset instead of materializing unbounded candidate pools. Candidate sets remain deterministic.

**D1 evaluation:**
1. Identify businesses that were cold as of T1 (or T2) and received at least one review in the subsequent test period (between T1 and T2, or after T2).
2. Define candidate set: businesses in the same city/category, limited to `candidate_set_max_size`, with entity cap applied.
3. Ground truth: which candidates did a user actually review in the test period.

**D2 evaluation:**
1. Identify users that were cold as of T1 (or T2). D2 evaluates the primary cold cohort only.
2. Define candidate set: businesses in cities/categories the user has previously interacted with, limited to `candidate_set_max_size`, with entity cap applied.
3. Ground truth: which business the user actually reviewed next (after the evaluation point).

**CRITICAL:** Candidate sets must exclude businesses the user has already reviewed before the recommendation point (evaluation contamination).

**Materialized outputs:**
- `track_d_s7_eval_cohorts.parquet`: `subtrack` (D1/D2), `entity_id`, `as_of_date`, `cohort_label`, `candidate_set_size`, `has_label`.
- `track_d_s7_eval_candidate_members.parquet`: `subtrack`, `entity_id`, `as_of_date`, `candidate_set_id`, `candidate_business_id`, `is_label`. This ensures candidate universes are reproducible.
- `track_d_s7_eval_cohort_summary.parquet`: aggregate statistics by subtrack and cohort.

Risk: High — most complex stage. Requires correct temporal filtering across multiple tables.

### Stage 8 — Leakage Check (`leakage_check.py`) — HARD GATE

```bash
python -m src.eda.track_d.leakage_check --config configs/track_d.yaml
```

**Inputs:**
- All Stage 2–7 output parquet files
- `src/eda/track_d/` source files (for code-path scan)
- `configs/track_d.yaml` — `leakage.banned_fields`, `leakage.hard_gate`

**Outputs:**
- `outputs/tables/track_d_s8_leakage_report.parquet`
- `outputs/logs/track_d_s8_leakage_check.log`

**Key logic — FOLLOWS TRACK B HARD-GATE PATTERN (Finding F6):**

**Code-path scan:**
- Scan all `.py` files in `src/eda/track_d/` for banned fields from config: `business.stars`, `business.review_count`, `business.is_open`, `user.average_stars`, `user.review_count`, `user.fans`, `user.elite`.
- Scan for raw entity joins that bypass curated tables (e.g., direct reads of `yelp_academic_dataset_*.json`).

**Output artifact scan:**
- Describe all `track_d_*.parquet` files in `outputs/tables/`. Flag any column named `stars` (ambiguous with snapshot `business.stars`), `review_count` (ambiguous with snapshot value), `average_stars`, `fans`, `elite`, `is_open`.
- Flag any column named `text`, `review_text`, or `raw_text`.
- Check that cohort tables contain only as-of values (column names should include `prior_` or `asof_` prefixes for computed fields).

**Temporal integrity checks:**
- For D1 cohort table: verify no business has `prior_review_count` greater than its total review count before `as_of_date` (computed independently).
- For D2 cohort table: verify no user has `prior_review_count` greater than their total count before `as_of_date`.
- For evaluation cohorts: verify no candidate set includes businesses the user reviewed before the evaluation point.

**BLOCKING BEHAVIOR (matches `src/eda/track_b/leakage_scope_check.py` line 337):**

```python
failures = report_df.loc[report_df["status"] == "FAIL"]
if not failures.empty:
    failure_names = ", ".join(sorted(failures["finding_name"].tolist()))
    raise RuntimeError(
        f"Track D leakage check FAILED on: {failure_names}. "
        f"Fix upstream stages before proceeding to summary."
    )
```

The `RuntimeError` causes a non-zero exit code. The dispatcher catches this at line 930 (`if exit_code != 0`) and marks the stage as failed, halting the pipeline before the summary report.

**Rationale for hard gate (not soft audit):** Track D has severe leakage risk — lifetime aggregates silently contaminating features would invalidate all downstream modeling. Track A's soft audit (exit 0, `leakage_audit.py:265–291`) is insufficient here because Track D's cold-start premise requires absolute certainty that no future information leaks into cohort definitions or feature construction. Track B's hard-gate pattern (`leakage_scope_check.py:334–337`) is the correct model.

Risk: Low (the check itself). May block pipeline completion if upstream stages have bugs — by design.

### Stage 9 — Summary Report (`summary_report.py`)

```bash
python -m src.eda.track_d.summary_report --config configs/track_d.yaml
```

**Inputs:** All prior stage outputs (S1–S8 tables, figures, and logs)

**Outputs:**
- `outputs/tables/track_d_s9_eda_summary.md`

**Key logic:**

1. Read all stage output tables.
2. Generate consolidated markdown with **SEPARATE D1 and D2 sections**:
   - Cohort definitions and sizes
   - Feature coverage tables (with explicit NULL rates for zero-history cohorts)
   - Baseline strength assessment
   - Evaluation cohort sizes and hit rates
   - Leakage audit results (PASS/FAIL summary)
   - Modeling feasibility assessment for each subtrack
3. Include hypothesis assessment table (H1–H6 with findings and evidence references).
4. Reference figure filenames (not embedded).
5. Document locked decisions: D2 interaction basis (reviews + tips), same-day batch policy, day-level tip granularity.

Risk: Low.

---

## Part 4: Verification, Testing, and Implementation Order

### 4.1 Dispatcher Registration

**File:** `scripts/pipeline_dispatcher.py`

Add two new approaches:

```python
APPROACH_TRACK_C = "track_c"
APPROACH_TRACK_D = "track_d"
APPROACH_CHOICES = (
    APPROACH_SHARED, APPROACH_TRACK_A, APPROACH_TRACK_B,
    APPROACH_TRACK_C, APPROACH_TRACK_D,
)
```

Register Track C and Track D stage definitions in the `PIPELINES` dict, following the existing pattern for Track A and Track B. Each stage must have its `required_outputs` tuple matching the outputs listed in §2 and §3 above.

**Track D prerequisite:** The dispatcher must verify that `outputs/tables/track_a_s5_candidate_splits.parquet` exists before Track D Stage 2 begins. This can be implemented as a prerequisite check in `maybe_run_shared_prerequisites()` or as an explicit entry in the Track D pipeline definition.

**CLI usage:**

```bash
# Run Track C
python scripts/run_pipeline.py --approach track_c

# Run Track D (requires Track A Stage 5 to have completed)
python scripts/run_pipeline.py --approach track_d
```

### 4.2 CLAUDE.md Files to Create

| File | id | Purpose |
|---|---|---|
| `src/eda/track_c/CLAUDE.md` | `src_eda_track_c` | Track C EDA implementation context |
| `src/eda/track_d/CLAUDE.md` | `src_eda_track_d` | Track D EDA implementation context |

These must follow the pattern of `src/eda/track_a/CLAUDE.md` and `src/eda/track_b/CLAUDE.md`, documenting: stage module map, critical rules (text contract for Track C, banned fields for Track D), CLI usage, and dependencies.

Update the root `CLAUDE.md` to add these to the "All CLAUDE.md Files" table and the "Context Loading Guide."

### 4.3 Test Plan

**Unit tests (new files in `tests/`):**

| Test File | What It Tests | Priority |
|---|---|---|
| `test_text_semijoin_contract.py` | Verify Track C NLP stages never persist raw text columns in any output parquet | P0 |
| `test_checkin_expansion.py` | Verify `checkin_expanded.parquet` schema and row expansion correctness | P0 |
| `test_track_d_splits_strict.py` | Verify `load_splits_strict()` raises RuntimeError when artifact is missing and config has `require_stage5_artifact: true` | P0 |
| `test_d1_cohort_temporal.py` | Verify D1 cohort `prior_review_count` is strictly as-of (no future reviews counted) | P0 |
| `test_d2_interaction_count.py` | Verify D2 `prior_total_interaction_count` sums reviews + tips with strict earlier-date semantics | P1 |
| `test_d2_warmup_features.py` | Verify D2 warm-up features are NULL for K=0 users and correct aggregates for K>0 | P1 |
| `test_track_d_leakage_gate.py` | Verify Stage 8 raises RuntimeError on FAIL findings | P0 |
| `test_eval_candidate_exclusion.py` | Verify evaluation candidate sets exclude businesses already interacted with | P1 |

**Integration tests:**

- Run Track C pipeline end-to-end on a small fixture dataset (100 reviews, 10 businesses, 5 cities). Verify all `required_outputs` exist after successful completion.
- Run Track D pipeline end-to-end on the same fixture. Verify all `required_outputs` exist.
- Run Track D with Stage 5 artifact deliberately missing. Verify hard failure with clear error message.

**Regression contract tests:**

- No `text` column in any `track_c_*.parquet` or `track_d_*.parquet` output.
- No `business.stars` or `business.review_count` values in any `track_d_*.parquet` column.
- D1 and D2 are always reported separately (separate rows with `subtrack` column) in every Track D output table.

### 4.4 Risks and Mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Raw text leaks into Track C parquet outputs | High | Mandatory semijoin pattern + `test_text_semijoin_contract.py` + Stage 9 scan |
| Track D silently uses placeholder splits | High | `load_splits_strict()` wrapper raises on config fallback |
| D1 zero-interaction cohort has no usable features | Medium | Explicitly documented: only static metadata available. Feature coverage table shows NULL rates. |
| `checkin_expanded.parquet` parsing fails on malformed timestamps | Medium | Add error handling in expansion SQL (TRIM + TRY_CAST), log dropped rows |
| Track D Stage 8 hard gate blocks summary report | Low | By design. Fix upstream leakage first. Pipeline cannot produce a clean summary with active leakage. |
| Sentiment proxy does not correlate with stars | Low | Quality check threshold in config. Log warning but do not block. |
| City-level aggregation too coarse for Track C | Low | Document limitation. lat/lon available for future micro-geography if needed. |
| TextBlob/langdetect add ~200MB transitive dependencies | Low | Both are already in or compatible with the existing dependency contract. Pin versions in `requirements.txt`. |

### 4.5 Implementation Order

The recommended implementation sequence, considering dependencies:

| Phase | Scope | Risk | Depends On |
|---|---|---|---|
| **Phase 0** | Shared changes: dispatcher registration, `checkin_expanded.parquet`, `load_splits_strict()`, config files, `requirements.txt` | Low | Nothing |
| **Phase 1** | Track C S1–S2: geographic coverage + temporal binning | Low | Phase 0 |
| **Phase 2** | Track C S3–S5: text normalization + sentiment + topic prevalence | **High** | Phase 1 |
| **Phase 3** | Track C S6–S9: drift + events + checkin + summary | Low | Phase 2 |
| **Phase 4** | Track D S1–S2: business lifecycle + D1 cohorts | Medium | Phase 0 + Track A S5 |
| **Phase 5** | Track D S3–S4: D1 early signals + popularity baselines | **High** | Phase 4 |
| **Phase 6** | Track D S5–S6: D2 cohorts + warm-up profiles | **High** | Phase 4 |
| **Phase 7** | Track D S7–S9: evaluation cohorts + leakage check + summary | **High** | Phase 5 + Phase 6 |

Track C and Track D have no inter-track dependencies, so Phases 1–3 and Phases 4–7 can proceed in parallel.

### 4.6 Success Criteria

- [ ] All 9 Track C stages produce their declared outputs without error
- [ ] All 9 Track D stages produce their declared outputs without error
- [ ] No raw review text appears in any `track_c_*.parquet` or `track_d_*.parquet` output file
- [ ] Track D leakage check (Stage 8) passes with zero FAIL findings
- [ ] Track C sentiment proxy correlates with star ratings (Spearman > 0.3)
- [ ] Track D has non-trivial D1 cohort (≥ 500 businesses) and D2 cohort (≥ 1,000 users)
- [ ] `checkin_expanded.parquet` is verified by the dispatcher
- [ ] `tip.parquet`, `checkin.parquet`, `user.parquet` are verified by the dispatcher
- [ ] Track D does not consume placeholder split dates (`load_splits_strict()` enforced)
- [ ] D1 and D2 are reported separately in every Track D output table and summary
- [ ] All new CLAUDE.md files are created and registered in root CLAUDE.md
- [ ] All new tests pass with `pytest tests/`
- [ ] Track C uses city (not neighborhood) as its primary geographic unit
- [ ] Track D Stage 8 returns non-zero on any FAIL, matching Track B's blocking pattern

### 4.7 Locked Decisions

These decisions are resolved in this document and must not be revisited without a new adversarial review:

| Decision | Resolution | Rationale |
|---|---|---|
| D2 interaction threshold basis | `prior_review_count + prior_tip_count` | Tips are a meaningful cold-start signal; checkins are too noisy |
| Same-day review policy | Batch — all same-day reviews count, no within-day ordering | Dataset provides dates not timestamps; synthetic ordering would be fabricated |
| Tip granularity | Day-level aggregates only | Consistent with same-day review policy |
| Track D leakage gate | Hard gate (raise on FAIL) | Cold-start premise requires zero leakage tolerance |
| D1 warm-up features | As-of aggregates, not event-sequence "first K" | Day-grain only; event-sequence extraction requires unsafe synthetic ordering |
| Track C geography | City + state only; neighborhood deferred | Ingestion does not load neighborhood field |
| `is_open` semantics | Snapshot context, not temporal event | No close-date timestamp available; proxy only |
| Text access pattern | Semijoin to `review.parquet`, drop text before write | Matches Track A `text_profile.py` established pattern |

---

## Appendix: Key Source File References

| File | Relevant Content | Lines |
|---|---|---|
| `src/curate/build_review_fact.py` | Text stripped to char/word count only; `ENTITY_TABLES` loop writes tip/checkin/etc. | 22–46, 60, 245–248 |
| `src/ingest/load_yelp_json.py` | Business schema — no `neighborhood` field | 26–41 |
| `scripts/pipeline_dispatcher.py` | Shared `required_outputs` (incomplete); execution logic (exit code check) | 150–156, 927–955 |
| `src/common/artifacts.py` | `load_candidate_splits()` with silent fallback to config | 14–68 |
| `src/eda/track_a/text_profile.py` | Established NLP semijoin pattern | 70–123 |
| `src/eda/track_a/user_history_profile.py` | Day-grain as-of history logic (`ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING`) | 29–55 |
| `src/eda/track_a/leakage_audit.py` | Soft audit — exits 0 always | 265–291 |
| `src/eda/track_b/leakage_scope_check.py` | Hard gate — raises RuntimeError on FAIL | 334–337 |
| `configs/track_a.yaml` | Placeholder split dates | 8–11 |
