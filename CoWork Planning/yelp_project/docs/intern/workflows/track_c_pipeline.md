# Track C Pipeline: Sentiment and Topic Drift

> **Last updated:** 2026-03-13
> **Related commit:** Add Track C EDA pipeline and shared text-safety contract
> **Difficulty level:** Beginner

## What You Need to Know First

- Read `../GLOSSARY.md` for **semijoin**, **drift detection**, and **soft audit**.
- Read `track_a_pipeline.md` if you have not seen how the shared dispatcher runs stage-based pipelines.

## The Big Picture

Track C asks a simple question: does review language change over time in different cities?

This matters because a model built on review text can become stale. If people start talking about different things, the old features may stop being useful.

## How It Works (Step by Step)

### Step 1: Measure which cities are big enough to study

The pipeline counts reviews and businesses by city.

This matters because you should not trust a “trend” built from a tiny sample. A city with 20 reviews is too noisy.

### Step 2: Put reviews into time bins

The pipeline groups reviews by month and quarter.

Think of this like turning a long diary into a calendar. You need regular time buckets before you can see trends.

### Step 3: Inspect text quality safely

Track C reads raw text from `data/curated/review.parquet`.

It does **not** read text from `review_fact.parquet`, because that curated table intentionally removed raw text. Instead, it semijoins review IDs from `review_fact.parquet` to keep the analysis inside the approved review scope.

### Step 4: Turn text into sentiment numbers

The pipeline computes one sentiment score per sampled review, then immediately aggregates to city-by-month summaries.

This matters because the project is allowed to use derived signals like “average sentiment in Phoenix during 2020-03,” but it is not allowed to store raw review text in output artifacts.

### Step 5: Track keyword and topic frequency

The pipeline counts configured keywords such as `delivery`, `service`, and `price`.

This is a lightweight way to measure topic drift without training a heavy topic model first.

### Step 6: Flag drift periods

Track C fits simple trend lines over time and marks cities or keywords that move meaningfully.

This is EDA, not a final causal claim. It tells you where to look next.

### Step 7: Compare language drift with business lifecycle events

The pipeline builds event proxies such as first observed review and likely closure candidates.

It uses `is_open` only as snapshot context. It does **not** pretend Yelp gives an exact closure timestamp.

### Step 8: Compare drift with check-in activity

Track C uses the new shared `checkin_expanded.parquet` artifact when it exists.

That file turns one comma-separated check-in string into many clean dates, which makes time-based analysis much easier.

### Step 9: Write one summary and run a text leak scan

The final stage writes `track_c_s9_eda_summary.md`.

It also scans Track C parquet files for columns like `text`, `review_text`, or `raw_text`. This is a **soft audit**: it reports problems, but it does not stop the run.

## Key Concepts Explained

### City-Level Aggregation
**What it is:** Combining many rows into one city summary.
**Why we use it:** The ingest schema does not have a reliable `neighborhood` field, so city is the safest geography level today.
**Analogy:** Instead of studying one person’s mood, you study the average mood of a whole class.

### Semijoin Text Contract
**What it is:** Read text from the raw text table, but only for IDs approved by the curated table.
**Why we use it:** It keeps Track C inside the same analysis scope as the rest of the project while still allowing text processing.

## Code Walkthrough

The Track C code lives in `src/eda/track_c/`.

- `common.py` holds the safety rules and helper functions.
- `text_normalization.py`, `sentiment_baseline.py`, and `topic_prevalence.py` are the only stages that touch raw text.
- `summary_report.py` is where the pipeline explains its own findings and checks for text-column leaks.

## Common Questions

**Q: Why not just store per-review sentiment scores?**
A: Because Track C is meant to publish aggregate analysis, not review-level text artifacts. Aggregate tables are safer and easier to explain.

**Q: Why is the geography city-level instead of neighborhood-level?**
A: The current ingest schema does not materialize a neighborhood field, so neighborhood analysis would be guessed instead of measured.

## What Could Go Wrong

- If a stage writes a `text` column to parquet, the summary audit will flag it.
- If `langdetect` is missing, language profiling becomes weaker.
- If monthly bins are too small, apparent “drift” may just be random noise.

## Try It Yourself

Run the whole Track C pipeline through the dispatcher:

```bash
python scripts/run_pipeline.py --approach track_c
```

Run one stage directly:

```bash
python -m src.eda.track_c.sentiment_baseline --config configs/track_c.yaml
```

Expected result:

- New tables appear in `outputs/tables/track_c_*`
- New figures appear in `outputs/figures/track_c_*`
- The final markdown summary appears at `outputs/tables/track_c_s9_eda_summary.md`
