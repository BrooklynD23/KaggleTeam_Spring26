# Track D — Agent Configuration: Cold-Start Recommender

## Agent Purpose

This agent implements the EDA pipeline for **Track D: separate D1 business-cold-start and D2 user-cold-start recommendation tasks**. It is a cohort definition and feature availability agent — it does not build recommender models.

## Context

You are working on a semester-scale data science project using the **Yelp Open Dataset**. Track D asks: *Can separate business-cold-start and user-cold-start recommenders outperform explicit as-of popularity baselines?*

Your job is to execute the EDA pipeline defined in `05_EDA_Pipeline_Track_D_Cold_Start_Recommender.md`. Read that file first.

## Agent Responsibilities

1. **Profile** business lifecycle and user activity ramp-up.
2. **Define** D1 business-cold-start cohorts using only as-of information.
3. **Define** D2 user-cold-start cohorts separately, including the first-K-interaction warm-up option.
4. **Catalog** early-stage signals for D1 and D2 separately.
5. **Construct** explicit as-of popularity baselines for each subtrack.
6. **Build** temporally valid D1 and D2 evaluation cohorts for future modeling.

## Key Constraints

- "Newness" must be defined **temporally** and from information available at `as_of_date`, never from lifetime totals or future windows.
- Do NOT use lifetime `business.stars`, lifetime `business.review_count`, lifetime `user.review_count`, or post-hoc outcome fields as features.
- Only use features that truly exist at cold-start time. A 10th review is not available when the business has 2 reviews.
- Depends on Track A's temporal splits (T₁, T₂) — coordinate via `configs/base.yaml`.
- Outputs are aggregate-only. No raw review text.
- D1 and D2 must stay separate in cohorts, metrics, and summary outputs.
- CLI-first: `python -m src.eda.track_d.<stage> --config configs/track_d.yaml`.

## Data Entities Needed

- `review` — dating and rating of business interactions
- `business` — attributes, categories, location
- `user` — yelping_since, elite/fans if explicitly justified
- `checkin` — first check-in timing
- `tip` — first tip timing

## Completion Signal

EDA is done when `outputs/tables/track_d_s9_eda_summary.md` exists and all exit criteria are met.
