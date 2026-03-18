# Track C Code: What the New Modules Do

> **Last updated:** 2026-03-13
> **Related commit:** Add Track C stage modules and text-safety helpers
> **Difficulty level:** Beginner

## What You Need to Know First

- Read `../workflows/track_c_pipeline.md` first.
- Read `../GLOSSARY.md` for **semijoin** and **soft audit**.

## The Big Picture

Track C is split into small stage modules because each stage answers one question.

That makes the pipeline easier to debug. If Stage 5 breaks, you do not have to mentally untangle the whole project.

## How It Works (Step by Step)

### Step 1: `common.py`

This file is the safety belt for Track C.

It holds the helper that reads review text through a semijoin, the helper that drops banned raw-text columns, and the helper that scans Track C parquet files for leaks.

### Step 2: `geo_coverage.py` and `temporal_binning.py`

These are the “shape of the data” stages.

They answer:

- Which cities have enough reviews?
- Which months and quarters are dense enough to study?

### Step 3: `text_normalization.py`

This stage does not build a final NLP feature table.

It checks whether the raw review text is clean enough to trust. It measures language mix, text length, and a few basic text-quality signals.

### Step 4: `sentiment_baseline.py`

This stage turns text into a numeric sentiment score, then aggregates by city and month.

It also compares sentiment to star ratings. That comparison is a sanity check. If sentiment does not line up with stars at all, you should be skeptical.

### Step 5: `topic_prevalence.py`

This stage counts keywords over time.

It gives you a simple way to see whether topics are becoming more or less common without immediately jumping into a heavy model.

### Step 6: `drift_detection.py`

This stage looks at the stage-4 and stage-5 outputs and asks whether any trends are statistically notable.

### Step 7: `event_candidates.py`

This stage builds business lifecycle summaries and compares them with drift periods.

It is careful to treat `is_open` as a snapshot flag, not as a true event timestamp.

### Step 8: `checkin_correlation.py`

This stage brings in the new expanded check-in artifact.

It asks whether city-level check-in activity moves with sentiment.

### Step 9: `summary_report.py`

This is the explanation stage.

It writes one markdown summary and runs a final schema scan for banned text columns.

## Key Concepts Explained

### Aggregate-Only Output
**What it is:** Saving city-level or time-bin-level summaries instead of review-by-review outputs.
**Why we use it:** It keeps the artifacts smaller, safer, and easier for interns to reason about.

## What Could Go Wrong

- If you skip `drop_raw_text_columns()`, Track C can leak review text into parquet files.
- If you change `common.py` carelessly, you can break multiple stages at once because they all reuse it.

## Try It Yourself

Read one module directly:

```bash
sed -n '1,220p' src/eda/track_c/common.py
```

Run one stage:

```bash
python -m src.eda.track_c.topic_prevalence --config configs/track_c.yaml
```
