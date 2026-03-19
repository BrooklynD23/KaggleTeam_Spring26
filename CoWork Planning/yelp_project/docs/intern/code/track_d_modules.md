# Track D Code: What the New Modules Do

> **Last updated:** 2026-03-13
> **Related commit:** Add Track D cohort, evaluation, and leakage-check modules
> **Difficulty level:** Beginner

## What You Need to Know First

- Read `../workflows/track_d_pipeline.md` first.
- Read `../GLOSSARY.md` for **cold start**, **candidate set**, and **hard gate**.

## The Big Picture

Track D is harder than it first looks because “new user” and “new business” are not the same problem.

The new code keeps those paths separate so an intern can follow the logic without mixing two different recommendation tasks together.

## How It Works (Step by Step)

### Step 1: `common.py`

This file is Track D’s shared toolbox.

It resolves paths, loads Track A split dates, parses business attributes, assigns cohort labels, and computes feature-coverage tables.

### Step 2 (Stage 1): `business_lifecycle.py`

This is a descriptive stage.

It measures how businesses grow over time, but it does not define the real D1 cohorts. That separation is important because lifetime growth is not safe to use as an as-of feature.

### Step 3 (Stage 2): `business_cold_start.py`

This stage computes D1 cohorts directly from reviews before each `as_of_date`.

That means “newness” is based on history that truly existed at the time.

### Step 4 (Stage 3): `business_early_signals.py`

This stage creates D1 features.

It mixes:

- static business information like city and categories
- safe as-of aggregates like prior review mean stars

For zero-history businesses, interaction-based fields stay `NULL`.

### Step 5 (Stage 4): `popularity_baseline.py`

This stage builds the baseline that Track D wants to beat later.

It is useful because you should not celebrate a future recommender unless it beats a reasonable “most popular so far” rule.

### Step 6 (Stage 5): `user_cold_start.py`

This stage builds D2 cohorts from prior reviews and tips.

It counts only interactions that happened before the evaluation date.

### Step 7 (Stage 6): `user_warmup_profile.py`

This stage summarizes what a user has already shown about their tastes.

It uses aggregates like prior average stars and prior category mix, which are much safer than pretending we know a perfect click-by-click order inside one day.

### Step 8 (Stage 7): `evaluation_cohorts.py`

This stage materializes the candidate sets and label businesses.

It uses a bounded, deterministic construction path: D1 and D2 candidate sets are built from already-materialized Track D artifacts (cohorts, baselines, warm-up profiles) via pandas operations, not spill-heavy DuckDB joins. The config option `evaluation.entity_cap_per_group` caps entities per group for reproducibility. D2 evaluates the primary cold cohort only.

It also removes businesses that were already seen before the recommendation point.

### Step 9 (Stages 8–9): `leakage_check.py` and `summary_report.py`

`leakage_check.py` (Stage 8) is the blocker. `summary_report.py` (Stage 9) is the explainer.

The order matters. The pipeline only writes a clean summary after the hard gate says the artifacts are safe enough to trust.

## Key Concepts Explained

### As-Of Cohort
**What it is:** A group defined using only information available at one evaluation date.
**Why we use it:** Recommendation needs to feel like a real-time decision, not a hindsight report.

## What Could Go Wrong

- If you use lifetime `business.review_count`, the D1 task becomes unrealistic.
- If `evaluation_cohorts.py` forgets to exclude already seen businesses, the measured candidate set quality becomes misleading.
- If you disable the hard gate casually, you may write polished summaries for invalid data.

## Try It Yourself

Read the leakage stage:

```bash
sed -n '1,240p' src/eda/track_d/leakage_check.py
```

Run one stage:

```bash
python -m src.eda.track_d.business_cold_start --config configs/track_d.yaml
```
