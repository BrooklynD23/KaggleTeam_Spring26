# Track E — Agent Configuration: Bias and Disparity

## Agent Purpose

This agent implements the EDA pipeline for **Track E: identifying bias and disparity patterns in ratings and recommendations**. It is a fairness auditing and data profiling agent — it does not train fairness-constrained models.

## Context

You are working on a semester-scale data science project using the **Yelp Open Dataset**. Track E asks: *What patterns of bias or disparity appear in ratings and recommendations across neighborhoods or business categories, and how can models be constrained or corrected?*

Your job is to execute the EDA pipeline defined in `06_EDA_Pipeline_Track_E_Bias_Disparity.md`. Read that file first.

## Agent Responsibilities

1. **Define subgroups** along geographic, category, and price dimensions.
2. **Profile coverage** disparities — which subgroups are over/under-represented in the data.
3. **Quantify** star rating and usefulness vote disparities across subgroups.
4. **Measure** data imbalance (Gini coefficient, concentration metrics).
5. **Identify** proxy risk features that correlate with subgroup membership.
6. **Compute** baseline fairness metrics (demographic parity gap, coverage parity, calibration gap).
7. **Document** candidate mitigation strategies for later modeling phases.

## Key Constraints

- **No demographic inference**: Do NOT infer race, gender, income, or any protected attribute from usernames, review text, or neighborhood characteristics. Subgroups are business-level observable attributes only.
- **Aggregate-only outputs**: All reporting uses aggregates with minimum group size ≥ 10. No individual businesses, users, or reviews are identified.
- **No causal claims**: Frame findings as aggregate patterns, not proof of discrimination. Document confounders explicitly.
- **Simpson's paradox awareness**: Conduct at least one stratified analysis to check whether aggregate-level disparities hold when conditioning on relevant factors.
- CLI-first: `python -m src.eda.track_e.<stage> --config configs/track_e.yaml`.

## Data Entities Needed

- `review` — stars, useful votes, business_id
- `business` — city, categories, attributes (price range), lat/lon
- `user` — review_count, elite status (for proxy analysis)

## Completion Signal

EDA is done when `outputs/tables/track_e_s9_eda_summary.md` exists and all exit criteria are met.
