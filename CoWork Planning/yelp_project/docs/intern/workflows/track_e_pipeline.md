# Track E Pipeline: Bias and Disparity Audit

> **Last updated:** 2026-03-17
> **Related commit:** Implement Track E fairness audit pipeline
> **Difficulty level:** Intermediate

## What You Need to Know First

- Read `CoWork Planning/yelp_project/track_e/06_EDA_Pipeline_Track_E_Bias_Disparity.md`.
- Read `src/eda/track_e/CLAUDE.md` for runtime rules and banned-column constraints.
- Remember that Track E is descriptive only. It does not train or evaluate a model.

## The Big Picture

Track E asks a simple question: before we train anything, what disparities already exist in the Yelp dataset?

The code stays intentionally aggregate-only. It uses business-facing subgroup definitions such as city, category, price tier, and review-volume tier. It does not infer protected traits, and it does not make causal claims.

## How It Works (Step by Step)

### Step 1: Define subgroups

`subgroup_definition.py` assigns each business exactly one value for:

- `city`
- `primary_category`
- `price_tier`
- `review_volume_tier`

It also writes subgroup summary tables and a price-tier coverage diagnostic.

### Step 2: Profile coverage

`coverage_profile.py` joins reviews to subgroup definitions and computes:

- business counts
- review counts
- user counts
- mean stars
- mean useful votes

This answers whether some subgroups are thinly represented before any fairness metric is computed.

### Step 3: Measure star disparities

`star_disparity.py` summarizes star distributions by subgroup and runs pairwise KS tests.

This is also where Track E performs the required Simpson's paradox check by conditioning city comparisons on `primary_category`.

### Step 4: Measure usefulness disparities

`usefulness_disparity.py` studies whether some subgroups receive fewer useful votes.

Subgroups with unusually high zero-useful rates are marked as visibility deserts.

### Step 5: Quantify imbalance

`imbalance_analysis.py` computes Gini coefficients and top/bottom share metrics for subgroup distributions.

This captures whether a small number of subgroup values dominate the dataset.

### Step 6: Check proxy risk

`proxy_risk.py` computes point-biserial correlations between candidate numeric features and subgroup indicators.

This stage reads `user.parquet` only for audit context. It does not use user data to define subgroups.

### Step 7: Build fairness baselines

`fairness_baseline.py` consolidates data-level fairness metrics such as:

- demographic parity gaps for stars
- demographic parity gaps for useful votes
- coverage parity ratios
- calibration gaps from KS statistics

These are baseline dataset diagnostics, not model fairness claims.

### Step 8: Write mitigation candidates

`mitigation_candidates.py` turns Stage 5-7 findings into a markdown brief.

The language stays conditional: if a downstream model reproduces or worsens observed disparities, these are the mitigations to consider.

### Step 9: Summarize and audit

`summary_report.py` builds the final markdown summary and runs a soft validity scan.

The validity scan checks for banned text columns, forbidden demographic column names, and count columns below the minimum group size.

## What Could Go Wrong

- A stage writes raw text or demographic-looking columns into parquet output.
- A stage skips min-group-size filtering and creates fragile subgroup rows.
- Someone reads Stage 7 metrics as model bias rather than dataset baseline disparity.
- The proxy scan is misread as evidence of protected attributes rather than correlation with subgroup membership.

## Try It Yourself

Run the full Track E pipeline:

```bash
python scripts/run_pipeline.py --approach track_e
```

Run just the summary stage:

```bash
python -m src.eda.track_e.summary_report --config configs/track_e.yaml
```
