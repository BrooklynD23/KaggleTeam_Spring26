# Track D Pipeline: Cold-Start Recommender EDA

> **Last updated:** 2026-03-13
> **Related commit:** Add Track D cold-start pipeline, strict split loading, and leakage hard gate
> **Difficulty level:** Beginner

## What You Need to Know First

- Read `../GLOSSARY.md` for **cold start**, **candidate set**, **hard gate**, and **as-of feature**.
- Read `track_a_pipeline.md` first, because Track D depends on Track A Stage 5 split artifacts.

## The Big Picture

Track D is about recommendation under uncertainty.

There are really two separate problems:

- **D1:** recommend businesses when the business is new and has very little history.
- **D2:** recommend businesses when the user is new and has very little history.

These are easy to mix up. The new Track D code keeps them separate on purpose.

## How It Works (Step by Step)

### Step 1: Describe business lifecycle

The pipeline measures how quickly businesses get their 3rd, 5th, and 10th reviews.

This is descriptive only. It helps you understand the dataset, but it is **not** allowed to define later “newness” using lifetime totals.

### Step 2: Build D1 business cold-start cohorts

Track D loads Track A’s split dates with a strict helper.

If the Stage 5 split file is missing, Track D fails early instead of quietly using placeholder dates. That prevents an intern from accidentally running a fake evaluation.

### Step 3: Build D1 early-signal features

For a new business, the safest features are static things like city, category, hours, and parsed attributes.

If a business has zero prior interactions, Track D leaves interaction-based features as `NULL`. That is intentional. You cannot invent history that does not exist.

### Step 4: Build popularity baselines

Track D computes rankings like “most reviewed in this city as of date X.”

The important phrase is **as of**. It only counts reviews that happened before the recommendation time.

### Step 5: Build D2 user cold-start cohorts

This stage counts earlier reviews and tips for each user.

The project treats same-day activity as one batch. That means it does not fake a minute-by-minute order inside one day.

### Step 6: Build D2 warm-up profiles

For users with some history, Track D summarizes what they have already done.

Examples include:

- average prior stars
- set of prior cities
- set of prior categories
- number of unique businesses already visited

### Step 7: Build evaluation cohorts

This stage creates candidate sets and marks which business became the real next interaction.

It uses a bounded, deterministic construction path: candidate sets are built from already-materialized Track D artifacts (cohorts, baselines, warm-up profiles) rather than spill-heavy DuckDB joins. The config option `evaluation.entity_cap_per_group` (default 10,000) caps entities per group so Stage 7 stays tractable on the Yelp dataset. D2 evaluates the primary cold cohort only.

It also removes businesses the user already saw before the evaluation point. That avoids recommending something the user already knows.

### Step 8: Run the leakage hard gate

This is the most important safety stage in Track D.

It scans Track D outputs and Track D source files for banned lifetime fields and unsafe output columns. If it finds a failure, it raises an error and blocks the summary stage.

### Step 9: Write the final summary

The summary explains D1 and D2 separately.

That separation matters because business cold start and user cold start need different reasoning, different features, and different expectations.

## Key Concepts Explained

### Strict Split Loading
**What it is:** Refusing to run when the real split artifact is missing.
**Why we use it:** Placeholder dates are convenient for configs, but dangerous for evaluation. Track D needs the real Track A split output.

### Leakage Hard Gate
**What it is:** A blocking check that raises an error on unsafe fields.
**Why we use it:** Cold-start recommendation is very easy to fake by accidentally using lifetime popularity fields.
**Analogy:** It is like a lab safety door that locks the machine if the sensor sees a dangerous condition.

## Code Walkthrough

The Track D code lives in `src/eda/track_d/`.

- `common.py` handles path resolution, split loading, category parsing, and cohort-label helpers.
- `business_cold_start.py` and `user_cold_start.py` build the D1 and D2 cohorts.
- `evaluation_cohorts.py` materializes candidate sets and label membership.
- `leakage_check.py` is the blocking safety layer.

## Common Questions

**Q: Why does Track D care so much about “prior” values?**
A: Because recommendation must use only the information available at the recommendation time. Future counts would make the task unrealistically easy.

**Q: Why can zero-history rows have many `NULL` values?**
A: Because that is the honest state of the data. If the user or business has no prior interactions, there is no interaction summary to compute.

## Track D and Track A: No Impact on Track A

**The Track D Stage 7 fix does not change the Track A process in any way.**

- **Dependency direction:** Track D → Track A. Track D *reads* Track A Stage 5 split artifact (`track_a_s5_candidate_splits.parquet`) for temporal boundaries. Track A does not read any Track D outputs.
- **Shared data:** Both tracks read `data/curated/review_fact.parquet`. Track A writes only `track_a_*` artifacts; Track D writes only `track_d_*` artifacts.
- **Conclusion:** You can run Track A exactly as before. Track D changes (bounded Stage 7 construction, `entity_cap_per_group`) affect only Track D outputs. Track A’s process, outputs, and constraints are unchanged.

## What Could Go Wrong

- If Track A Stage 5 was not run, Track D will stop before cohorting.
- If a Track D output contains banned columns like `is_open` or `average_stars`, the leakage stage will block the run.
- If candidate sets keep previously seen businesses, evaluation becomes contaminated.

## Try It Yourself

Run Track A to create real split dates first:

```bash
python scripts/run_pipeline.py --approach track_a --from-stage split_selection
```

Then run Track D:

```bash
python scripts/run_pipeline.py --approach track_d
```

Run the leakage stage alone:

```bash
python -m src.eda.track_d.leakage_check --config configs/track_d.yaml
```

Expected result:

- `outputs/tables/track_d_s7_eval_cohorts.parquet` and related artifacts appear
- `outputs/tables/track_d_s8_leakage_report.parquet` is written
- If the report contains any `FAIL` rows, the stage exits non-zero on purpose
