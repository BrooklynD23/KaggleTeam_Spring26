# Config: `configs/track_d.yaml`

> **Last updated:** 2026-03-13
> **Related commit:** Add Track D configuration
> **Difficulty level:** Beginner

## What You Need to Know First

- Read `../workflows/track_d_pipeline.md` first.

## The Big Picture

`configs/track_d.yaml` tells the cold-start pipeline how strict to be.

That matters because Track D is mostly about defining the task correctly, not just writing code that runs.

## How It Works (Step by Step)

### `splits`

- `t1` and `t2`: placeholder dates
- `require_stage5_artifact`: whether Track D is allowed to fall back to placeholders

Why this matters: with the new strict loader, Track D should normally refuse to use placeholders.

### `cold_start.d1_thresholds`

These numbers define the business cohort labels:

- `zero_history`
- `sparse_history`
- `emerging`

Why this matters: interns need one shared language for “how cold is this business?”

### `cold_start.d2_k_values`

These settings define which user-history sizes matter.

Examples:

- `0` = truly new user
- `1` = just one prior interaction
- `3` = early warm-up

### `interaction`

These settings explain how reviews and tips are counted.

Why this matters: same-day ambiguity can create fake precision if you are not careful.

### `baseline`

- `min_support_reviews`: minimum support for rating-based baselines
- `candidate_set_max_size`: cap for candidate-set size

Why this matters: a baseline should be realistic, not overfit or unreasonably huge.

### `evaluation`

- `recall_k`
- `ndcg_k`
- `entity_cap_per_group` (default: 10,000) — caps the number of entities processed per group in Stage 7 so candidate construction stays tractable and reproducible on the Yelp dataset. Prevents unbounded candidate pools that would cause memory spills.

Why this matters: these are the report-card cutoffs for future recommendation experiments. The entity cap keeps Stage 7 bounded and deterministic.

### `leakage`

- `banned_fields`: snapshot or lifetime fields Track D must not use
- `hard_gate`: whether failures should stop the pipeline

Why this matters: this is the line between a trustworthy cold-start experiment and a fake one.

### `quality`

- minimum D1 cohort size
- minimum D2 cohort size
- minimum feature coverage

Why this matters: a clever pipeline is not useful if the resulting cohort is too small to study.

## Common Questions

**Q: Why keep placeholder dates in the config if strict mode blocks them?**
A: They are still useful as readable defaults and documentation, but the strict loader stops them from being used by mistake in Track D.

## Try It Yourself

```bash
python -m src.eda.track_d.user_cold_start --config configs/track_d.yaml
```
